"""
Layered Intent Classifier for TrustCall / VoiceShield — Phase 5.
Runs 100% locally with zero paid API keys.
Approach: TF-IDF-style cosine similarity against hand-crafted scam-intent phrase templates
covering English, Hindi, Telugu, and Tamil.

Returns:
  intent_class   — top predicted scam intent category
  confidence     — 0.0–1.0 similarity score
  evidence_phrases — list of {text, start, end, language} spans matched in the input
"""

import math
import re
from typing import Any, Dict, List, Tuple

from app.config import settings

# --------------------------------------------------------------------------- #
#  Scam intent templates (multilingual)
# --------------------------------------------------------------------------- #

# Each template is a list of representative phrases per intent.
# We compute TF-IDF vectors offline from these at startup.

INTENT_TEMPLATES: Dict[str, List[str]] = {
    "DIGITAL_ARREST": [
        # English
        "digital arrest you are under digital arrest cbi officer ed enforcement directorate",
        "crime branch investigation skype video call interrogation do not move",
        "narcotics parcel seized customs department illegal package your name",
        "non bailable warrant arrest warrant court order issued against you",
        "you are in legal trouble police will come if you disconnect",
        # Hindi
        "digital giraftari aapko digital arrest kiya ja raha hai cbi adhikari",
        "crime branch jaanch skype video call mat kaato police aayegi",
        "aapka parcel pakda gaya nashe ka maal aapka naam warrant nikla hai",
        "jail bheja jayega agar aapne phone kata to arrest ho jayenge",
        # Telugu
        "digital arrest meeru digital arrest lo unnaru cbi officer crime branch",
        "mee parcel police pakadindi warrant vachindi jadam potharu",
        "video call lo anukuntaru court order vachindi district court",
        # Tamil
        "digital arrest ungalukku digital arrest cbi officer enforcement directorate",
        "parcel polisal pudichiruku warrant vanthuchu court order vanthuchu",
        "video call la irunga arrest pannuvom crime branch",
    ],
    "BANKING_FRAUD": [
        # English
        "bank account blocked suspended kyc update otp enter share pin",
        "transfer money immediately send funds wire transfer bank account frozen",
        "upi pin enter scan qr code credit card blocked atm card deactivated",
        "sbi hdfc icici rbi reserve bank india kyc pending account deactivated",
        "your account will be permanently closed if you do not update kyc",
        # Hindi
        "bank khata block ho gaya kyc update karo otp batao pin share karo",
        "paisa transfer karo abhi nahi to account band ho jayega rbi notice",
        "atm card band ho gaya upi pin dalwao qr code scan karo",
        "khata suspend ho gaya kyc expire ho gaya turant update karo",
        # Telugu
        "bank account block aindi kyc update cheyandi otp cheppandi",
        "dabbu pampandi account suspend aindi upi pin ivvandi",
        "account permanent close aipothundi kyc expire aindi",
        # Tamil
        "bank account block aagiruku kyc update pannutha otp sollunga",
        "panam anupunga account suspend aagiruku upi pin kudunga",
        "account close aagum kyc expire aagiruku",
    ],
    "FAMILY_EMERGENCY": [
        # English
        "your son daughter husband wife is in custody accident hospital icu",
        "emergency bail money needed operation fees send money immediately",
        "your child arrested need money to release them hospital critical",
        "family member accident surgery urgent funds required now",
        # Hindi
        "aapka beta arrest hai paisa chahiye chhudane ke liye",
        "aapka bachha accident mein hai hospital mein operation ke liye paisa bhejo",
        "ghar wala pakda gaya paisa chahiye abhi bhejo warna jail jayega",
        "medical emergency operation ke liye turant paise chahiye",
        # Telugu
        "mee abbayi arrest ayyadu money kavali release ki",
        "mee pillalu accident lo unnaru hospital ki money pampandi",
        # Tamil
        "ungal pillai kadiyil irukaru panam teva release ku",
        "ungal family accident hospital la irukaru panam anupunga",
    ],
    "PARCEL_SCAM": [
        # English
        "parcel seized narcotics drugs passport illegal items your name address",
        "customs department package detained aadhaar linked dangerous goods",
        "delivery stopped illegal shipment your mobile linked parcel drugs found",
        # Hindi
        "aapka courier pakda gaya usme drugs mila hai aapka aadhaar se link hai",
        "customs ne parcel roka hai illegal saaman aapke naam ka",
        "delivery band kar di gayi drugs mila parcel mein",
        # Telugu
        "mee parcel drugs dorikayi customs officer aapadi",
        # Tamil
        "parcel police pudichiruku drugs irruku ungal name address link",
    ],
    "BENIGN": [
        "hello how are you good morning good evening nice to meet you",
        "what is the weather today can you help me with directions",
        "thank you for calling have a nice day bye goodbye",
        "I would like to schedule an appointment please",
        "namaskar kaise hain aap aaj ka mausam kaisa hai dhanyavad",
    ],
}

