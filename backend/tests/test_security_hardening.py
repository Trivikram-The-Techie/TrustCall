"""
Phase 6 Security Hardening Tests:
- Security HTTP Headers (CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy)
- Rate limiting on /v1/score, /v1/redteam, and /v1/stream
- Upload limits (max file size, max duration, disallowed MIME types, malformed audio resilience)
- Webhook HMAC-SHA256 verification and nonce replay protection
- API key authentication controls
"""

import io
import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.security.rate_limiter import rate_limiter
from app.security.webhook_auth import webhook_signer
from app.audio.feature_extraction import decode_audio_bytes

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Security Headers Verification
# ---------------------------------------------------------------------------

class TestSecurityHeaders:
    def test_root_and_health_security_headers_present(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        headers = resp.headers

        # Content-Security-Policy
        assert "content-security-policy" in headers
        csp = headers["content-security-policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "script-src 'self' 'wasm-unsafe-eval'" in csp
        assert "style-src 'self' 'unsafe-inline'" in csp

        # Strict-Transport-Security
        assert "strict-transport-security" in headers
        assert "max-age=" in headers["strict-transport-security"]
        assert "includeSubDomains" in headers["strict-transport-security"]

        # X-Content-Type-Options
        assert headers.get("x-content-type-options") == "nosniff"

        # X-Frame-Options
        assert headers.get("x-frame-options") == "DENY"

        # Referrer-Policy
        assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"

        # Permissions-Policy
        assert "permissions-policy" in headers
        assert "microphone=(self)" in headers["permissions-policy"]


# ---------------------------------------------------------------------------
# 2. Rate Limiting Tests
# ---------------------------------------------------------------------------

class TestRateLimiting:
    def setup_method(self):
        rate_limiter.reset()

    def test_rate_limiter_allows_under_limit(self):
        allowed, retry = rate_limiter.is_allowed("test-ip-1", "score", max_requests=5, window_sec=60)
        assert allowed is True
        assert retry == 0

    def test_rate_limiter_blocks_above_limit(self):
        test_ip = "test-ip-blocked"
        for _ in range(5):
            allowed, _ = rate_limiter.is_allowed(test_ip, "score", max_requests=5, window_sec=60)
            assert allowed is True

        # 6th request must be blocked
        allowed, retry_after = rate_limiter.is_allowed(test_ip, "score", max_requests=5, window_sec=60)
        assert allowed is False
        assert retry_after > 0

    def test_rate_limiter_http_endpoint_triggers_429(self):
        # Configure a small limit for test
        rate_limiter.reset()
        endpoint_key = "score"

        # Fill up quota
        client_header = {"X-Forwarded-For": "198.51.100.42"}
        payload = {
            "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=",
            "sample_rate": 16000
        }

        # Exhaust limit
        limit = settings.RATE_LIMIT_SCORE_PER_MIN
        for _ in range(limit):
            rate_limiter.is_allowed("ip:198.51.100.42", endpoint_key, limit, 60)

        # Direct HTTP request from same IP should now return 429
        resp = client.post("/v1/score", json=payload, headers=client_header)
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers
        assert "Rate limit exceeded" in resp.json()["detail"]

    def test_rate_limiter_tracks_api_key_separately(self):
        rate_limiter.reset()
        allowed1, _ = rate_limiter.is_allowed("key:admin-1", "score", max_requests=2, window_sec=60)
        allowed2, _ = rate_limiter.is_allowed("key:admin-1", "score", max_requests=2, window_sec=60)
        blocked, _ = rate_limiter.is_allowed("key:admin-1", "score", max_requests=2, window_sec=60)

        # Different key should still be allowed
        other_allowed, _ = rate_limiter.is_allowed("key:admin-2", "score", max_requests=2, window_sec=60)

        assert allowed1 is True
        assert allowed2 is True
        assert blocked is False
        assert other_allowed is True


# ---------------------------------------------------------------------------
# 3. Upload Constraints & Safe Decoding Tests
# ---------------------------------------------------------------------------

class TestUploadConstraints:
    def test_upload_disallowed_mime_type_rejected(self):
        fake_pdf = b"%PDF-1.5 test file content"
        files = {"file": ("malicious.pdf", io.BytesIO(fake_pdf), "application/pdf")}
        resp = client.post("/v1/score/upload", files=files)
        assert resp.status_code == 415
        assert "Unsupported media type" in resp.json()["detail"]

    def test_upload_oversized_file_rejected(self):
        # Build payload larger than settings.MAX_UPLOAD_SIZE_BYTES
        oversized = b"0" * (settings.MAX_UPLOAD_SIZE_BYTES + 1024)
        files = {"file": ("huge.wav", io.BytesIO(oversized), "audio/wav")}
        resp = client.post("/v1/score/upload", files=files)
        assert resp.status_code == 413
        assert "exceeds maximum limit" in resp.json()["detail"]

    def test_corrupted_audio_safely_rejected(self):
        # Random binary garbage sent as WAV
        garbage = b"RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00\xFF\xFFcorrupted data"
        files = {"file": ("corrupt.wav", io.BytesIO(garbage), "audio/wav")}
        resp = client.post("/v1/score/upload", files=files)
        # Server should cleanly reject with 400 Bad Request, never 500 crash
        assert resp.status_code == 400

    def test_decode_audio_bytes_bounds_duration(self):
        # 16000 samples = 1 sec
        # Create 130 seconds worth of audio bytes (exceeds 120s limit)
        sr = 16000
        sec = 130
        excessive_pcm = b"\x00\x00" * (sr * sec)
        audio = decode_audio_bytes(excessive_pcm, target_sr=sr)
        max_allowed_samples = int(sr * settings.MAX_AUDIO_DURATION_SEC)
        assert len(audio) == max_allowed_samples

    def test_decode_audio_bytes_cleans_nan_inf(self):
        import numpy as np
        # Raw bytes representing NaN / Inf in float32
        nan_bytes = np.array([np.nan, np.inf, -np.inf, 0.5], dtype=np.float32).tobytes()
        audio = decode_audio_bytes(nan_bytes, target_sr=16000)
        assert not np.isnan(audio).any()
        assert not np.isinf(audio).any()


# ---------------------------------------------------------------------------
# 4. Webhook Verification & Nonce Replay Tests
# ---------------------------------------------------------------------------

class TestWebhookReplayProtection:
    def setup_method(self):
        webhook_signer.clear_nonce_store()

    def test_webhook_with_nonce_verification_succeeds(self):
        payload = {"session_id": "CALL-REPLAY-1", "risk_score": 92}
        sig, ts, nonce = webhook_signer.sign_payload_with_nonce(payload)

        # First verification must succeed
        valid = webhook_signer.verify_signature(payload, sig, ts, nonce=nonce)
        assert valid is True

    def test_webhook_replayed_nonce_rejected(self):
        payload = {"session_id": "CALL-REPLAY-2", "risk_score": 88}
        sig, ts, nonce = webhook_signer.sign_payload_with_nonce(payload)

        # First delivery
        first_attempt = webhook_signer.verify_signature(payload, sig, ts, nonce=nonce)
        assert first_attempt is True

        # Replay attempt with same nonce within tolerance window must be blocked
        replay_attempt = webhook_signer.verify_signature(payload, sig, ts, nonce=nonce)
        assert replay_attempt is False

    def test_webhook_verify_endpoint_blocks_replay(self):
        payload = {"session_id": "CALL-EP-REPLAY", "risk_score": 95}
        sig, ts, nonce = webhook_signer.sign_payload_with_nonce(payload)

        body = {
            "payload": payload,
            "signature": sig,
            "timestamp": ts,
            "nonce": nonce
        }

        # 1st attempt: 200 OK
        resp1 = client.post("/v1/alerts/webhook/verify", json=body)
        assert resp1.status_code == 200
        assert resp1.json()["verified"] is True

        # 2nd attempt with same nonce: 400 Bad Request (Replay rejected)
        resp2 = client.post("/v1/alerts/webhook/verify", json=body)
        assert resp2.status_code == 400
        assert "replayed nonce" in resp2.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 5. API Key Authentication Controls
# ---------------------------------------------------------------------------

class TestApiKeyAuthentication:
    def test_api_key_enabled_blocks_missing_key(self, monkeypatch):
        from app.security.api_key import verify_api_key
        from fastapi import Request

        monkeypatch.setattr(settings, "API_KEY_AUTH_ENABLED", True)

        class MockRequest:
            headers = {}

        # Calling without key should raise 401
        with pytest.raises(Exception) as excinfo:
            verify_api_key(MockRequest(), api_key_from_header=None)
        assert "401" in str(excinfo.value)

    def test_api_key_enabled_accepts_valid_key(self, monkeypatch):
        from app.security.api_key import verify_api_key

        monkeypatch.setattr(settings, "API_KEY_AUTH_ENABLED", True)

        class MockRequest:
            headers = {"X-API-Key": "trustcall-admin-key-2024"}

        key = verify_api_key(MockRequest(), api_key_from_header="trustcall-admin-key-2024")
        assert key == "trustcall-admin-key-2024"
