"""
Number Reputation Engine for TrustCall / VoiceShield — Phase 5.
Provides:
  - Blocklist lookup (local JSON file; SIMULATED DEMO data only)
  - VoIP prefix detection
  - Call-burst / velocity tracking (in-memory, TTL-based)
  - Short repeated call detection

All blocklist data is synthetic / SIMULATED DEMO — not a real threat intelligence source.
"""

import json
import os
import re
import time
from collections import defaultdict
from typing import Any, Dict, Optional

from app.config import settings

# --------------------------------------------------------------------------- #
#  Blocklist loader
# --------------------------------------------------------------------------- #

_BLOCKLIST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "blocklist.json"
)


def _load_blocklist() -> Dict[str, Any]:
    try:
        with open(_BLOCKLIST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"entries": [], "voip_prefixes": []}


_BLOCKLIST_DATA = _load_blocklist()

# Normalise to E.164-style for fast lookup
_BLOCKLIST_INDEX: Dict[str, Dict[str, Any]] = {
    re.sub(r"[\s\-\(\)\+]", "", e["number"]): e
    for e in _BLOCKLIST_DATA.get("entries", [])
}

_VOIP_PREFIXES: list = _BLOCKLIST_DATA.get(
    "voip_prefixes", settings.VOIP_PREFIXES
)


# --------------------------------------------------------------------------- #
#  In-memory velocity tracker
# --------------------------------------------------------------------------- #

class _VelocityTracker:
    """Tracks call timestamps per normalised number within a rolling TTL window."""

    def __init__(self):
        # number → list of (timestamp_epoch, duration_sec)
        self._calls: Dict[str, list] = defaultdict(list)

    def _normalise(self, number: str) -> str:
        return re.sub(r"[\s\-\(\)\+]", "", number)

    def record_call(self, number: str, duration_sec: float = 0.0):
        norm = self._normalise(number)
        now = time.time()
        self._calls[norm].append((now, duration_sec))
        # Prune stale entries beyond window
        window = settings.CALL_BURST_WINDOW_SEC
        self._calls[norm] = [
            (ts, dur)
            for ts, dur in self._calls[norm]
            if now - ts <= window
        ]

    def get_burst_stats(self, number: str) -> Dict[str, Any]:
        norm = self._normalise(number)
        now = time.time()
        window = settings.CALL_BURST_WINDOW_SEC
        recent = [
            (ts, dur)
            for ts, dur in self._calls.get(norm, [])
            if now - ts <= window
        ]
        count = len(recent)
        short_count = sum(
            1 for _, dur in recent if dur < settings.SHORT_CALL_THRESHOLD_SEC
        )
        return {
            "call_count_in_window": count,
            "short_call_count": short_count,
            "window_sec": window,
        }


_velocity_tracker = _VelocityTracker()


# --------------------------------------------------------------------------- #
#  Main engine
# --------------------------------------------------------------------------- #