# --------------------------------------------------------------------------- #
#  Evidence phrase patterns per intent (for highlighting)
# --------------------------------------------------------------------------- #

EVIDENCE_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
    "DIGITAL_ARREST": [
        (r"\b(digital\s+arrest|digital\s+giraftari|arrest\s+warrant|non.bailable\s+warrant)\b", "en"),
        (r"\b(cbi|ed|enforcement\s+directorate|crime\s+branch)\b", "en"),
        (r"\b(skype\s+(call|investigation)|video\s+call\s+arrest)\b", "en"),
        (r"\b(digital\s+giraftari|jail\s+bheja|warrant\s+nikla|giraftari)\b", "hi"),
        (r"\b(digital\s+arrest\s+lo|warrant\s+vachindi|jadam\s+potharu)\b", "te"),
        (r"\b(digital\s+arrest\s+pannuvom|warrant\s+vanthuchu)\b", "ta"),
    ],
    "BANKING_FRAUD": [
        (r"\b(bank\s+account\s+(blocked|suspended|frozen|deactivated))\b", "en"),
        (r"\b(otp|upi\s+pin|kyc\s+(update|expired)|qr\s+code)\b", "en"),
        (r"\b(transfer\s+money|send\s+funds|wire\s+transfer)\b", "en"),
        (r"\b(khata\s+block|otp\s+batao|upi\s+pin\s+dalwao|paisa\s+transfer)\b", "hi"),
        (r"\b(account\s+block\s+aindi|otp\s+cheppandi|dabbu\s+pampandi)\b", "te"),
        (r"\b(account\s+block\s+aagiruku|otp\s+sollunga|panam\s+anupunga)\b", "ta"),
    ],
    "FAMILY_EMERGENCY": [
        (r"\b(your\s+(son|daughter|husband|wife)\s+is\s+in)\b", "en"),
        (r"\b(hospital|icu|operation|bail|custody|arrested)\b", "en"),
        (r"\b(beta\s+arrest|paisa\s+chahiye|bachha\s+accident)\b", "hi"),
        (r"\b(abbayi\s+arrest|pillalu\s+accident)\b", "te"),
    ],
    "PARCEL_SCAM": [
        (r"\b(parcel\s+(seized|detained)|narcotics|illegal\s+(items|shipment))\b", "en"),
        (r"\b(customs\s+department|customs\s+officer)\b", "en"),
        (r"\b(courier\s+pakda|parcel\s+mein\s+drugs|aapka\s+courier)\b", "hi"),
        (r"\b(parcel\s+drugs|customs\s+officer\s+aapadi)\b", "te"),
    ],
}

# --------------------------------------------------------------------------- #
#  TF-IDF vectoriser (zero-dependency, pure Python)
# --------------------------------------------------------------------------- #

def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z\u0900-\u097f\u0c00-\u0c7f\u0b80-\u0bff]+", text.lower())


