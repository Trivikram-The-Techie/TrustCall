"""
Burst-Robust Temporal Aggregator for Anti-Spoofing.
Combines Rolling Median with CUSUM (Cumulative Sum) Change-Point Detection
and Max-Window Pooling to prevent evasion via brief synthetic burst injection,
silence splicing, or hybrid human-clone audio interleaving.
"""

from collections import deque
from typing import Dict, Any, List
import numpy as np

class BurstRobustAggregator:
    """
    Online CUSUM and Max-Window aggregator for streaming anti-spoofing probabilities.
    Standard median filters fail against hybrid attacks (e.g., 50% genuine speech / 50% cloned speech)
    because the median washes out the synthetic signal.
    This aggregator tracks:
    1. Rolling Median: nominal baseline for steady continuous speech.
    2. Max-Window: retains peak synthetic confidence in a sliding window.
    3. CUSUM Accumulator: accumulates positive log-likelihood shifts above nominal human baseline.
    """
    def __init__(
        self,
        window_size: int = 5,
        nominal_human_mean: float = 0.20,
        allowance_k: float = 0.15,
        decision_threshold_h: float = 0.45
    ):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)
        self.nominal_mean = nominal_human_mean
        self.allowance_k = allowance_k
        self.threshold_h = decision_threshold_h
        self.cusum_stat = 0.0

    def update(self, chunk_prob: float) -> Dict[str, Any]:
        """
        Updates the aggregator with a new chunk's raw spoof probability [0.0 - 1.0].
        Returns aggregated probabilities and burst detection status.
        """
        prob = float(np.clip(chunk_prob, 0.0, 1.0))
        self.history.append(prob)

        # 1. Rolling Median
        median_prob = float(np.median(list(self.history)))

        # 2. Max-Window Pooling
        max_window_prob = float(np.max(list(self.history)))

        # 3. CUSUM Change-Point Statistic
        # S_t = max(0, S_{t-1} + (prob - (nominal_mean + allowance_k)))
        shift = prob - (self.nominal_mean + self.allowance_k)
        if shift > 0:
            self.cusum_stat = float(self.cusum_stat + shift)
        else:
            # Gradual leak for negative shifts (half-step dissipation)
            self.cusum_stat = float(max(0.0, self.cusum_stat + shift * 0.4))

        burst_alarm = bool(self.cusum_stat >= self.threshold_h or max_window_prob >= 0.75)

        # 4. Fused Mitigated Probability:
        # If a burst is detected, prioritize max-window and CUSUM over the diluted median.
        if burst_alarm:
            cusum_scaled = min(1.0, 0.50 + (self.cusum_stat / (self.threshold_h * 2.0)) * 0.50)
            mitigated_prob = float(max(median_prob, max_window_prob * 0.90, cusum_scaled))
        else:
            mitigated_prob = median_prob

        return {
            "raw_probability": round(prob, 4),
            "median_probability": round(median_prob, 4),
            "max_window_probability": round(max_window_prob, 4),
            "cusum_statistic": round(self.cusum_stat, 4),
            "burst_detected": burst_alarm,
            "mitigated_probability": round(float(np.clip(mitigated_prob, 0.0, 1.0)), 4)
        }

    def reset(self):
        """Resets the history and CUSUM accumulator."""
        self.history.clear()
        self.cusum_stat = 0.0

burst_aggregator = BurstRobustAggregator()
