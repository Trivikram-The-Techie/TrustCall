"""
Tests for Webhook HMAC-SHA256 signature verification and replay protection.
"""

import time
from app.security.webhook_auth import webhook_signer

def test_webhook_signature_generation_and_verification():
    payload = {
        "session_id": "CALL-SEC-001",
        "risk_score": 94,
        "action": "LOCK_ACCOUNT"
    }

    sig, ts = webhook_signer.sign_payload(payload)
    assert len(sig) == 64  # SHA-256 hex length
    assert ts > 0

    # Verification should succeed
    is_valid = webhook_signer.verify_signature(payload, sig, ts)
    assert is_valid is True

def test_webhook_tampered_payload_rejected():
    payload = {"session_id": "CALL-SEC-002", "risk_score": 88}
    sig, ts = webhook_signer.sign_payload(payload)

    tampered_payload = {"session_id": "CALL-SEC-002", "risk_score": 12}
    assert webhook_signer.verify_signature(tampered_payload, sig, ts) is False

def test_webhook_replay_skew_rejected():
    payload = {"session_id": "CALL-SEC-003", "risk_score": 90}
    old_ts = int(time.time()) - 400  # 400s in the past (exceeds 300s window)
    sig, _ = webhook_signer.sign_payload(payload, timestamp=old_ts)

    assert webhook_signer.verify_signature(payload, sig, old_ts, max_skew_sec=300) is False
