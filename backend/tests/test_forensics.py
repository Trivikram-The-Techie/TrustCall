"""
Unit and integration tests for Forensic Evidence Bag generation and cryptographic verification.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.privacy.evidence_report import forensic_evidence_generator

client = TestClient(app)

def test_evidence_bag_generation_and_integrity():
    payload = {
        "session_id": "test-session-101",
        "risk_score": 92,
        "verdict": "Critical",
        "explanation": "Neural vocoder artifacts detected with high confidence.",
        "forensic_reasons": ["Unnatural F0 flatness", "Vocoder high-freq cutoff"],
        "layers": {
            "l1_pitch_naturalness": {"passed": False, "label": "Pitch Inflection", "score": 0.88},
            "l2_vocal_fold_tremor": {"passed": False, "label": "Vocal Fold Jitter", "score": 0.91}
        },
        "components": {"model_confidence": 92.0, "urgency_nlp": 80.0},
        "caller_metadata": {"caller_id": "+91-9876543210"},
        "nlp_keywords": ["CBI", "arrest warrant", "transfer money"]
    }
    
    evidence = forensic_evidence_generator.generate_evidence_bag(**payload)
    assert evidence["evidence_id"].startswith("TC-EVD-")
    assert "tamper_proof_signature" in evidence
    assert len(evidence["tamper_proof_signature"]) == 64
    assert evidence["risk_score"] == 92
    assert "CRITICAL" in evidence["recommended_action"]

    # Verify authentic signature
    verification = forensic_evidence_generator.verify_evidence_integrity(evidence)
    assert verification["is_valid"] is True
    assert verification["status"] == "VERIFIED_AUTHENTIC"

    # Test tampering detection
    tampered_evidence = dict(evidence)
    tampered_evidence["risk_score"] = 15  # Tamper with the risk score
    tamper_result = forensic_evidence_generator.verify_evidence_integrity(tampered_evidence)
    assert tamper_result["is_valid"] is False
    assert tamper_result["status"] == "TAMPER_DETECTED"

def test_forensic_report_api_endpoints():
    req_body = {
        "session_id": "api-call-session-888",
        "risk_score": 88,
        "verdict": "Critical",
        "explanation": "Synthetic voice attack confirmed.",
        "forensic_reasons": ["Vocoder phase comb filtering"],
        "nlp_keywords": ["OTP"]
    }
    
    # 1. Generate report
    response = client.post("/v1/forensics/generate-report", json=req_body)
    assert response.status_code == 201
    data = response.json()
    assert "tamper_proof_signature" in data
    assert data["evidence_id"].startswith("TC-EVD-")

    # 2. Verify report authentic
    verify_resp = client.post("/v1/forensics/verify-report", json=data)
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["is_valid"] is True

    # 3. Verify report tampering
    data["risk_score"] = 20
    verify_tampered_resp = client.post("/v1/forensics/verify-report", json=data)
    assert verify_tampered_resp.status_code == 200
    assert verify_tampered_resp.json()["is_valid"] is False
