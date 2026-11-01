"""
Main entry point for TrustCall / VoiceShield FastAPI Backend.
Provides REST and WebSocket endpoints for real-time voice clone impersonation detection.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.api.routes_score import router as score_router
from app.api.routes_stream import router as stream_router
from app.api.routes_alerts import router as alerts_router
from app.api.routes_forensics import router as forensics_router
from app.api.routes_redteam import router as redteam_router
from app.api.routes_challenge import router as challenge_router
from app.api.routes_metrics import router as metrics_router
from app.api.routes_scale import router as scale_router
from app.api.routes_trusted_alert import router as trusted_alert_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure demo_audio directory exists
    demo_dir = os.path.join(os.path.dirname(__file__), "..", "demo_audio")
    os.makedirs(demo_dir, exist_ok=True)
    yield
    # Shutdown cleanup if needed

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects enterprise security headers on all HTTP responses:
    - Content-Security-Policy (with frame-ancestors none)
    - Strict-Transport-Security (HSTS)
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: microphone=(self)
    """
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'wasm-unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob: https:; "
            "media-src 'self' blob: data:; "
            "connect-src 'self' ws: wss: http: https:; "
            "font-src 'self' data:; "
            "frame-ancestors 'none';"
        )
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "microphone=(self), camera=(), geolocation=()"
        return response

app = FastAPI(
    title="TrustCall / VoiceShield API",
    version=settings.APP_VERSION,
    description="AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks (SIH)",
    lifespan=lifespan
)

# Enterprise Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Restricted CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount Static Files for Demo Audio Samples
demo_audio_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "demo_audio"))
os.makedirs(demo_audio_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=demo_audio_path), name="static")

# Include Routers
app.include_router(score_router)
app.include_router(stream_router)
app.include_router(alerts_router)
app.include_router(forensics_router)
app.include_router(redteam_router)
app.include_router(challenge_router)
app.include_router(metrics_router)
app.include_router(scale_router)
app.include_router(trusted_alert_router)

@app.get("/")
async def root():
    return {
        "system": "TrustCall / VoiceShield",
        "status": "operational",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "realtime_ws": "/v1/stream",
        "score_api": "/v1/score"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "neural_model": "AntiSpoofNet (AASIST-L Pre-Trained Deep Graph Attention)",
        "nlp_scanner": "Multilingual Urgency Engine (EN/HI)",
        "privacy_compliance": "Zero-Raw-Audio-Persisted"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