def _build_vocab_and_idf(corpus: List[str]) -> Tuple[Dict[str, int], List[float]]:
    vocab: Dict[str, int] = {}
    doc_freq: Dict[str, int] = {}
    tokenized = []
    for doc in corpus:
        tokens = set(_tokenize(doc))
        tokenized.append(tokens)
        for tok in tokens:
            if tok not in vocab:
                vocab[tok] = len(vocab)
            doc_freq[tok] = doc_freq.get(tok, 0) + 1

    N = len(corpus)
    idf = [0.0] * len(vocab)
    for term, idx in vocab.items():
        idf[idx] = math.log((N + 1) / (doc_freq[term] + 1)) + 1.0  # smoothed

    return vocab, idf


def _vectorise(tokens: List[str], vocab: Dict[str, int], idf: List[float]) -> List[float]:
    tf: Dict[int, int] = {}
    for tok in tokens:
        idx = vocab.get(tok)
        if idx is not None:
            tf[idx] = tf.get(idx, 0) + 1
    n = len(tokens) or 1
    vec = [0.0] * len(vocab)
    for idx, count in tf.items():
        vec[idx] = (count / n) * idf[idx]
    return vec


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# --------------------------------------------------------------------------- #
#  Build model at import time (fast — pure dict ops)
# --------------------------------------------------------------------------- #

_ALL_DOCS = [phrase for phrases in INTENT_TEMPLATES.values() for phrase in phrases]
_VOCAB, _IDF = _build_vocab_and_idf(_ALL_DOCS)

# Pre-compute centroid vector per intent class
_CLASS_VECTORS: Dict[str, List[float]] = {}
for _intent, _phrases in INTENT_TEMPLATES.items():
    _vecs = [_vectorise(_tokenize(p), _VOCAB, _IDF) for p in _phrases]
    n_vecs = len(_vecs)
    centroid = [sum(v[i] for v in _vecs) / n_vecs for i in range(len(_VOCAB))]
    _CLASS_VECTORS[_intent] = centroid


# --------------------------------------------------------------------------- #
#  Public classifier
# --------------------------------------------------------------------------- #

class IntentClassifier:
    """
    Local-only multilingual scam intent classifier.
    Uses TF-IDF cosine similarity against intent centroids.
    No paid API, no model download.
    """

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify input text into a scam intent category.

        Returns:
          intent_class    — predicted intent label
          confidence      — 0.0–1.0
          evidence_phrases — [{text, start, end, language}]
          all_scores      — per-class similarity scores
        """
        if not text or not text.strip():
            return self._null_result()

        tokens = _tokenize(text)
        query_vec = _vectorise(tokens, _VOCAB, _IDF)

        scores: Dict[str, float] = {}
        for intent, centroid in _CLASS_VECTORS.items():
            scores[intent] = round(_cosine(query_vec, centroid), 4)

        best_intent = max(scores, key=lambda k: scores[k])
        confidence = scores[best_intent]

        if confidence < settings.INTENT_CLASSIFIER_THRESHOLD:
            best_intent = "BENIGN"

        evidence = self._extract_evidence(text, best_intent)

        return {
            "intent_class": best_intent,
            "confidence": round(confidence, 4),
            "evidence_phrases": evidence,
            "all_scores": scores,
        }

    def _null_result(self) -> Dict[str, Any]:
        return {
            "intent_class": "BENIGN",
            "confidence": 0.0,
            "evidence_phrases": [],
            "all_scores": {},
        }

    def _extract_evidence(self, text: str, intent: str) -> List[Dict[str, Any]]:
        """Find regex evidence spans for the classified intent."""
        patterns = EVIDENCE_PATTERNS.get(intent, [])
        results: List[Dict[str, Any]] = []
        seen_spans = set()

        for pattern, lang in patterns:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                span = (m.start(), m.end())
                if span not in seen_spans:
                    seen_spans.add(span)
                    results.append({
                        "text": m.group(),
                        "start": m.start(),
                        "end": m.end(),
                        "language": lang,
                    })

        return sorted(results, key=lambda x: x["start"])


# Global singleton
intent_classifier = IntentClassifier()
