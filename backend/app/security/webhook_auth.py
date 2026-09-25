"""
HMAC-SHA256 Webhook Authentication and Signature Verification Middleware.
Protects downstream banking fraud gateways from unauthorized dispatch and replay attacks.
"""

import hmac
import hashlib
import time
import json
from typing import Dict, Any, Tuple
from app.config import settings

class WebhookSigner:
    """
    Computes and verifies RFC-2104 HMAC-SHA256 signatures for webhook alerts.
    Includes replay window protection (default 300 seconds).
    """
    def __init__(self, secret_key: str = settings.SALT_KEY):
        self.secret_key = secret_key.encode("utf-8")

    def sign_payload(self, payload: Dict[str, Any], timestamp: int = None) -> Tuple[str, int]:
        """
        Signs canonical JSON payload with current Unix timestamp.
        Returns (signature_hex, timestamp).
        """
        ts = timestamp or int(time.time())
        canonical_str = f"{ts}.{json.dumps(payload, sort_keys=True, separators=(',', ':'))}"
        sig = hmac.new(self.secret_key, canonical_str.encode("utf-8"), hashlib.sha256).hexdigest()
        return sig, ts

    def verify_signature(self, payload: Dict[str, Any], signature: str, timestamp: int, max_skew_sec: int = 300) -> bool:
        """
        Validates signature against canonical payload and checks for timestamp replay skew.
        """
        now = int(time.time())
        if abs(now - timestamp) > max_skew_sec:
            return False

        expected_sig, _ = self.sign_payload(payload, timestamp=timestamp)
        return hmac.compare_digest(signature, expected_sig)

webhook_signer = WebhookSigner()
