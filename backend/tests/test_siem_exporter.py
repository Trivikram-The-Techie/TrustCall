"""
Tests for SIEM Common Event Format (CEF) and Syslog telemetry exporter.
"""

import json
from app.security.siem_exporter import siem_exporter

def test_cef_event_formatting():
    cef = siem_exporter.format_cef_event(
        session_id="CALL-SIEM-101",
        risk_score=94,
        verdict="Critical",
        threat_type="DIGITAL_ARREST_EXTORTION",
        caller_id="+919110088231",
        explanation="Deep neural clone detected."
    )
    assert cef.startswith("CEF:0|VoiceShield|TrustCall|1.3|VOICE_SPOOF_001|")
    assert "cn1=94" in cef
    assert "cs2=Critical" in cef
    assert "src=+919110088231" in cef

def test_syslog_json_formatting():
    log_str = siem_exporter.format_syslog_json(
        session_id="CALL-SIEM-102",
        risk_score=78,
        verdict="High",
        threat_type="BANKING_CREDENTIAL_PHISHING",
        caller_id="+919820144521",
        explanation="OTP phishing phrase detected."
    )
    data = json.loads(log_str)
    assert data["session_id"] == "CALL-SIEM-102"
    assert data["risk_score"] == 78
    assert data["verdict"] == "High"
    assert data["app_name"] == "voiceshield-interceptor"
