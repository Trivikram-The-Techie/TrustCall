"""
Adversarial Perturbation Guard & Spectral Dithering Sanitizer.
Detects and neutralizes imperceptible adversarial perturbations (FGSM/PGD)
and artificial high-frequency dithering used by attackers to mask synthetic vocoder comb ripples.
"""

import numpy as np
from typing import Dict, Any, Tuple

class AdversarialPerturbationGuard:
    """
    Sanitizes audio waveforms against adversarial noise and assesses dither anomaly index.
    """
    def __init__(self, sample_rate: int = 16000):
        self.sr = sample_rate

    def detect_synthetic_dithering(self, audio: np.ndarray) -> Dict[str, Any]:
        """
        Analyzes the high-frequency residual floor (>7 kHz) for unnatural uniform or Gaussian dithering.
        Attackers inject high-frequency white noise to artificially destroy vocoder comb ripples.
        """
        if len(audio) < 512:
            return {"dither_detected": False, "anomaly_score": 0.0, "sanitized_audio": audio}

        # Calculate high-frequency residual via first-order backward difference (high-pass)
        diff = np.diff(audio)
        kurtosis = self._compute_kurtosis(diff)
        variance = float(np.var(diff))

        # Pure synthetic white dither typically exhibits kurtosis near 3.0 and invariant variance
        is_suspicious_dither = (2.7 <= kurtosis <= 3.3) and (variance > 0.005)
        anomaly_score = float(np.clip(1.0 - abs(kurtosis - 3.0) / 1.5, 0.0, 1.0)) if is_suspicious_dither else 0.10

        return {
            "dither_detected": is_suspicious_dither,
            "dither_kurtosis": round(kurtosis, 3),
            "residual_variance": round(variance, 5),
            "anomaly_score": round(anomaly_score, 3)
        }

    def sanitize_waveform(self, audio: np.ndarray) -> np.ndarray:
        """
        Applies 3-point running median filter to strip high-frequency adversarial spikes
        without altering natural vocal tract formants or fundamental frequency (F0).
        """
        if len(audio) < 3:
            return audio

        # 3-point median filter implementation
        sanitized = np.copy(audio)
        sanitized[1:-1] = np.median([audio[:-2], audio[1:-1], audio[2:]], axis=0)
        return sanitized.astype(np.float32)

    def _compute_kurtosis(self, x: np.ndarray) -> float:
        """Computes sample kurtosis (Fisher-Pearson coefficient)."""
        n = len(x)
        if n < 4:
            return 3.0
        mean = np.mean(x)
        std = np.std(x) + 1e-9
        z = (x - mean) / std
        return float(np.mean(z ** 4))

adversarial_guard = AdversarialPerturbationGuard()
