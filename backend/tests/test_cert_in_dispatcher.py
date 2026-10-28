"""
Tests for CERT-In & 1930 Cyber Helpline Incident Dispatcher.
"""

from app.security.cert_in_dispatcher import cert_in_dispatcher

def test_incident_package_generation():
    pkg = cert_in_dispatcher.build_incident_package(
        session_id="CALL-CERT-001",
        caller_number="+919110088231",
        risk_score=96,
        threat_type="DIGITAL_ARREST_EXTORTION",
        evidence_id="TC-EVD-9921",
        tamper_proof_sig="a1b2c3d4e5f6",
        transcript_snippet="CBI arrest warrant issued. Pay fine."
    )
    assert pkg["incident_id"].startswith("CERTIN-INC-")
    assert pkg["severity_level"] == "CRITICAL"
    assert pkg["telecom_identifiers"]["suspect_caller_id"] == "+919110088231"
    assert "Section 65B(4)" in pkg["evidence_integrity"]["statutory_basis"]
    assert len(pkg["recommended_enforcement_action"]) >= 3
