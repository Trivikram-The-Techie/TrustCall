"""
Rate Limiter Middleware & Dependency for TrustCall / VoiceShield.
Implements a sliding-window rate limiter per Client IP or API Key.
Enforces limits on:
  - /v1/score
  - /v1/redteam
  - /v1/stream
"""

import time
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from fastapi import Request, WebSocket, HTTPException, status
from app.config import settings

class SlidingWindowRateLimiter:
    """
    In-memory thread-safe sliding window rate limiter.
    Tracks timestamps per key: (endpoint, client_identifier).
    """
    def __init__(self):
        # Key: (endpoint, identifier) -> list of timestamp floats
        self._history: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        self._enabled: bool = True

    def set_enabled(self, enabled: bool):
        """Allows disabling in specific tests if necessary."""
        self._enabled = enabled

    def reset(self):
        """Clear all rate limit histories (for tests)."""
        self._history.clear()

    def get_client_identifier(self, request_or_ws) -> str:
        """
        Extracts client identifier:
        1. X-API-Key header (if present)
        2. X-Forwarded-For header (if behind proxy)
        3. Client IP address
        """
        headers = request_or_ws.headers
        api_key = headers.get("x-api-key") or headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key}"

        forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
            return f"ip:{client_ip}"

        client = getattr(request_or_ws, "client", None)
        if client and client.host:
            return f"ip:{client.host}"

        return "ip:127.0.0.1"

    def is_allowed(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int,
        window_sec: int = 60
    ) -> Tuple[bool, int]:
        """
        Checks whether client is permitted to make a request.
        Returns: (is_allowed: bool, retry_after_seconds: int)
        """
        if not self._enabled or max_requests <= 0:
            return True, 0

        now = time.time()
        key = (endpoint, identifier)
        timestamps = self._history[key]

        # Prune timestamps older than window
        cutoff = now - window_sec
        valid_timestamps = [ts for ts in timestamps if ts > cutoff]
        self._history[key] = valid_timestamps

        if len(valid_timestamps) >= max_requests:
            # Earliest request in current window determines retry-after
            earliest = valid_timestamps[0]
            retry_after = max(1, int(window_sec - (now - earliest)))
            return False, retry_after

        # Record this request
        valid_timestamps.append(now)
        return True, 0

    def check_request(
        self,
        request: Request,
        endpoint: str,
        max_requests: int,
        window_sec: int = 60
    ):
        """Convenience method raising HTTPException(429) if exceeded."""
        client_id = self.get_client_identifier(request)
        allowed, retry_after = self.is_allowed(client_id, endpoint, max_requests, window_sec)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded on {endpoint}. Maximum {max_requests} requests per {window_sec}s.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after)
                }
            )

    def check_websocket(
        self,
        websocket: WebSocket,
        endpoint: str = "stream",
        max_requests: Optional[int] = None,
        window_sec: int = 60
    ) -> Tuple[bool, int]:
        """Check rate limit for incoming WebSocket connection."""
        limit = max_requests or settings.RATE_LIMIT_STREAM_PER_MIN
        client_id = self.get_client_identifier(websocket)
        return self.is_allowed(client_id, endpoint, limit, window_sec)


# Global singleton instance
rate_limiter = SlidingWindowRateLimiter()

def rate_limit(endpoint: str, max_requests: Optional[int] = None):
    """
    FastAPI dependency for endpoint rate limiting.
    Example: Depends(rate_limit("score", settings.RATE_LIMIT_SCORE_PER_MIN))
    """
    def dependency(request: Request):
        limit = max_requests
        if limit is None:
            if endpoint == "score":
                limit = settings.RATE_LIMIT_SCORE_PER_MIN
            elif endpoint == "redteam":
                limit = settings.RATE_LIMIT_REDTEAM_PER_MIN
            else:
                limit = 60
        rate_limiter.check_request(request, endpoint, limit)
    return dependency
