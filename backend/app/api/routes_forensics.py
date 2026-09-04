"""
FastAPI route definitions for Forensic Audit Evidence Bags and Verification.
Provides tamper-proof incident certification for cyber defense, banking gateways, and SIEMs.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from app.privacy.evidence_report import forensic_evidence_generator
from app.privacy.embedding_store import session_store

router = APIRouter(prefix="/v1/forensics", tags=["Forensic Evidence & Audit"])

class ReportRequest(BaseModel):
    session_id: str = Field(..., description="Unique call or file analysis session ID")
    risk_score: int = Field(..., ge=0, le=100, description="Overall risk score (0-100)")
    verdict: str = Field(..., description="Risk tier: Low, Medium, High, or Critical")
    explanation: str = Field(..., description="Primary forensic rationale")
    forensic_reasons: Optional[List[str]] = Field(default=[], description="List of detected anomaly flags")
    layers: Optional[Dict[str, Any]] = Field(default=None, description="5-layer biometric status dict")
    components: Optional[Dict[str, float]] = Field(default=None, description="Score component breakdown")
    caller_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata such as caller ID")
    nlp_keywords: Optional[List[str]] = Field(default=[], description="Detected scam keywords")
    embedding_hash: Optional[str] = Field(default=None, description="Non-reversible speaker hash")

@router.post("/generate-report", status_code=status.HTTP_201_CREATED)
async def generate_forensic_report(payload: ReportRequest):
    """
    Generates a cryptographically signed forensic evidence bag conforming to Section 65B/66D IT Act.
    """
    try:
        evidence_bag = forensic_evidence_generator.generate_evidence_bag(
            session_id=payload.session_id,
            risk_score=payload.risk_score,
            verdict=payload.verdict,
            explanation=payload.explanation,
            forensic_reasons=payload.forensic_reasons,
            layers=payload.layers,
            components=payload.components,
            caller_metadata=payload.caller_metadata,
            nlp_keywords=payload.nlp_keywords,
            embedding_hash=payload.embedding_hash
        )
        return evidence_bag
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forensic evidence certificate: {str(e)}"
        )

@router.post("/verify-report", status_code=status.HTTP_200_OK)
async def verify_forensic_report(evidence_bag: Dict[str, Any]):
    """
    Verifies the SHA-256 HMAC integrity of an exported evidence bag to confirm zero tampering.
    """
    if not evidence_bag or "tamper_proof_signature" not in evidence_bag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing tamper_proof_signature in evidence bag"
        )
    return forensic_evidence_generator.verify_evidence_integrity(evidence_bag)

@router.get("/session/{session_id}", status_code=status.HTTP_200_OK)
async def get_session_forensic_report(session_id: str):
    """
    Retrieves and generates an on-the-fly forensic audit report for a previously recorded session.
    """
    summary = session_store.get_session_summary(session_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found or expired from TTL memory"
        )

    risk_scores = summary.get("risk_scores", [])
    max_risk = max([r["risk_score"] for r in risk_scores]) if risk_scores else 15
    alerts = summary.get("alert_history", [])
    verdict = alerts[-1]["alert_tier"] if alerts else ("Critical" if max_risk >= 85 else ("High" if max_risk >= 60 else "Low"))
    explanation = alerts[-1]["explanation"] if alerts else "Acoustic signals analyzed within normal human parameters."

    evidence_bag = forensic_evidence_generator.generate_evidence_bag(
        session_id=session_id,
        risk_score=max_risk,
        verdict=verdict,
        explanation=explanation,
        forensic_reasons=[a["explanation"] for a in alerts],
        embedding_hash=summary.get("embedding_hash")
    )
    return evidence_bag
