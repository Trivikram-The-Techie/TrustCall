"""
API Key Authentication Dependency for TrustCall / VoiceShield.
Enforces X-API-Key or Bearer token verification on sensitive/non-demo routes.
"""

from typing import Optional
from fastapi import Request, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(
    request: Request,
    api_key_from_header: Optional[str] = Security(api_key_header)
) -> Optional[str]:
    """
    Validates API key for sensitive routes.
    If settings.API_KEY_AUTH_ENABLED is False, access is permitted (demo mode).
    If True, request must provide a valid key in X-API-Key or Authorization header.
    """
    if not settings.API_KEY_AUTH_ENABLED:
        return api_key_from_header or "demo_mode_active"

    key = api_key_from_header

    # Fallback to Authorization: Bearer <key> if X-API-Key is missing
    if not key:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            key = auth_header.split(" ", 1)[1].strip()

    if not key or key not in settings.API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing or invalid X-API-Key header. Provide a valid institutional API key.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    return key
