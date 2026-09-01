"""
Integration tests for FastAPI REST and WebSocket endpoints.
"""

import os
import base64
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "AntiSpoofNet" in data["neural_model"]

def test_demo_samples_endpoint():
    response = client.get("/v1/demo/samples")
    assert response.status_code == 200
    data = response.json()
    assert "samples" in data
    assert len(data["samples"]) == 2

def test_score_clip_endpoint():
    # Read generated sample WAV
    base_dir = os.path.join(os.path.dirname(__file__), "..", "demo_audio")
    cloned_path = os.path.join(base_dir, "cloned_scam_sample.wav")
    with open(cloned_path, "rb") as f:
        b64_audio = base64.b64encode(f.read()).decode("utf-8")
        
    payload = {
        "audio_base64": b64_audio,
        "sample_rate": 16000,
        "text_transcript": "Police investigation transfer money now OTP",
        "caller_metadata": {"is_unknown_number": True}
    }
    
    response = client.post("/v1/score", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert "risk_score" in res_data
    assert "verdict" in res_data
    assert "components" in res_data
    assert "embedding_hash" in res_data
    assert res_data["risk_score"] > 60

def test_alerts_endpoint():
    response = client.get("/v1/alerts?session_id=test_session_123")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert data["session_id"] == "test_session_123"
