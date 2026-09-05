"""
REST API routes for single-clip scoring and file uploads.
POST /v1/score
POST /v1/score/upload
"""

import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.audio.feature_extraction import (
    decode_base64_audio, 
    decode_audio_bytes, 
    extract_acoustic_features
)
from app.models.spoof_detector import spoof_detector
from app.nlp.urgency_keywords import urgency_scanner
from app.nlp.transcriber import transcriber
from app.models.risk_engine import risk_engine
from app.privacy.embedding_store import privacy_hasher, session_store
from app.models.vocoder_fingerprint import vocoder_fingerprinter

router = APIRouter(prefix="/v1", tags=["Scoring"])

class ScoreRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64 encoded WAV or PCM audio")
    sample_rate: Optional[int] = Field(default=16000, description="Audio sample rate (default 16kHz)")
    language_hint: Optional[str] = Field(default="en", description="Optional language identifier")
    text_transcript: Optional[str] = Field(default=None, description="Optional text transcript if available")
    caller_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional caller flags")
    session_id: Optional[str] = Field(default=None, description="Session ID for tracking")

class ScoreResponse(BaseModel):
    session_id: str
    risk_score: int
    verdict: str
    status_text: str
    color: str
    action_recommendation: str
    explanation: str
    forensic_reasons: list
    components: dict
    contributions: dict
    transcript: str
    embedding_hash: str
    is_repeat_offender: bool
    offender_details: Optional[dict] = None
    vocoder_fingerprint: Optional[dict] = None

@router.post("/score", response_model=ScoreResponse)
async def score_audio_clip(payload: ScoreRequest):
    """
    Analyzes an audio clip provided as a base64 string.
    Extracts acoustic features, evaluates neural anti-spoofing model,
    scans for scam urgency indicators, and returns a 0-100 risk score with forensic explanation.
    """
    session_id = payload.session_id or str(uuid.uuid4())
    
    try:
        audio = decode_base64_audio(payload.audio_base64, target_sr=settings.SAMPLE_RATE)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode audio: {str(e)}")

    if len(audio) < 160:
        raise HTTPException(status_code=400, detail="Audio is too short or empty (minimum 10ms required).")

    # 1. Feature Extraction
    features = extract_acoustic_features(audio, sr=settings.SAMPLE_RATE)
    
    # 2. Deep Anti-Spoofing Detection
    model_result = spoof_detector.predict_chunk(audio, sr=settings.SAMPLE_RATE, use_history=False)
    
    # 3. Transcription & Urgency Scanning
    transcript_text = transcriber.transcribe_chunk(
        audio, 
        sr=settings.SAMPLE_RATE, 
        text_override=payload.text_transcript
    )
    nlp_result = urgency_scanner.scan_text(transcript_text)
    
    # 4. Non-reversible Hash Generation
    embedding_hash = privacy_hasher.generate_hash(audio)
    
    # 5. Multi-Signal Fusion
    risk_eval = risk_engine.evaluate_risk(
        model_result=model_result,
        acoustic_features=features,
        nlp_result=nlp_result,
        caller_metadata=payload.caller_metadata
    )
    
    # 6. Vocoder Architecture Fingerprinting
    fingerprint = vocoder_fingerprinter.analyze_audio_fingerprint(
        audio=audio,
        acoustic_features=features,
        spoof_probability=model_result["smoothed_probability"]
    )

    # 7. Ephemeral Session Logging (Zero Raw Audio Saved)
    session_data = session_store.record_chunk_risk(
        session_id=session_id,
        risk_score=risk_eval["risk_score"],
        alert_tier=risk_eval["verdict"],
        components=risk_eval["components"],
        explanation=risk_eval["explanation"],
        embedding_hash=embedding_hash
    )
    
    return ScoreResponse(
        session_id=session_id,
        risk_score=risk_eval["risk_score"],
        verdict=risk_eval["verdict"],
        status_text=risk_eval["status_text"],
        color=risk_eval["color"],
        action_recommendation=risk_eval["action_recommendation"],
        explanation=risk_eval["explanation"],
        forensic_reasons=risk_eval["forensic_reasons"],
        components=risk_eval["components"],
        contributions=risk_eval["contributions"],
        transcript=transcript_text,
        embedding_hash=embedding_hash,
        is_repeat_offender=session_data.get("is_repeat_offender", False),
        offender_details=session_data.get("offender_details"),
        vocoder_fingerprint=fingerprint
    )


@router.post("/score/upload", response_model=ScoreResponse)
async def score_audio_file(
    file: UploadFile = File(...),
    text_transcript: Optional[str] = Form(None),
    is_unknown_number: Optional[bool] = Form(False),
    session_id: Optional[str] = Form(None)
):
    """
    Accepts multipart file upload (WAV, MP3, etc.), decodes, and runs full risk evaluation.
    """
    s_id = session_id or str(uuid.uuid4())
    content = await file.read()
    
    try:
        audio = decode_audio_bytes(content, target_sr=settings.SAMPLE_RATE)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read audio file: {str(e)}")

    if len(audio) < 160:
        raise HTTPException(status_code=400, detail="Audio file contains insufficient samples.")

    # Features
    features = extract_acoustic_features(audio, sr=settings.SAMPLE_RATE)
    # Model
    model_result = spoof_detector.predict_chunk(audio, sr=settings.SAMPLE_RATE, use_history=False)
    # NLP
    transcript_text = transcriber.transcribe_chunk(audio, sr=settings.SAMPLE_RATE, text_override=text_transcript)
    nlp_result = urgency_scanner.scan_text(transcript_text)
    # Hash
    embedding_hash = privacy_hasher.generate_hash(audio)
    
    metadata = {"is_unknown_number": is_unknown_number}
    
    # Risk Fusion
    risk_eval = risk_engine.evaluate_risk(
        model_result=model_result,
        acoustic_features=features,
        nlp_result=nlp_result,
        caller_metadata=metadata
    )
    
    # Vocoder Fingerprint
    fingerprint = vocoder_fingerprinter.analyze_audio_fingerprint(
        audio=audio,
        acoustic_features=features,
        spoof_probability=model_result["smoothed_probability"]
    )

    session_data = session_store.record_chunk_risk(
        session_id=s_id,
        risk_score=risk_eval["risk_score"],
        alert_tier=risk_eval["verdict"],
        components=risk_eval["components"],
        explanation=risk_eval["explanation"],
        embedding_hash=embedding_hash
    )
    
    return ScoreResponse(
        session_id=s_id,
        risk_score=risk_eval["risk_score"],
        verdict=risk_eval["verdict"],
        status_text=risk_eval["status_text"],
        color=risk_eval["color"],
        action_recommendation=risk_eval["action_recommendation"],
        explanation=risk_eval["explanation"],
        forensic_reasons=risk_eval["forensic_reasons"],
        components=risk_eval["components"],
        contributions=risk_eval["contributions"],
        transcript=transcript_text,
        embedding_hash=embedding_hash,
        is_repeat_offender=session_data.get("is_repeat_offender", False),
        offender_details=session_data.get("offender_details"),
        vocoder_fingerprint=fingerprint
    )
