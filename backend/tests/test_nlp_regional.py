"""
Tests for regional Indian language scam keyword and coercion detection.
Covers Telugu, Tamil, Marathi, and Bengali.
"""

from app.nlp.urgency_keywords import urgency_scanner

def test_telugu_scam_keywords():
    res = urgency_scanner.scan_text("Meeru ventane dabbu pampandi lekapothe police case aindi.")
    assert res["detected"] is True
    assert res["urgency_score"] >= 0.70
    assert any("financial_coercion" in c for c in res["categories"])

def test_tamil_scam_keywords():
    res = urgency_scanner.scan_text("Ungal bank account block aagirukku. OTP sollunga.")
    assert res["detected"] is True
    assert res["urgency_score"] >= 0.70
    assert any("otp_credential_theft" in c for c in res["categories"])

def test_marathi_scam_keywords():
    res = urgency_scanner.scan_text("Tumche khata bandh zala ahe, tatkal paise pathva.")
    assert res["detected"] is True
    assert res["urgency_score"] >= 0.70

def test_bengali_scam_keywords():
    res = urgency_scanner.scan_text("Apnar account block hoyeche, OTP din.")
    assert res["detected"] is True
    assert res["urgency_score"] >= 0.70
