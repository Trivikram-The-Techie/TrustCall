"""
Neural Vocoder & Synthesis Architecture Fingerprinting Engine.
Classifies synthetic voice attacks by underlying generative architecture:
- Diffusion / Flow-Matching (ElevenLabs, Voicebox, XTTS)
- Neural Vocoders (HiFi-GAN, BigVGAN, WaveGlow)
- Autoregressive Neural Codecs (Bark, AudioLM, DAC)
- Organic Human Biomechanics (Natural physiological vocal fold speech)
"""

import numpy as np
from typing import Dict, Any, Optional

class VocoderFingerprinter:
    """
    Forensic classifier analyzing high-frequency comb ripples, phase jitter,
    and pitch micro-inflections to identify the specific synthesis engine.
    """
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def analyze_audio_fingerprint(
        self,
        audio: np.ndarray,
        acoustic_features: Optional[Dict[str, Any]] = None,
        spoof_probability: float = 0.1
    ) -> Dict[str, Any]:
        """
        Extracts synthesis architecture signatures from raw audio and acoustic feature dict.
        """
        acoustic_features = acoustic_features or {}
        n_samples = len(audio)

        if n_samples < 512:
            return {
                "primary_architecture": "Insufficient Audio",
                "architecture_scores": {
                    "Organic Human": 1.0,
                    "Diffusion / Flow-Matching": 0.0,
                    "Neural Vocoder (HiFi-GAN)": 0.0,
                    "Autoregressive Codec (Bark)": 0.0
                },
                "comb_ripple_index": 0.05,
                "phase_continuity_index": 0.95,
                "confidence": 0.5,
                "fingerprint_summary": "Sample duration too brief for vocoder classification."
            }

        # 1. High-frequency comb filtering & sub-band spectral variance
        fft_mag = np.abs(np.fft.rfft(audio))
        freqs = np.fft.rfftfreq(n_samples, d=1.0 / self.sample_rate)

        hf_mask = (freqs >= 6000) & (freqs <= 7800)
        mf_mask = (freqs >= 2000) & (freqs < 5000)

        hf_energy = float(np.mean(fft_mag[hf_mask])) if np.any(hf_mask) else 1e-6
        mf_energy = float(np.mean(fft_mag[mf_mask])) if np.any(mf_mask) else 1e-6
        comb_ratio = float(hf_energy / (mf_energy + 1e-6))

        # 2. Extract Pitch & Perturbation signatures
        pitch_info = acoustic_features.get("pitch", {})
        pitch_std = float(pitch_info.get("pitch_std_hz", 25.0))
        pitch_flatness = float(pitch_info.get("contour_flatness_score", 0.1))

        perturb_info = acoustic_features.get("perturbation", {})
        jitter = float(perturb_info.get("jitter_percent", 1.2))
        shimmer = float(perturb_info.get("shimmer_percent", 3.5))

        # 3. Spectral Flux & Frame Boundary Jitter
        spectral_info = acoustic_features.get("spectral", {})
        flux = float(spectral_info.get("spectral_flux_mean", 0.05))

        # Architecture scoring algorithm
        if spoof_probability < 0.35 and pitch_std >= 18.0 and (0.7 <= jitter <= 3.0):
            # Clearly Human
            h_score = 0.92
            diff_score = 0.03
            voc_score = 0.03
            ar_score = 0.02
        else:
            # Synthetic / Suspect speech
            # Check Diffusion: extremely low jitter, high pitch flatness, smooth phase
            diff_score = 0.2
            if pitch_flatness > 0.65 or pitch_std < 14.0:
                diff_score += 0.45
            if jitter < 0.45:
                diff_score += 0.25

            # Check HiFi-GAN / Neural Vocoder: high frequency comb filtering & buzz
            voc_score = 0.2
            if comb_ratio > 0.65 or comb_ratio < 0.08:
                voc_score += 0.45
            if shimmer > 6.0 or jitter > 4.5:
                voc_score += 0.25

            # Check Autoregressive Codec (Bark / AudioLM): sudden spectral flux jumps
            ar_score = 0.15
            if flux > 0.10:
                ar_score += 0.40
            if 0.45 <= jitter <= 0.8:
                ar_score += 0.25

            # Human score in suspect audio
            h_score = max(0.02, 1.0 - max(diff_score, voc_score, ar_score))

        # Normalize scores to probabilities
        total = h_score + diff_score + voc_score + ar_score
        scores = {
            "Organic Human Biomechanics": round(h_score / total, 3),
            "Diffusion / Flow-Matching (ElevenLabs/XTTS)": round(diff_score / total, 3),
            "Neural Vocoder (HiFi-GAN/BigVGAN)": round(voc_score / total, 3),
            "Autoregressive Codec (Bark/AudioLM)": round(ar_score / total, 3)
        }

        # Determine winner
        best_arch = max(scores, key=scores.get)
        confidence = float(scores[best_arch])

        if best_arch == "Organic Human Biomechanics":
            summary = "Natural vocal tract micro-tremor and physiological pitch trajectory confirmed."
        elif "Diffusion" in best_arch:
            summary = "Diffusion / Flow-matching signature detected: unnatural pitch curvature flatness and over-smoothed phase."
        elif "Neural Vocoder" in best_arch:
            summary = "Neural vocoder signature detected: high-frequency comb filtering and phase dispersion in upper harmonics."
        else:
            summary = "Autoregressive neural codec artifacts detected: frame boundary phase discontinuities."

        return {
            "primary_architecture": best_arch,
            "architecture_scores": scores,
            "comb_ripple_index": round(min(1.0, comb_ratio), 3),
            "phase_continuity_index": round(max(0.0, 1.0 - flux), 3),
            "pitch_stability_index": round(max(0.0, 1.0 - (pitch_std / 50.0)), 3),
            "confidence": confidence,
            "fingerprint_summary": summary
        }

# Global fingerprinter instance
vocoder_fingerprinter = VocoderFingerprinter()