class NumberReputationEngine:
    """
    Evaluates caller phone numbers against local synthetic blocklist,
    VoIP prefix heuristics, and in-memory call-burst velocity.
    Returns structured risk sub-scores for each signal.

    ⚠ SIMULATED DEMO — blocklist is entirely synthetic.
    """

    # sub-signal weights (sum = 1.0) — read from settings
    @property
    def _w_reputation(self) -> float:
        return settings.META_WEIGHT_NUMBER_REPUTATION

    @property
    def _w_velocity(self) -> float:
        return settings.META_WEIGHT_CALL_BURST_VELOCITY

    @property
    def _w_short_repeat(self) -> float:
        return settings.META_WEIGHT_SHORT_REPEAT_CALLS

    @property
    def _w_voip(self) -> float:
        return settings.META_WEIGHT_VOIP_PREFIX

    def _normalise(self, number: str) -> str:
        return re.sub(r"[\s\-\(\)\+]", "", number)

    # ------------------------------------------------------------------ #

    def check_blocklist(self, number: str) -> Dict[str, Any]:
        """Return blocklist entry or empty dict."""
        norm = self._normalise(number)
        entry = _BLOCKLIST_INDEX.get(norm)
        if entry:
            return {
                "listed": True,
                "category": entry.get("category", "Unknown"),
                "reports": entry.get("reports", 0),
                "score": min(1.0, 0.5 + entry.get("reports", 0) / 100.0),
            }
        return {"listed": False, "score": 0.0}

    def detect_voip_prefix(self, number: str) -> Dict[str, Any]:
        """Detect whether number starts with a known VoIP gateway prefix."""
        norm = self._normalise(number)
        for pfx in _VOIP_PREFIXES:
            if norm.startswith(pfx):
                return {"is_voip": True, "matched_prefix": pfx, "score": 0.6}
        return {"is_voip": False, "score": 0.0}

    def record_call(self, number: str, duration_sec: float = 0.0):
        """Persist a call event for velocity tracking."""
        _velocity_tracker.record_call(number, duration_sec)

    def get_velocity_score(self, number: str) -> Dict[str, Any]:
        """Compute burst-velocity and short-repeat sub-scores."""
        stats = _velocity_tracker.get_burst_stats(number)
        burst_count = stats["call_count_in_window"]
        short_count = stats["short_call_count"]

        # Burst: sigmoid-style ramp above threshold
        threshold = settings.CALL_BURST_THRESHOLD
        burst_score = 0.0
        if burst_count >= threshold:
            excess = burst_count - threshold
            burst_score = min(1.0, 0.5 + excess * 0.15)

        # Short-repeat: >1 short call is suspicious
        short_score = min(1.0, short_count * 0.35)

        return {
            "burst_score": round(burst_score, 3),
            "short_repeat_score": round(short_score, 3),
            "call_count_in_window": burst_count,
            "short_call_count": short_count,
        }

    # ------------------------------------------------------------------ #

    def evaluate(
        self,
        number: str,
        extra_caller_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Full metadata reputation evaluation for a caller number.
        Returns a dict with aggregated score + per-signal breakdown
        compatible with risk_engine.py caller_metadata field.
        """
        blocklist = self.check_blocklist(number)
        voip = self.detect_voip_prefix(number)
        velocity = self.get_velocity_score(number)

        # Weighted aggregate (sub-weights from settings)
        rep_score = blocklist["score"] * self._w_reputation
        vel_score = velocity["burst_score"] * self._w_velocity
        short_score = velocity["short_repeat_score"] * self._w_short_repeat
        voip_score = voip["score"] * self._w_voip

        aggregate = min(1.0, rep_score + vel_score + short_score + voip_score)

        # Pass through legacy flags for existing risk_engine compatibility
        meta = {
            # Legacy keys (risk_engine.py already reads these)
            "is_unknown_number": not blocklist["listed"] and not voip["is_voip"],
            "is_voip_spoofed": voip["is_voip"],
            "country_mismatch": False,  # placeholder for future SIM-swap check
            # New Phase-5 sub-signal breakdown
            "number_reputation": {
                "listed": blocklist["listed"],
                "score": round(blocklist["score"], 3),
                "category": blocklist.get("category", ""),
                "reports": blocklist.get("reports", 0),
                "contribution": round(rep_score * 100, 1),
            },
            "call_burst_velocity": {
                "score": round(velocity["burst_score"], 3),
                "call_count_in_window": velocity["call_count_in_window"],
                "contribution": round(vel_score * 100, 1),
            },
            "short_repeat_calls": {
                "score": round(velocity["short_repeat_score"], 3),
                "short_call_count": velocity["short_call_count"],
                "contribution": round(short_score * 100, 1),
            },
            "voip_prefix": {
                "is_voip": voip["is_voip"],
                "matched_prefix": voip.get("matched_prefix", ""),
                "score": round(voip["score"], 3),
                "contribution": round(voip_score * 100, 1),
            },
            "meta_aggregate_score": round(aggregate, 3),
        }

        if extra_caller_meta:
            meta.update(extra_caller_meta)

        return meta


# Global singleton
number_reputation_engine = NumberReputationEngine()
