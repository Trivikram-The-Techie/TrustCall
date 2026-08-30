"""
Tests for AntiSpoofNet model inference, rolling median smoothing,
scam urgency detection, and multi-signal risk fusion.
"""

import numpy as np
import pytest
from app.models.spoof_detector import SpoofDetector
from app.nlp.urgency_keywords import urgency_scanner
from app.models.risk_engine import risk_engine
from app.privacy.embedding_store import privacy_hasher

def test_model_inference():
    detector = SpoofDetector()
    audio = np.random.uniform(-0.5, 0.5, 24000).astype(np.float32)
    res = detector.predict_chunk(audio, sr=16000)
    
    assert "raw_probability" in res
    assert "smoothed_probability" in res
    assert 0.0 <= res["raw_probability"] <= 1.0
    assert 0.0 <= res["smoothed_probability"] <= 1.0
    assert isinstance(res["is_synthetic"], bool)

def test_rolling_smoothing():
    detector = SpoofDetector()
    detector.reset()
    
    # Predict 5 chunks and check that history length matches
    audio = np.random.uniform(-0.2, 0.2, 24000).astype(np.float32)
    for _ in range(5):
        res = detector.predict_chunk(audio, sr=16000)
        
    assert len(detector.score_history) == 5
    assert 0.0 <= res["smoothed_probability"] <= 1.0

def test_urgency_scanner():
    benign_text = "Good afternoon, could you please send over the meeting agenda for tomorrow?"
    res_benign = urgency_scanner.scan_text(benign_text)
    assert not res_benign["detected"]
    assert res_benign["urgency_score"] == 0.0

    scam_text_en = "This is urgent from police department. Transfer money now and share your OTP or warrant issued."
    res_scam_en = urgency_scanner.scan_text(scam_text_en)
    assert res_scam_en["detected"]
    assert res_scam_en["urgency_score"] > 0.70

    scam_text_hi = "Aapka bank account block ho gaya hai, jaldi se OTP batao kisi ko mat batana."
    res_scam_hi = urgency_scanner.scan_text(scam_text_hi)
    assert res_scam_hi["detected"]
    assert res_scam_hi["urgency_score"] > 0.70

def test_risk_fusion_engine():
    # Test low-risk scenario
    low_eval = risk_engine.evaluate_risk(
        model_result={"smoothed_probability": 0.12},
        acoustic_features={"discontinuity": {"discontinuity_score": 0.1}, "prosodic_spoof_score": 0.15},
        nlp_result={"urgency_score": 0.0, "matched_phrases": []}
    )
    assert low_eval["risk_score"] < 30
    assert low_eval["verdict"] == "Low"

    # Test critical-risk scenario
    crit_eval = risk_engine.evaluate_risk(
        model_result={"smoothed_probability": 0.88},
        acoustic_features={"discontinuity": {"discontinuity_score": 0.85}, "prosodic_spoof_score": 0.78},
        nlp_result={"urgency_score": 0.95, "matched_phrases": ["transfer money", "OTP"]},
        caller_metadata={"is_unknown_number": True, "is_voip_spoofed": True}
    )
    assert crit_eval["risk_score"] > 80
    assert crit_eval["verdict"] in ["High", "Critical"]
    assert len(crit_eval["forensic_reasons"]) > 0

def test_privacy_embedding_hasher():
    audio1 = np.random.uniform(-0.5, 0.5, 8000).astype(np.float32)
    audio2 = audio1.copy()
    
    hash1 = privacy_hasher.generate_hash(audio1)
    hash2 = privacy_hasher.generate_hash(audio2)
    
    # Deterministic for identical acoustic input
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex string
