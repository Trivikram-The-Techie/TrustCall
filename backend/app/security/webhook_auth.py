"""
HMAC-SHA256 Webhook Authentication, Signature Verification, and Nonce Store Middleware.
Protects downstream banking fraud gateways from unauthorized dispatch and replay attacks.

Features:
- Constant-time HMAC-SHA256 comparison (hmac.compare_digest)
- Strict timestamp tolerance (default max 300s clock skew)
- In-memory Nonce Store blocking replay attacks
"""

import hmac
import hashlib
import time
import json
import uuid
from typing import Dict, Any, Tuple, Optional
from app.config import settings

class WebhookSigner:
    """
    Computes and verifies RFC-2104 HMAC-SHA256 signatures for webhook alerts.
    Includes replay window protection and a cryptographic nonce store.
    """
    def __init__(self, secret_key: str = settings.SALT_KEY):
        self.secret_key = secret_key.encode("utf-8")
        # Nonce store: nonce -> timestamp float
        self._seen_nonces: Dict[str, float] = {}

    def clear_nonce_store(self):
        """Clears nonce store (useful for tests)."""
        self._seen_nonces.clear()

    def _purge_expired_nonces(self, max_skew_sec: int):
        """Remove nonces older than the maximum allowable timestamp drift."""
        now = time.time()
        cutoff = now - (max_skew_sec * 2)
        expired = [n for n, ts in self._seen_nonces.items() if ts < cutoff]
        for n in expired:
            del self._seen_nonces[n]

    def sign_payload(
        self,
        payload: Dict[str, Any],
        timestamp: Optional[int] = None,
        nonce: Optional[str] = None
    ) -> Tuple[str, int]:
        """
        Signs canonical JSON payload with Unix timestamp and optional nonce.
        Returns (signature_hex, timestamp) for backwards compatibility.
        """
        ts = timestamp if timestamp is not None else int(time.time())
        if nonce:
            canonical_str = f"{ts}.{nonce}.{json.dumps(payload, sort_keys=True, separators=(',', ':'))}"
        else:
            canonical_str = f"{ts}.{json.dumps(payload, sort_keys=True, separators=(',', ':'))}"

        sig = hmac.new(self.secret_key, canonical_str.encode("utf-8"), hashlib.sha256).hexdigest()
        return sig, ts

    def sign_payload_with_nonce(
        self,
        payload: Dict[str, Any],
        timestamp: Optional[int] = None,
        nonce: Optional[str] = None
    ) -> Tuple[str, int, str]:
        """
        Signs canonical JSON payload and returns (signature, timestamp, nonce).
        """
        ts = timestamp if timestamp is not None else int(time.time())
        n = nonce or str(uuid.uuid4())
        sig, _ = self.sign_payload(payload, timestamp=ts, nonce=n)
        return sig, ts, n

    def verify_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        timestamp: int,
        nonce: Optional[str] = None,
        max_skew_sec: int = 300
    ) -> bool:
        """
        Validates HMAC signature, timestamp tolerance, and ensures nonce has not been replayed.
        Uses constant-time comparison (hmac.compare_digest).
        """
        now = int(time.time())

        # 1. Timestamp Tolerance Check
        if abs(now - timestamp) > max_skew_sec:
            return False

        # 2. Nonce Replay Check
        if nonce:
            self._purge_expired_nonces(max_skew_sec)
            if nonce in self._seen_nonces:
                # Replay attack detected!
                return False

        # 3. Constant-Time Signature Comparison
        expected_sig, _ = self.sign_payload(payload, timestamp=timestamp, nonce=nonce)
        if not hmac.compare_digest(signature, expected_sig):
            return False

        # 4. Record Nonce
        if nonce:
            self._seen_nonces[nonce] = float(now)

        return True


webhook_signer = WebhookSigner()
