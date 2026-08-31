"""
Privacy-preserving session store and non-reversible biometric hasher.
Ensures zero persistent raw audio storage and transforms acoustic vectors
into one-way cryptographic SHA-256 hashes for repeat-scam tracking.
"""

import time
import hmac
import hashlib
import numpy as np
from typing import Dict, List, Optional, Any
from app.config import settings

class NonReversibleEmbeddingHasher:
    """
    Computes a one-way cryptographic HMAC-SHA256 signature from acoustic spectral vectors.
    Mathematically non-reversible: the original voice or audio cannot be reconstructed.
    Enables repeat-offender scam tracking across multiple phone calls.
    """
    def __init__(self, salt_key: str = settings.SALT_KEY):
        self.salt = salt_key.encode('utf-8')

    def generate_hash(self, audio: np.ndarray) -> str:
        """
        Extracts coarse spectral energy bands, quantizes them,
        and returns a 64-char HMAC-SHA256 hash.
        """
        if len(audio) < 512:
            return "hash_insufficient_audio_samples"

        # Coarse energy distribution across 8 octave frequency bands
        fft_mag = np.abs(np.fft.rfft(audio[:2048]))
        band_size = len(fft_mag) // 8
        if band_size == 0:
            return "hash_empty_bands"

        bands = [float(np.mean(fft_mag[i * band_size:(i + 1) * band_size])) for i in range(8)]
        # Quantize to discrete integers to allow robust matching
        quantized = [str(int(b * 100) % 1000) for b in bands]
        vector_str = ":".join(quantized)

        # Hash with secret salt
        signature = hmac.new(self.salt, vector_str.encode('utf-8'), hashlib.sha256).hexdigest()
        return signature


class EphemeralSessionStore:
    """
    In-memory session registry with strict TTL purging.
    Persists only: session_id, risk scores, alert tier, timestamp, and one-way hash.
    ZERO raw audio is persisted to disk.
    """
    def __init__(self, ttl_seconds: int = settings.SESSION_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self.sessions: Dict[str, Dict[str, Any]] = {}
        # Simulated database of known scammer hashes
        self.known_scam_hashes: Dict[str, Dict[str, Any]] = {
            "d8578edf8458ce06fbc5bb76a58c5ca4": {"flags": 14, "label": "Known Digital Arrest Botnet"},
            "c3ab8ff13720e8ad9047dd39466b3c89": {"flags": 28, "label": "Known Bank Impersonation Ring"}
        }

    def _purge_expired(self):
        """Removes sessions older than TTL."""
        now = time.time()
        expired = [sid for sid, data in self.sessions.items() if now - data["last_updated"] > self.ttl_seconds]
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
        """
        Logs a scoring event in the active session.
        """
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
            # Check against known scam hashes
            if embedding_hash in self.known_scam_hashes:
                session["is_repeat_offender"] = True
                session["offender_details"] = self.known_scam_hashes[embedding_hash]

        # Log alert if Medium, High, or Critical
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
        """Retrieves alert history for a session."""
        self._purge_expired()
        session = self.sessions.get(session_id)
        if not session:
            return []
        return session.get("alert_history", [])

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves non-biometric session summary."""
        self._purge_expired()
        return self.sessions.get(session_id)

# Global instances
privacy_hasher = NonReversibleEmbeddingHasher()
session_store = EphemeralSessionStore()
