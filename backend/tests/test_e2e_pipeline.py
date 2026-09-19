"""
End-to-End Comprehensive Multi-Signal Feature Verification Test Suite.
Verifies all 10 feature modules across REST, WebSocket, Forensics, and SDK pipelines.
"""

import os
import io
import base64
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def audio_samples():
    base_dir = os.path.join(os.path.dirname(__file__), "..", "demo_audio")
    gen_path = os.path.join(base_dir, "genuine_call_sample.wav")
    clone_path = os.path.join(base_dir, "cloned_scam_sample.wav")
    
    with open(gen_path, "rb") as f:
        gen_bytes = f.read()
    with open(clone_path, "rb") as f:
        clone_bytes = f.read()
        
    return {
        "genuine_bytes": gen_bytes,
        "cloned_bytes": clone_bytes
    }

def test_module_01_health_and_model_metadata():
    """Module 1: Probe health endpoint and model architecture metadata."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "AASIST-L" in data["neural_model"]

def test_module_02_demo_samples_listing():
    """Module 2: Validate sample library discovery endpoint."""
    res = client.get("/v1/demo/samples")
    assert res.status_code == 200
    data = res.json()
    assert "samples" in data
    assert len(data["samples"]) >= 2

def test_module_03_genuine_human_voice_scoring(audio_samples):
    """Module 3: Verify authentic human voice achieves low risk score."""
    b64 = base64.b64encode(audio_samples["genuine_bytes"]).decode("ascii")
    res = client.post("/v1/score", json={
        "audio_base64": b64,
        "sample_rate": 16000,
        "text_transcript": "Hey, let's meet tomorrow for the SIH project discussion at the lab.",
        "caller_metadata": {
            "is_unknown_number": False,
            "is_voip_spoofed": False
        }
    })
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] <= 35, f"Expected low score for genuine audio, got {data['risk_score']}"
    assert data["verdict"] == "Low"
    assert "Organic Human" in data["vocoder_fingerprint"]["primary_architecture"]

def test_module_04_synthetic_clone_scam_scoring(audio_samples):
    """Module 4: Verify cloned voice attack triggers high/critical alert."""
    b64 = base64.b64encode(audio_samples["cloned_bytes"]).decode("ascii")
    res = client.post("/v1/score", json={
        "audio_base64": b64,
        "sample_rate": 16000,
        "text_transcript": "This is Senior Manager Rajesh from State Bank of India. Your card is blocked. Share OTP immediately.",
        "caller_metadata": {
            "is_unknown_number": True,
            "is_voip_spoofed": True,
            "claimed_entity": "State Bank of India"
        }
    })
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] >= 65, f"Expected high score for cloned audio, got {data['risk_score']}"
    assert data["verdict"] in ["High", "Critical"]
    assert len(data["forensic_reasons"]) > 0

def test_module_05_multipart_file_upload(audio_samples):
    """Module 5: Test multipart audio file upload and forensic extraction."""
    res = client.post(
        "/v1/score/upload",
        files={"file": ("scam_recording.wav", io.BytesIO(audio_samples["cloned_bytes"]), "audio/wav")},
        data={
            "text_transcript": "CBI police warrant issued. Immediate bank transfer required.",
            "is_unknown_number": "true"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] >= 60
    assert "vocoder_fingerprint" in data

def test_module_06_and_07_forensic_evidence_bag_and_verification():
    """Modules 6 & 7: Generate Section 65B evidence bag and verify cryptographic HMAC signature."""
    session_id = f"CALL-E2E-{os.urandom(4).hex().upper()}"
    res = client.post("/v1/forensics/generate-report", json={
        "session_id": session_id,
        "risk_score": 92,
        "verdict": "Critical",
        "explanation": "Deep neural vocoder artifacts detected with high-frequency comb ripple spikes.",
        "forensic_reasons": ["AASIST-L synthetic model confidence 98%", "Extortion coercion keywords detected"],
        "caller_metadata": {"caller_id": "+91 91100 88231", "carrier": "VoIP Trunk"},
        "nlp_keywords": ["CBI", "digital arrest", "OTP"]
    })
    assert res.status_code == 201
    bag = res.json()
    assert "tamper_proof_signature" in bag
    assert bag["evidence_id"].startswith("TC-EVD-")

    # Verify integrity
    verify_res = client.post("/v1/forensics/verify-report", json=bag)
    assert verify_res.status_code == 200
    assert verify_res.json()["is_valid"] is True
    assert verify_res.json()["status"] == "VERIFIED_AUTHENTIC"

def test_module_08_alerts_and_bank_webhook():
    """Module 8: Verify audit alerts query and bank fraud gateway webhook dispatch."""
    session_id = f"CALL-WB-{os.urandom(4).hex().upper()}"
    alerts_res = client.get("/v1/alerts", params={"session_id": session_id})
    assert alerts_res.status_code == 200
    assert alerts_res.json()["session_id"] == session_id

    wb_res = client.post("/v1/alerts/webhook", json={
        "session_id": session_id,
        "risk_score": 96,
        "alert_tier": "Critical",
        "explanation": "Voice clone scam attempt intercepted. Account locked."
    })
    assert wb_res.status_code == 200
    assert wb_res.json()["status"] == "DELIVERED_TO_FRAUD_GATEWAY"

def test_module_09_realtime_websocket_stream():
    """Module 9: Verify real-time WebSocket handshake and streaming telemetry."""
    with client.websocket_connect("/v1/stream") as ws:
        handshake = ws.receive_json()
        assert handshake.get("event") == "connected"
        assert "session_id" in handshake

        # Send 1 second of audio PCM
        dummy_pcm = b"\x00\x00" * 16000
        ws.send_bytes(dummy_pcm)
        telemetry = ws.receive_json()
        assert telemetry.get("event") == "score_update"
        assert "risk_score" in telemetry
        assert "verdict" in telemetry
