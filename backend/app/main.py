"""
Main entry point for TrustCall / VoiceShield FastAPI Backend.
Provides REST and WebSocket endpoints for real-time voice clone impersonation detection.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.routes_score import router as score_router
from app.api.routes_stream import router as stream_router
from app.api.routes_alerts import router as alerts_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure demo_audio directory exists
    demo_dir = os.path.join(os.path.dirname(__file__), "..", "demo_audio")
    os.makedirs(demo_dir, exist_ok=True)
    yield
    # Shutdown cleanup if needed

app = FastAPI(
    title="TrustCall / VoiceShield API",
    version=settings.APP_VERSION,
    description="AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks (SIH)",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
        "neural_model": "AntiSpoofNet (AASIST / Spectral CNN)",
        "nlp_scanner": "Multilingual Urgency Engine (EN/HI)",
        "privacy_compliance": "Zero-Raw-Audio-Persisted"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
