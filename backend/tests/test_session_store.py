"""
Unit tests for Session Store Interface (InMemory and Redis multi-replica implementations).
"""

import time
import json
import pytest
from unittest.mock import MagicMock

from app.privacy.session_store_interface import (
    InMemorySessionStore,
    RedisSessionStore,
    create_session_store
)


def test_in_memory_session_store():
    store = InMemorySessionStore(ttl_seconds=2)
    session_id = "test-session-123"

    # Record normal chunk
    res = store.record_chunk_risk(
        session_id=session_id,
        risk_score=15,
        alert_tier="Low",
        components={"model": 10},
        explanation="Benign speech",
        embedding_hash="hash_abc"
    )
    assert res["session_id"] == session_id
    assert len(res["risk_scores"]) == 1
    assert store.get_active_session_count() == 1
    assert session_id in store.list_active_sessions()

    # Record high alert
    store.record_chunk_risk(
        session_id=session_id,
        risk_score=85,
        alert_tier="High",
        components={"model": 90},
        explanation="Voice clone detected"
    )
    alerts = store.get_session_alerts(session_id)
    assert len(alerts) == 1
    assert alerts[0]["alert_tier"] == "High"

    # Test TTL purging
    time.sleep(2.1)
    assert store.get_session_summary(session_id) is None
    assert store.get_active_session_count() == 0


def test_redis_session_store_with_mock_client():
    mock_redis = MagicMock()
    # Mock data storage dict
    mock_db = {}

    def mock_setex(key, ttl, value):
        mock_db[key] = value

    def mock_get(key):
        return mock_db.get(key)

    def mock_sadd(set_key, val):
        pass

    def mock_smembers(set_key):
        return ["test-redis-session"]

    def mock_scard(set_key):
        return 1

    mock_redis.setex.side_effect = mock_setex
    mock_redis.get.side_effect = mock_get
    mock_redis.sadd.side_effect = mock_sadd
    mock_redis.smembers.side_effect = mock_smembers
    mock_redis.scard.side_effect = mock_scard
    mock_redis.ping.return_value = True

    store = RedisSessionStore(client=mock_redis)
    assert store.is_connected is True

    res = store.record_chunk_risk(
        session_id="test-redis-session",
        risk_score=78,
        alert_tier="High",
        components={"model": 75},
        explanation="Impersonation anomaly"
    )
    assert res["session_id"] == "test-redis-session"
    assert "trustcall:session:test-redis-session" in mock_db
    assert store.get_active_session_count() == 1

    alerts = store.get_session_alerts("test-redis-session")
    assert len(alerts) == 1
    assert alerts[0]["risk_score"] == 78


def test_redis_session_store_graceful_fallback():
    # If connection fails or Redis is unreachable, fallback store operates seamlessly
    store = RedisSessionStore(redis_url="redis://invalid-host-999:6379/0")
    assert store.is_connected is False

    res = store.record_chunk_risk(
        session_id="fallback-sess",
        risk_score=20,
        alert_tier="Low",
        components={},
        explanation="Fallback ok"
    )
    assert res["session_id"] == "fallback-sess"
    assert store.get_session_summary("fallback-sess") is not None


def test_create_session_store_factory(monkeypatch):
    monkeypatch.setenv("SESSION_STORE_BACKEND", "memory")
    store_mem = create_session_store()
    assert isinstance(store_mem, InMemorySessionStore)

    monkeypatch.setenv("SESSION_STORE_BACKEND", "redis")
    store_redis = create_session_store()
    assert isinstance(store_redis, RedisSessionStore)
