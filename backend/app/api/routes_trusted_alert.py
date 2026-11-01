"""
Phase 5: Trusted Contact Alert & Bank Webhook Demo Routes.
All outputs are SIMULATED DEMO — no real SMS/WhatsApp/bank integration.
"""

import uuid
import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.config import settings

router = APIRouter(prefix="/v1/alert", tags=["Trusted Contact Alert (Demo)"])

_SIMULATED_DISCLAIMER = (
    "SIMULATED DEMO — No real message sent. "
    "This is a fictional alert for SIH TrustCall demonstration only."
)

# ─────────────────────────────────────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class TrustedAlertRequest(BaseModel):
    session_id: str = Field(default="demo-session")
    risk_score: int = Field(ge=0, le=100)
    verdict: str
    caller_number: str = Field(default="+91 XXXXXXXXXX")
    transcript_snippet: Optional[str] = None
    detected_intent: Optional[str] = None


class BankWebhookRequest(BaseModel):
    session_id: str = Field(default="demo-session")
    risk_score: int = Field(ge=0, le=100)
    verdict: str
    caller_number: str = Field(default="+91 XXXXXXXXXX")
    account_last4: str = Field(default="4321")
    amount: str = Field(default="₹50,000")


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/trusted-contact")
async def send_trusted_contact_alert(req: TrustedAlertRequest):
    """
    SIMULATED DEMO — Produces a mock SMS/WhatsApp-style alert payload
    that would be sent to the configured family/trusted contact.
    No real message is sent.
    """
    if req.verdict not in ("High", "Critical"):
        raise HTTPException(
            status_code=400,
            detail="Trusted contact alerts are only triggered for High or Critical verdicts."
        )

    alert_id = f"ALERT-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    message_body = (
        f"🚨 TrustCall SECURITY ALERT\n"
        f"A suspicious call was detected on {req.caller_number}.\n"
        f"Risk: {req.verdict} ({req.risk_score}/100)\n"
        f"Intent: {req.detected_intent or 'Unknown'}\n"
        f"Snippet: \"{req.transcript_snippet or 'N/A'}\"\n"
        f"Action: Ask your family member to verify this call before sharing any details.\n"
        f"Alert ID: {alert_id}"
    )

    return {
        "simulated": True,
        "disclaimer": _SIMULATED_DISCLAIMER,
        "alert_id": alert_id,
        "timestamp": timestamp,
        "recipient": {
            "name": settings.TRUSTED_CONTACT_MOCK_NAME,
            "number": settings.TRUSTED_CONTACT_MOCK_NUMBER,
            "channel": "WhatsApp (SIMULATED)",
        },
        "message_body": message_body,
        "delivery_status": "SIMULATED_DELIVERED",
        "trigger": {
            "session_id": req.session_id,
            "risk_score": req.risk_score,
            "verdict": req.verdict,
            "caller_number": req.caller_number,
            "detected_intent": req.detected_intent,
        }
    }


@router.post("/bank-webhook")
async def bank_webhook_consumer(req: BankWebhookRequest):
    """
    SIMULATED DEMO — Mimics a bank-side webhook consumer that receives
    a TrustCall alert and puts a pending transaction on hold.
    """
    hold_id = f"HOLD-{uuid.uuid4().hex[:10].upper()}"
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    return {
        "simulated": True,
        "disclaimer": _SIMULATED_DISCLAIMER,
        "hold_id": hold_id,
        "timestamp": timestamp,
        "bank_action": "TRANSACTION_HELD",
        "account_last4": req.account_last4,
        "hold_amount": req.amount,
        "hold_reason": f"TrustCall risk alert: {req.verdict} ({req.risk_score}/100)",
        "caller_flagged": req.caller_number,
        "session_id": req.session_id,
        "recommended_action": (
            "Customer should call back on the official bank helpline "
            "before this hold is released. Estimated review time: 15 min."
        ),
        "release_url": "/v1/alert/bank-webhook/release (SIMULATED)"
    }


@router.get("/bank-webhook/demo")
async def bank_webhook_demo_state():
    """
    Returns a fixed demo 'transaction held' state for the UI to render.
    """
    return {
        "simulated": True,
        "disclaimer": _SIMULATED_DISCLAIMER,
        "hold_id": "HOLD-DEMO0001AA",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "bank_action": "TRANSACTION_HELD",
        "account_last4": "4321",
        "hold_amount": settings.BANK_WEBHOOK_DEMO_HOLD_AMOUNT,
        "hold_reason": "TrustCall risk alert: Critical (92/100)",
        "caller_flagged": "+91 8800012345 [BLOCKLISTED]",
        "session_id": "demo-session",
        "recommended_action": (
            "Customer should call back on the official bank helpline. "
            "Do NOT release until identity is verified."
        ),
    }
