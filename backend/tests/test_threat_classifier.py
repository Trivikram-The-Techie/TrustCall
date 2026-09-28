"""
Tests for Scam Threat Classifier and BNS/IT Act legal penal code mapping.
"""

from app.nlp.threat_classifier import threat_classifier

def test_digital_arrest_classification():
    text = "This is CBI Officer Sharma from Delhi Police Crime Branch. Digital arrest warrant issued."
    res = threat_classifier.classify_threat(text)
    assert res["primary_threat"] == "DIGITAL_ARREST_EXTORTION"
    assert res["severity"] == "CRITICAL"
    assert any("Section 319" in s for s in res["bns_sections"])
    assert any("Section 66D" in s for s in res["it_act_sections"])

def test_banking_phishing_classification():
    text = "Your SBI debit card is blocked. Share the 6 digit OTP immediately to reactivate."
    res = threat_classifier.classify_threat(text)
    assert res["primary_threat"] == "BANKING_CREDENTIAL_PHISHING"
    assert res["severity"] == "HIGH"

def test_fedex_parcel_classification():
    text = "Customs department has seized your FedEx courier parcel containing illegal narcotics and fake passport."
    res = threat_classifier.classify_threat(text)
    assert res["primary_threat"] == "FEDEX_CUSTOMS_NARCOTICS"
    assert res["severity"] == "CRITICAL"
