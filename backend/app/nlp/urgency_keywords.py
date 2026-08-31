"""
Multilingual scam-phrase and urgency keyword detector.
Covers English, Hindi, and Hinglish fraud vectors tailored for Indian telecom/banking scams:
- Banking / OTP extortion
- Digital arrest / Police / CBI impersonation
- Emergency extortion / Family coercion
- Urgency and secrecy pressure
"""

import re
from typing import Dict, List, Any

# Keyword taxonomy with severity weights (1.0 = highest scam risk, 0.6 = moderate urgency)
SCAM_DICTIONARY = {
    "financial_coercion": {
        "weight": 1.0,
        "patterns": [
            r"\b(transfer\s+money|send\s+money|wire\s+funds?)\b",
            r"\b(paisa\s+(bhejo|transfer\s+karo|dalwao))\b",
            r"\b(bank\s+account\s+(blocked|suspended|hacked|deactivated))\b",
            r"\b(khata\s+block\s+ho\s+gaya)\b",
            r"\b(kyc\s+(update|expired|pending|verification))\b",
            r"\b(upi\s+pin|enter\s+pin|pin\s+batao|share\s+pin)\b",
            r"\b(scan\s+qr\s+code|qr\s+code\s+scan\s+karo)\b",
            r"\b(immediate(ly)?\s+payment|pay\s+now|pay\s+within\s+\d+\s+min)\b",
            r"\b(credit\s+card\s+limit|card\s+blocked|atm\s+card)\b"
        ]
    },
    "otp_credential_theft": {
        "weight": 1.0,
        "patterns": [
            r"\b(otp|one\s*time\s*password)\b",
            r"\b(otp\s+(share\s+karo|batao|bhejo|enter\s+karo|padho))\b",
            r"\b(share\s+(the\s+)?otp|tell\s+me\s+the\s+code|6\s*digit\s*code)\b",
            r"\b(cvv\s*number|card\s*expiry)\b"
        ]
    },
    "legal_impersonation_digital_arrest": {
        "weight": 0.95,
        "patterns": [
            r"\b(cbi|ed|enforcement\s+directorate|crime\s+branch|raw)\b",
            r"\b(police\s+(officer|inspector|commissioner|station|arrest))\b",
            r"\b(arrest\s+warrant|non\s*bailable\s*warrant|court\s+order)\b",
            r"\b(digital\s+arrest|skype\s+investigation|video\s+call\s+arrest)\b",
            r"\b(narcotics|customs\s+(department|seized|parcel))\b",
            r"\b(parcel\s+mein\s+(drugs|illegal|passport))\b",
            r"\b(fir\s+(register|lodged|file\s+ho\s+chuki))\b",
            r"\b(jail\s+(jana\s+padega|bheja\s+jayega))\b"
        ]
    },
    "secrecy_isolation_pressure": {
        "weight": 0.85,
        "patterns": [
            r"\b(don'?t\s+(tell|inform)\s+(anyone|family|police|bank))\b",
            r"\b(kisi\s+ko\s+mat\s+batana|ghar\s+walo\s+ko\s+mat\s+batao)\b",
            r"\b(don'?t\s+disconnect|do\s+not\s+hang\s+up|phone\s+mat\s+katna)\b",
            r"\b(keep\s+(this|the\s+call)\s+(secret|confidential))\b",
            r"\b(confidential\s+inquiry|secret\s+investigation)\b"
        ]
    },
    "family_medical_emergency": {
        "weight": 0.90,
        "patterns": [
            r"\b(hospital|accident|icu|operation|critical\s+condition)\b",
            r"\b(beta\s+police\s+ke\s+paas\s+hai|baccha\s+arrest\s+hai)\b",
            r"\b(your\s+(son|daughter|husband|wife)\s+is\s+in\s+(trouble|custody))\b",
            r"\b(bachane\s+ke\s+liye\s+paisa\s+chahiye|emergency\s+fund)\b"
        ]
    }
}


class UrgencyKeywordScanner:
    """
    Scans transcripts or text streams for high-risk fraud and urgency indicators.
    Returns urgency_score [0.0 - 1.0], category matches, and explainability text.
    """
    def __init__(self):
        self.compiled_rules = {}
        for category, data in SCAM_DICTIONARY.items():
            self.compiled_rules[category] = {
                "weight": data["weight"],
                "regexes": [re.compile(p, re.IGNORECASE) for p in data["patterns"]]
            }

    def scan_text(self, text: str) -> Dict[str, Any]:
        """
        Evaluates input text against scam categories.
        """
        if not text or not text.strip():
            return {
                "urgency_score": 0.0,
                "detected": False,
                "categories": [],
                "matched_phrases": [],
                "explanation": "No suspicious keywords detected."
            }

        matched_categories = []
        matched_phrases = []
        max_weight = 0.0
        total_hits = 0

        for category, info in self.compiled_rules.items():
            cat_matched = False
            for r in info["regexes"]:
                hits = r.findall(text)
                if hits:
                    cat_matched = True
                    total_hits += len(hits)
                    # Extract string representation
                    for h in hits:
                        phrase = h if isinstance(h, str) else (h[0] if isinstance(h, tuple) else str(h))
                        if phrase not in matched_phrases:
                            matched_phrases.append(phrase)
            if cat_matched:
                matched_categories.append(category)
                max_weight = max(max_weight, info["weight"])

        if total_hits == 0:
            return {
                "urgency_score": 0.0,
                "detected": False,
                "categories": [],
                "matched_phrases": [],
                "explanation": "No suspicious keywords detected."
            }

        # Dynamic urgency scaling based on hit count and category severity
        urgency_score = min(1.0, max_weight * (0.65 + min(0.35, total_hits * 0.15)))
        urgency_score = round(urgency_score, 3)

        readable_categories = [c.replace('_', ' ').title() for c in matched_categories]
        explanation = f"Scam indicators detected: {', '.join(readable_categories)} (Phrases: {', '.join(matched_phrases[:3])})"

        return {
            "urgency_score": urgency_score,
            "detected": True,
            "categories": matched_categories,
            "matched_phrases": matched_phrases,
            "explanation": explanation
        }

# Global singleton scanner
urgency_scanner = UrgencyKeywordScanner()
