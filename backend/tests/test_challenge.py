"""
Unit and integration tests for Automated Out-of-Band Challenge-Response Protocol (Phase 3).
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.nlp.challenge_engine import challenge_engine
from app.models.risk_engine import risk_engine

client = TestClient(app)

def test_challenge_generator_all_variants():
    """Verifies randomized dynamic challenge generation across all 5 variants."""
    variants = ["standard_digits", "backwards_digits", "hindi_words", "telugu_words", "code_and_city"]
    for v in variants:
        chal = challenge_engine.generate_challenge(variant=v)
        assert "challenge_id" in chal
        assert chal["challenge_id"].startswith("CHAL-")
        assert len(chal["code"]) == 4
        assert chal["variant"] == v
        assert "prompt_text" in chal
        assert len(chal["prompt_text"]) > 10

def test_speech_onset_latency_measurement():
    """Verifies that speech-onset detector accurately isolates delay before audio energy onset."""
    sr = 16000
    # 500ms silence (0.5s = 8000 samples) followed by 1s voiced tone (440Hz sine wave)
    silence = np.zeros(8000, dtype=np.float32)
    tone = np.sin(2 * np.pi * 440 * np.linspace(0, 1.0, 16000)).astype(np.float32) * 0.4
    audio = np.concatenate([silence, tone])

    latency = challenge_engine.measure_speech_onset_latency(audio, sr=sr)
    # Measured latency should be around 500ms (within 80ms VAD window tolerance)
    assert 420.0 <= latency <= 580.0, f"Expected ~500ms latency, got {latency}ms"

def test_transcript_correctness_verification():
    """Verifies fuzzy and multilingual phonetic matching across variants."""
    # Standard digits
    chal_std = {"variant": "standard_digits", "code": "8492"}
    assert challenge_engine.verify_transcript_correctness("security code 8492", chal_std)[0] is True
    assert challenge_engine.verify_transcript_correctness("eight four nine two", chal_std)[0] is True
    assert challenge_engine.verify_transcript_correctness("code is 1111", chal_std)[0] is False

    # Backwards digits
    chal_back = {"variant": "backwards_digits", "code": "8492"}
    assert challenge_engine.verify_transcript_correctness("reversed is 2948", chal_back)[0] is True
    assert challenge_engine.verify_transcript_correctness("8492", chal_back)[0] is False

    # Hindi words
    chal_hi = {"variant": "hindi_words", "code": "8492"}
    assert challenge_engine.verify_transcript_correctness("aath chaar nau do", chal_hi)[0] is True

    # Telugu words
    chal_te = {"variant": "telugu_words", "code": "8492"}
    assert challenge_engine.verify_transcript_correctness("enimidi naalugu tommidi rendu", chal_te)[0] is True

    # Code and city
    chal_city = {"variant": "code_and_city", "code": "8492"}
    assert challenge_engine.verify_transcript_correctness("code 8492 in Mumbai city", chal_city)[0] is True

def test_latency_classification_and_scoring():
    """Verifies that human cognitive latency passes, while TTS lag (>2.2s) triggers failure."""
    chal = challenge_engine.generate_challenge("standard_digits")
    code = chal["code"]

    # 1. Human Cognitive Latency (650ms)
    res_human = challenge_engine.evaluate_challenge_response(
        challenge_id=chal["challenge_id"],
        transcript_override=f"code is {code}",
        client_latency_ms=650.0
    )
    assert res_human["passed"] is True
    assert res_human["latency_tier"] == "human_natural"
    assert res_human["score_multiplier"] <= 0.20

    # 2. TTS Pipeline Latency Spike (2800ms)
    res_bot = challenge_engine.evaluate_challenge_response(
        challenge_id=chal["challenge_id"],
        transcript_override=f"code is {code}",
        client_latency_ms=2800.0
    )
    assert res_bot["passed"] is False
    assert res_bot["latency_tier"] == "tts_generative_lag"
    assert res_bot["score_multiplier"] >= 0.85

def test_risk_engine_challenge_integration():
    """Verifies that challenge verification recalibrates overall risk score in risk_engine."""
    dummy_model = {"smoothed_probability": 0.80, "raw_probability": 0.80}
    dummy_feat = {"discontinuity": {}, "pitch": {}, "perturbation": {}}

    # Pre-challenge risk (without challenge signal)
    pre_risk = risk_engine.evaluate_risk(
        model_result=dummy_model,
        acoustic_features=dummy_feat,
        nlp_result={"urgency_score": 0.0}
    )
    assert pre_risk["risk_score"] >= 70

    # Post-challenge PASS (human confirmed) -> Drops to Low tier
    pass_eval = {"passed": True, "expected_code": "8492", "latency_ms": 620.0}
    calibrated_pass = risk_engine.evaluate_risk(
        model_result=dummy_model,
        acoustic_features=dummy_feat,
        nlp_result={"urgency_score": 0.0},
        challenge_result=pass_eval
    )
    assert calibrated_pass["risk_score"] <= 20
    assert calibrated_pass["verdict"] == "Low"

    # Post-challenge FAIL (bot TTS lag) -> Surges to Critical
    fail_eval = {"passed": False, "explanation": "Excessive 2800ms TTS latency lag", "latency_ms": 2800.0}
    calibrated_fail = risk_engine.evaluate_risk(
        model_result=dummy_model,
        acoustic_features=dummy_feat,
        nlp_result={"urgency_score": 0.0},
        challenge_result=fail_eval
    )
    assert calibrated_fail["risk_score"] >= 88
    assert calibrated_fail["verdict"] == "Critical"

def test_challenge_api_endpoints():
    """Integration test for GET /v1/challenge/generate and POST /v1/challenge/verify."""
    # 1. Generate challenge
    gen_res = client.get("/v1/challenge/generate?variant=standard_digits")
    assert gen_res.status_code == 200
    chal = gen_res.json()
    assert "challenge_id" in chal
    assert "code" in chal

    # 2. Verify with Demo Override Pass
    verify_res_pass = client.post("/v1/challenge/verify", json={
        "challenge_id": chal["challenge_id"],
        "demo_override": "pass"
    })
    assert verify_res_pass.status_code == 200
    data_pass = verify_res_pass.json()
    assert data_pass["challenge_evaluation"]["passed"] is True
    assert data_pass["calibrated_risk"]["risk_score"] <= 20
    assert "limitation_note" in data_pass

    # 3. Verify with Demo Override Fail
    verify_res_fail = client.post("/v1/challenge/verify", json={
        "challenge_id": chal["challenge_id"],
        "demo_override": "fail_latency"
    })
    assert verify_res_fail.status_code == 200
    data_fail = verify_res_fail.json()
    assert data_fail["challenge_evaluation"]["passed"] is False
    assert data_fail["calibrated_risk"]["risk_score"] >= 88
