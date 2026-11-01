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
            r"\b(credit\s+card\s+limit|card\s+blocked|atm\s+card)\b",
            # Regional Indian Languages (Telugu, Tamil, Marathi, Bengali)
            r"\b(dabbu\s+pampandi|account\s+block\s+aindi|dabbu\s+ivvandi)\b",
            r"\b(panam\s+anupunga|account\s+block\s+aagirukku|panam\s+kudunga)\b",
            r"\b(paise\s+pathva|khata\s+bandh\s+zala|paise\s+dya)\b",
            r"\b(taka\s+pathan|account\s+block\s+hoyeche|taka\s+din)\b"
        ]
    },
    "otp_credential_theft": {
        "weight": 1.0,
        "patterns": [
            r"\b(otp|one\s*time\s*password)\b",
            r"\b(otp\s+(share\s+karo|batao|bhejo|enter\s+karo|padho))\b",
            r"\b(share\s+(the\s+)?otp|tell\s+me\s+the\s+code|6\s*digit\s*code)\b",
            r"\b(cvv\s*number|card\s*expiry)\b",
            # Regional Dialect OTP extraction
            r"\b(otp\s+(cheppandi|ivvandi))\b",   # Telugu
            r"\b(otp\s+(sollunga|kudunga))\b",   # Tamil
            r"\b(otp\s+(dya|saanga))\b",         # Marathi
            r"\b(otp\s+(din|bolun))\b"           # Bengali
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
            r"\b(jail\s+(jana\s+padega|bheja\s+jayega))\b",
            # Regional Legal Coercion
            r"\b(police\s+case\s+aindi|arrest\s+chestham|jail\s+ki\s+veltharu)\b",       # Telugu
            r"\b(kaval\s+thurai|police\s+case\s+aagirukku|arrest\s+pannuvom)\b",        # Tamil
            r"\b(police\s+karwai|tatkal\s+dakhla|jail\s+madhe\s+jaava\s+lagel)\b",      # Marathi
            r"\b(police\s+case\s+hoyeche|arrest\s+korbo|jail\s+hobe)\b"                 # Bengali
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


# --------------------------------------------------------------------------- #
#  Phase 5: Layered Intent Scanner (keyword + intent classifier fusion)
# --------------------------------------------------------------------------- #

class LayeredIntentScanner:
    """
    Wraps UrgencyKeywordScanner with the local intent classifier.
    Returns the merged result including evidence phrase positions.
    Backward-compatible: still exposes urgency_score, matched_phrases, etc.
    """

    def __init__(self):
        self._keyword_scanner = UrgencyKeywordScanner()
        self._classifier_enabled = True
        self._intent_classifier = None  # lazy import to avoid circular deps

    def _get_classifier(self):
        if self._intent_classifier is None:
            try:
                from app.nlp.intent_classifier import intent_classifier
                self._intent_classifier = intent_classifier
            except Exception:
                self._classifier_enabled = False
        return self._intent_classifier

    def scan_text(self, text: str) -> Dict[str, Any]:
        """
        Combines keyword scan + intent classification.
        Result is a superset of UrgencyKeywordScanner.scan_text().
        """
        kw_result = self._keyword_scanner.scan_text(text)

        clf_result = {"intent_class": "BENIGN", "confidence": 0.0, "evidence_phrases": [], "all_scores": {}}
        classifier = self._get_classifier()
        if classifier and self._classifier_enabled:
            try:
                clf_result = classifier.classify(text)
            except Exception:
                pass

        # Merge: urgency_score is max of keyword hit and classifier signal
        kw_score = kw_result["urgency_score"]
        intent = clf_result["intent_class"]

        # Boost urgency when classifier fires a scam intent
        intent_boost = 0.0
        if intent != "BENIGN":
            conf = clf_result["confidence"]
            intent_boost = min(0.35, conf * 0.40)  # max +0.35 boost

        merged_score = round(min(1.0, kw_score + intent_boost), 3)

        return {
            # core backward-compat keys
            "urgency_score": merged_score,
            "detected": merged_score > 0.05 or kw_result["detected"],
            "categories": kw_result["categories"],
            "matched_phrases": kw_result["matched_phrases"],
            "explanation": kw_result["explanation"],
            # Phase 5 extras
            "intent_class": intent,
            "intent_confidence": round(clf_result["confidence"], 4),
            "evidence_phrases": clf_result["evidence_phrases"],
            "all_intent_scores": clf_result.get("all_scores", {}),
        }


# Global layered scanner singleton (use this in routes / risk engine for Phase 5)
layered_scanner = LayeredIntentScanner()
