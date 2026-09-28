"""
Automated Scam Threat Taxonomy and Legal Penal Code Mapping.
Categorizes detected voice cloning attacks into specific Indian cyber fraud vectors
and maps them to Bharatiya Nyaya Sanhita 2023 (BNS) and Information Technology Act 2000 sections.
"""

from typing import Dict, List, Any

SCAM_TAXONOMY = {
    "DIGITAL_ARREST_EXTORTION": {
        "title": "Digital Arrest & Law Enforcement Impersonation",
        "description": "Criminals posing as CBI/ED/Police officers intimidating victims via video/audio calls.",
        "bns_sections": ["Section 319(2) (Cheating by personation)", "Section 308(2) (Extortion)", "Section 204 (Impersonating a public servant)"],
        "it_act_sections": ["Section 66D (Cheating by personation using computer resource)"],
        "severity": "CRITICAL",
        "keywords": ["cbi", "police", "arrest", "digital arrest", "customs", "narcotics", "court order", "fir", "crime branch"]
    },
    "BANKING_CREDENTIAL_PHISHING": {
        "title": "Banking Gateway & OTP Exfiltration",
        "description": "Fraudulent claims of blocked debit cards or expired KYC designed to steal OTPs and passwords.",
        "bns_sections": ["Section 318(4) (Cheating and dishonestly inducing delivery of property)"],
        "it_act_sections": ["Section 66C (Identity theft)", "Section 66D (Cheating by personation)"],
        "severity": "HIGH",
        "keywords": ["otp", "debit card", "atm card", "kyc", "bank account", "freeze", "blocked", "upi pin", "cvv"]
    },
    "FEDEX_CUSTOMS_NARCOTICS": {
        "title": "Illegal Courier & Customs Drug Parcel Scam",
        "description": "False alerts claiming an overseas parcel containing illegal contraband, narcotics, or passports.",
        "bns_sections": ["Section 308(2) (Extortion)", "Section 319(2) (Personation)"],
        "it_act_sections": ["Section 66D (Cheating by personation)"],
        "severity": "CRITICAL",
        "keywords": ["parcel", "courier", "fedex", "customs", "drugs", "passport", "illegal items", "taiwan parcel", "mumbai customs"]
    },
    "FAMILY_KIDNAPPING_EMERGENCY": {
        "title": "Synthetic Family Voice Emergency / Kidnapping",
        "description": "Cloned family member voice claiming immediate hospitalization, accident, or police detention.",
        "bns_sections": ["Section 308(5) (Extortion putting person in fear of death/grievous hurt)", "Section 318(4) (Cheating)"],
        "it_act_sections": ["Section 66D (Cheating by personation)"],
        "severity": "CRITICAL",
        "keywords": ["accident", "hospital", "icu", "kidnapped", "custody", "bail money", "bachao", "emergency fund"]
    },
    "ELECTRICITY_BILL_DISCONNECTION": {
        "title": "Utility Disconnection Extortion",
        "description": "Urgent notification threatening power or water cutoff within hours unless paid to personal UPI.",
        "bns_sections": ["Section 318(4) (Cheating)"],
        "it_act_sections": ["Section 66D (Cheating by personation)"],
        "severity": "MEDIUM",
        "keywords": ["electricity bill", "power cut", "disconnection", "bijli bill", "officer number", "pay immediately"]
    }
}

class ScamThreatClassifier:
    """Classifies scam transcripts into legal actionable threat intelligence."""

    def classify_threat(self, transcript: str, nlp_categories: List[str] = None) -> Dict[str, Any]:
        if not transcript or not transcript.strip():
            return {
                "primary_threat": "GENERIC_ACOUSTIC_ANOMALY",
                "title": "Acoustic Discontinuity / Unverified Call",
                "severity": "LOW",
                "bns_sections": [],
                "it_act_sections": [],
                "confidence": 0.0
            }

        text_lower = transcript.lower()
        matched_scores = {}

        for code, details in SCAM_TAXONOMY.items():
            matches = sum(1 for kw in details["keywords"] if kw in text_lower)
            if matches > 0:
                matched_scores[code] = matches

        if not matched_scores:
            return {
                "primary_threat": "UNSPECIFIED_TELECOM_SCAM",
                "title": "Unspecified Coercive Telephony Threat",
                "severity": "MEDIUM",
                "bns_sections": ["Section 318(4) (Cheating)"],
                "it_act_sections": ["Section 66D (Cheating by personation)"],
                "confidence": 0.50
            }

        primary_code = max(matched_scores, key=matched_scores.get)
        threat_info = SCAM_TAXONOMY[primary_code]

        return {
            "primary_threat": primary_code,
            "title": threat_info["title"],
            "severity": threat_info["severity"],
            "bns_sections": threat_info["bns_sections"],
            "it_act_sections": threat_info["it_act_sections"],
            "match_count": matched_scores[primary_code],
            "confidence": min(1.0, 0.60 + matched_scores[primary_code] * 0.15)
        }

threat_classifier = ScamThreatClassifier()
