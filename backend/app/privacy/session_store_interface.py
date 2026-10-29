"""
Session Store Interface & Multi-Backend Implementations (In-Memory & Redis).
Supports horizontal scaling across distributed replicas with zero raw audio persistence.
"""

import os
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from app.config import settings

logger = logging.getLogger("trustcall.session_store")


class BaseSessionStore(ABC):
    """
    Abstract interface for privacy-preserving session storage across replicas.
    Stores only risk scores, alerts, cryptographic hashes, and TTL metadata.
    ZERO raw audio is ever persisted.
    """

    @abstractmethod
    def record_chunk_risk(
        self,
        session_id: str,
        risk_score: int,
        alert_tier: str,
        components: dict,
        explanation: str,
        embedding_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """Logs a chunk scoring event."""
        pass

    @abstractmethod
    def get_session_alerts(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieves alert history for a session."""
        pass

    @abstractmethod
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves non-biometric session summary."""
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Explicitly deletes a session."""
        pass

    @abstractmethod
    def list_active_sessions(self) -> List[str]:
        """Returns list of active session IDs."""
        pass

    @abstractmethod
    def get_active_session_count(self) -> int:
        """Returns the number of active sessions."""
        pass


class InMemorySessionStore(BaseSessionStore):
    """
    In-memory session registry with strict TTL purging.
    Ideal for single-instance deployments, testing, and local development.
    """
    def __init__(self, ttl_seconds: int = settings.SESSION_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.known_scam_hashes: Dict[str, Dict[str, Any]] = {
            "d8578edf8458ce06fbc5bb76a58c5ca4": {"flags": 14, "label": "Known Digital Arrest Botnet"},
            "c3ab8ff13720e8ad9047dd39466b3c89": {"flags": 28, "label": "Known Bank Impersonation Ring"}
        }

    def _purge_expired(self):
        """Purges sessions older than TTL."""
        now = time.time()
        expired = [sid for sid, data in self.sessions.items() if now - data.get("last_updated", now) > self.ttl_seconds]
        for sid in expired:
            del self.sessions[sid]

    def record_chunk_risk(
        self,
        session_id: str,
        risk_score: int,
        alert_tier: str,
        components: dict,
        explanation: str,
        embedding_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        self._purge_expired()
        now = time.time()

        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "session_id": session_id,
                "created_at": now,
                "last_updated": now,
                "risk_scores": [],
                "alert_history": [],
                "components_history": [],
                "embedding_hash": embedding_hash,
                "is_repeat_offender": False,
                "offender_details": None
            }

        session = self.sessions[session_id]
        session["last_updated"] = now
        session["risk_scores"].append({"timestamp": round(now, 2), "risk_score": risk_score})
        session["components_history"].append(components)

        if embedding_hash:
            session["embedding_hash"] = embedding_hash
            if embedding_hash in self.known_scam_hashes:
                session["is_repeat_offender"] = True
                session["offender_details"] = self.known_scam_hashes[embedding_hash]

        if alert_tier in ["Medium", "High", "Critical"]:
            alert_entry = {
                "timestamp": round(now, 2),
                "alert_tier": alert_tier,
                "risk_score": risk_score,
                "explanation": explanation
            }
            session["alert_history"].append(alert_entry)

        return session

    def get_session_alerts(self, session_id: str) -> List[Dict[str, Any]]:
        self._purge_expired()
        session = self.sessions.get(session_id)
        if not session:
            return []
        return session.get("alert_history", [])

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        self._purge_expired()
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def list_active_sessions(self) -> List[str]:
        self._purge_expired()
        return list(self.sessions.keys())

    def get_active_session_count(self) -> int:
        self._purge_expired()
        return len(self.sessions)


class RedisSessionStore(BaseSessionStore):
    """
    Redis-backed session store for multi-replica horizontal clustering.
    Serializes non-biometric session state to Redis with automatic TTL expiry.
    Gracefully falls back to local memory if Redis server is unreachable.
    """
    def __init__(
        self,
        redis_url: str = settings.REDIS_URL,
        ttl_seconds: int = settings.SESSION_TTL_SECONDS,
        client=None
    ):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.fallback = InMemorySessionStore(ttl_seconds=ttl_seconds)
        self.known_scam_hashes: Dict[str, Dict[str, Any]] = {
            "d8578edf8458ce06fbc5bb76a58c5ca4": {"flags": 14, "label": "Known Digital Arrest Botnet"},
            "c3ab8ff13720e8ad9047dd39466b3c89": {"flags": 28, "label": "Known Bank Impersonation Ring"}
        }

        self.client = client
        self.is_connected = False

        if self.client is not None:
            self.is_connected = True
        else:
            try:
                import redis
                self.client = redis.from_url(redis_url, decode_responses=True, socket_timeout=1.0)
                # Quick ping check
                self.client.ping()
                self.is_connected = True
                logger.info(f"Connected to Redis session backend: {redis_url}")
            except Exception as e:
                logger.warning(
                    f"Could not connect to Redis at {redis_url}: {e}. "
                    "Operating with in-memory replica fallback."
                )
                self.is_connected = False

    def _key(self, session_id: str) -> str:
        return f"trustcall:session:{session_id}"

    def record_chunk_risk(
        self,
        session_id: str,
        risk_score: int,
        alert_tier: str,
        components: dict,
        explanation: str,
        embedding_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.is_connected:
            return self.fallback.record_chunk_risk(
                session_id, risk_score, alert_tier, components, explanation, embedding_hash
            )

        try:
            key = self._key(session_id)
            raw = self.client.get(key)
            now = time.time()

            if raw:
                session = json.loads(raw)
            else:
                session = {
                    "session_id": session_id,
                    "created_at": now,
                    "last_updated": now,
                    "risk_scores": [],
                    "alert_history": [],
                    "components_history": [],
                    "embedding_hash": embedding_hash,
                    "is_repeat_offender": False,
                    "offender_details": None
                }

            session["last_updated"] = now
            session["risk_scores"].append({"timestamp": round(now, 2), "risk_score": risk_score})
            session["components_history"].append(components)

            if embedding_hash:
                session["embedding_hash"] = embedding_hash
                if embedding_hash in self.known_scam_hashes:
                    session["is_repeat_offender"] = True
                    session["offender_details"] = self.known_scam_hashes[embedding_hash]

            if alert_tier in ["Medium", "High", "Critical"]:
                alert_entry = {
                    "timestamp": round(now, 2),
                    "alert_tier": alert_tier,
                    "risk_score": risk_score,
                    "explanation": explanation
                }
                session["alert_history"].append(alert_entry)

            # Store in Redis with TTL
            self.client.setex(key, self.ttl_seconds, json.dumps(session))
            self.client.sadd("trustcall:active_sessions", session_id)
            self.client.expire("trustcall:active_sessions", self.ttl_seconds)

            return session
        except Exception as e:
            logger.warning(f"Redis write error: {e}. Falling back to in-memory.")
            return self.fallback.record_chunk_risk(
                session_id, risk_score, alert_tier, components, explanation, embedding_hash
            )

    def get_session_alerts(self, session_id: str) -> List[Dict[str, Any]]:
        if not self.is_connected:
            return self.fallback.get_session_alerts(session_id)

        try:
            key = self._key(session_id)
            raw = self.client.get(key)
            if not raw:
                return []
            session = json.loads(raw)
            return session.get("alert_history", [])
        except Exception as e:
            logger.warning(f"Redis read error: {e}. Using fallback.")
            return self.fallback.get_session_alerts(session_id)

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            return self.fallback.get_session_summary(session_id)

        try:
            key = self._key(session_id)
            raw = self.client.get(key)
            if not raw:
                return None
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"Redis read error: {e}. Using fallback.")
            return self.fallback.get_session_summary(session_id)

    def delete_session(self, session_id: str) -> bool:
        if not self.is_connected:
            return self.fallback.delete_session(session_id)

        try:
            key = self._key(session_id)
            self.client.delete(key)
            self.client.srem("trustcall:active_sessions", session_id)
            return True
        except Exception:
            return self.fallback.delete_session(session_id)

    def list_active_sessions(self) -> List[str]:
        if not self.is_connected:
            return self.fallback.list_active_sessions()

        try:
            return list(self.client.smembers("trustcall:active_sessions"))
        except Exception:
            return self.fallback.list_active_sessions()

    def get_active_session_count(self) -> int:
        if not self.is_connected:
            return self.fallback.get_active_session_count()

        try:
            return self.client.scard("trustcall:active_sessions")
        except Exception:
            return self.fallback.get_active_session_count()


def create_session_store(backend: Optional[str] = None) -> BaseSessionStore:
    """
    Factory creating configured session store based on environment variable
    or setting: TRUSTCALL_SESSION_STORE_BACKEND="redis"|"memory".
    """
    selected_backend = backend or os.getenv("SESSION_STORE_BACKEND", settings.SESSION_STORE_BACKEND).lower()

    if selected_backend == "redis":
        return RedisSessionStore()
    return InMemorySessionStore()
