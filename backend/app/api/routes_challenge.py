"""
REST API routes for Automated Out-of-Band Challenge-Response Protocol.
GET  /v1/challenge/generate
POST /v1/challenge/verify
"""

import time
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.nlp.challenge_engine import challenge_engine
from app.audio.feature_extraction import decode_base64_audio, extract_acoustic_features
from app.models.spoof_detector import spoof_detector
from app.models.risk_engine import risk_engine
from app.config import settings

router = APIRouter(prefix="/v1/challenge", tags=["Automated Challenge Protocol"])

class ChallengeVerifyRequest(BaseModel):
    challenge_id: str = Field(..., description="Active challenge ID returned by /v1/challenge/generate")
    audio_base64: Optional[str] = Field(default=None, description="Optional caller response audio in Base64")
    transcript_text: Optional[str] = Field(default=None, description="Optional verbal transcript from client speech recognition")
    client_latency_ms: Optional[float] = Field(default=None, description="Measured response latency from challenge end to speech onset (ms)")
    session_id: Optional[str] = Field(default=None, description="Active call session identifier")
    demo_override: Optional[str] = Field(default=None, description="Optional manual demo override: 'pass' | 'fail_latency' | 'fail_code'")

@router.get("/generate")
async def generate_security_challenge(
    variant: str = Query(
        default="standard_digits",
        description="Challenge variant: 'standard_digits', 'backwards_digits', 'hindi_words', 'telugu_words', 'code_and_city'"
    )
):
    """
    Generates a randomized dynamic security challenge.
    Variants require live cognitive comprehension and translation,
    exposing generative TTS pipeline latency or soundboard limitations.
    """
    try:
        challenge = challenge_engine.generate_challenge(variant=variant)
        return challenge
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Challenge generation failed: {str(e)}")

@router.post("/verify")
async def verify_security_challenge(payload: ChallengeVerifyRequest):
    """
    Verifies caller challenge reply: measures acoustic speech-onset latency,
    evaluates transcript correctness, and recalibrates the session threat risk score.
    """
    # 1. Handle Demo Override (clearly labelled for testing)
    if payload.demo_override == "pass":
        chal = challenge_engine._active_challenges.get(payload.challenge_id) or {"code": "8492"}
        eval_result = {
            "challenge_id": payload.challenge_id,
            "variant": chal.get("variant", "standard_digits"),
            "expected_code": chal.get("code", "8492"),
            "transcript": f"Security code {chal.get('code', '8492')}",
            "is_code_correct": True,
            "latency_ms": 680.0,
            "latency_tier": "human_natural",
            "passed": True,
            "verdict": "Passed (Human Verified - Demo Override)",
            "explanation": f"Caller echoed code '{chal.get('code', '8492')}' with organic cognitive timing (680 ms).",
            "score_multiplier": 0.14,
            "timestamp": time.time()
        }
    elif payload.demo_override == "fail_latency":
        chal = challenge_engine._active_challenges.get(payload.challenge_id) or {"code": "8492"}
        eval_result = {
            "challenge_id": payload.challenge_id,
            "variant": chal.get("variant", "standard_digits"),
            "expected_code": chal.get("code", "8492"),
            "transcript": f"{chal.get('code', '8492')}",
            "is_code_correct": True,
            "latency_ms": 2850.0,
            "latency_tier": "tts_generative_lag",
            "passed": False,
            "verdict": "Failed (TTS Pipeline Latency Spike - Demo Override)",
            "explanation": f"Code matched but cognitive delay was 2,850 ms (exceeds 2,200 ms TTS threshold).",
            "score_multiplier": 0.88,
            "timestamp": time.time()
        }
    elif payload.demo_override == "fail_code":
        chal = challenge_engine._active_challenges.get(payload.challenge_id) or {"code": "8492"}
        eval_result = {
            "challenge_id": payload.challenge_id,
            "variant": chal.get("variant", "standard_digits"),
            "expected_code": chal.get("code", "8492"),
            "transcript": "Hello? Who is speaking?",
            "is_code_correct": False,
            "latency_ms": 1400.0,
            "latency_tier": "human_natural",
            "passed": False,
            "verdict": "Failed (Incorrect Code - Demo Override)",
            "explanation": f"Caller evaded code repetition. Expected '{chal.get('code', '8492')}', received evasive response.",
            "score_multiplier": 0.92,
            "timestamp": time.time()
        }
    else:
        # 2. Automated Acoustic & Transcript Processing
        audio = None
        if payload.audio_base64:
            try:
                audio = decode_base64_audio(payload.audio_base64, target_sr=settings.SAMPLE_RATE)
            except Exception as e:
                print(f"[WARN] Failed to decode audio_base64: {e}")

        eval_result = challenge_engine.evaluate_challenge_response(
            challenge_id=payload.challenge_id,
            audio=audio,
            transcript_override=payload.transcript_text,
            client_latency_ms=payload.client_latency_ms,
            sr=settings.SAMPLE_RATE
        )

    # 3. Fuse into Risk Engine
    dummy_model = {
        "smoothed_probability": 0.10 if eval_result["passed"] else 0.85,
        "raw_probability": 0.10 if eval_result["passed"] else 0.85,
        "is_synthetic": not eval_result["passed"],
        "confidence": 0.90
    }
    dummy_feat = {"discontinuity": {}, "pitch": {}, "perturbation": {}, "vocoder_metrics": {}}

    risk_eval = risk_engine.evaluate_risk(
        model_result=dummy_model,
        acoustic_features=dummy_feat,
        nlp_result={"urgency_score": 0.0 if eval_result["passed"] else 0.75},
        caller_metadata={"is_unknown_number": not eval_result["passed"]},
        challenge_result=eval_result
    )

    return {
        "challenge_evaluation": eval_result,
        "calibrated_risk": {
            "risk_score": risk_eval["risk_score"],
            "verdict": risk_eval["verdict"],
            "status_text": risk_eval["status_text"],
            "color": risk_eval["color"],
            "action_recommendation": risk_eval["action_recommendation"],
            "explanation": risk_eval["explanation"],
            "forensic_reasons": risk_eval["forensic_reasons"]
        },
        "limitation_note": (
            "A live human operator using a voice changer can pass this challenge; "
            "it specifically targets automated TTS pipelines."
        )
    }
