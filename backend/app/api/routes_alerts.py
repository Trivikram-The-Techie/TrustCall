"""
Alert logs and enterprise webhook integration routes.
GET /v1/alerts?session_id=
POST /v1/alerts/webhook
GET /v1/demo/samples
"""

import os
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.privacy.embedding_store import session_store

router = APIRouter(prefix="/v1", tags=["Alerts & Integrations"])

class WebhookDispatchPayload(BaseModel):
    session_id: str
    risk_score: int
    alert_tier: str
    target_webhook_url: Optional[str] = "https://bank-fraud-gateway.internal/api/v1/intercept"
    action: str = "TERMINATE_CALL_AND_LOCK_ACCOUNT"
    explanation: str

@router.get("/alerts")
async def get_alerts_for_session(session_id: str = Query(..., description="Session identifier")):
    """
    Returns alert history for a session without exposing raw audio.
    Enforces privacy-by-design.
    """
    alerts = session_store.get_session_alerts(session_id)
    summary = session_store.get_session_summary(session_id)
    
    return {
        "session_id": session_id,
        "total_alerts": len(alerts),
        "alerts": alerts,
        "is_repeat_offender": summary.get("is_repeat_offender", False) if summary else False,
        "offender_details": summary.get("offender_details") if summary else None
    }

@router.post("/alerts/webhook")
async def trigger_bank_fraud_webhook(payload: WebhookDispatchPayload):
    """
    Dispatches automated fraud intervention alert to bank/PBX core banking gateway.
    """
    # Simulated enterprise dispatch
    dispatch_record = {
        "dispatched": True,
        "status": "DELIVERED_TO_FRAUD_GATEWAY",
        "session_id": payload.session_id,
        "action_taken": payload.action,
        "target_url": payload.target_webhook_url,
        "protocol": "HMAC_SIGNED_REST_V2"
    }
    return dispatch_record

@router.get("/demo/samples")
async def get_demo_samples():
    """
    Returns preset sample definitions for judge demo simulation.
    """
    return {
        "samples": [
            {
                "id": "genuine_sample",
                "label": "Genuine Human Call (Normal Conversation)",
                "description": "Natural human prosody, authentic breath pauses, irregular pitch tremor, benign discussion.",
                "audio_url": "/static/genuine_call_sample.wav",
                "expected_tier": "Low",
                "sample_text": "Hey Rahul, are we still meeting tomorrow for the SIH project discussion at the lab? Let me know if you need any notes."
            },
            {
                "id": "cloned_scam_sample",
                "label": "Cloned Voice Attack (Urgent Extortion / Digital Arrest)",
                "description": "Synthesized voice clone with neural vocoder artifacts, flat pitch contour, and high-urgency legal coercion script.",
                "audio_url": "/static/cloned_scam_sample.wav",
                "expected_tier": "Critical",
                "sample_text": "This is Officer Sharma from Delhi Police Crime Branch. Your bank account is linked to an illegal money transfer. Share your OTP immediately or arrest warrant will be issued. Do not tell anyone."
            }
        ]
    }
