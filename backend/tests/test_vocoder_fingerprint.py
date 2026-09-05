"""
Unit tests for Neural Vocoder Architecture Fingerprinting engine.
"""

import numpy as np
import pytest
from app.models.vocoder_fingerprint import vocoder_fingerprinter

def test_genuine_human_fingerprint_classification():
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    # Organic pitch frequency modulation (vibrato / inflection)
    f0 = 140.0 + 35.0 * np.sin(2 * np.pi * 4.0 * t)
    phase = 2 * np.pi * np.cumsum(f0) / sr
    audio = 0.5 * np.sin(phase) + 0.05 * np.random.randn(len(t))

    acoustic_features = {
        "pitch": {"pitch_std_hz": 35.0, "contour_flatness_score": 0.12},
        "perturbation": {"jitter_percent": 1.4, "shimmer_percent": 3.2},
        "spectral": {"spectral_flux_mean": 0.04}
    }

    result = vocoder_fingerprinter.analyze_audio_fingerprint(
        audio=audio,
        acoustic_features=acoustic_features,
        spoof_probability=0.12
    )

    assert result["primary_architecture"] == "Organic Human Biomechanics"
    assert result["architecture_scores"]["Organic Human Biomechanics"] > 0.6
    assert "comb_ripple_index" in result
    assert "phase_continuity_index" in result

def test_diffusion_voice_clone_classification():
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    # Flat pitch and zero jitter (characteristic of flow-matching/diffusion)
    f0 = 160.0
    phase = 2 * np.pi * f0 * t
    audio = 0.5 * np.sin(phase)

    acoustic_features = {
        "pitch": {"pitch_std_hz": 4.5, "contour_flatness_score": 0.88},
        "perturbation": {"jitter_percent": 0.15, "shimmer_percent": 1.0},
        "spectral": {"spectral_flux_mean": 0.02}
    }

    result = vocoder_fingerprinter.analyze_audio_fingerprint(
        audio=audio,
        acoustic_features=acoustic_features,
        spoof_probability=0.85
    )

    assert "Diffusion" in result["primary_architecture"]
    assert result["architecture_scores"]["Diffusion / Flow-Matching (ElevenLabs/XTTS)"] > 0.4
    assert result["confidence"] > 0.35

def test_neural_vocoder_hifi_gan_classification():
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    # High frequency comb buzz (6.5 kHz - 7.5 kHz)
    audio = 0.4 * np.sin(2 * np.pi * 200.0 * t) + 0.35 * np.sin(2 * np.pi * 7100.0 * t)

    acoustic_features = {
        "pitch": {"pitch_std_hz": 18.0, "contour_flatness_score": 0.4},
        "perturbation": {"jitter_percent": 3.8, "shimmer_percent": 7.5},
        "spectral": {"spectral_flux_mean": 0.08}
    }

    result = vocoder_fingerprinter.analyze_audio_fingerprint(
        audio=audio,
        acoustic_features=acoustic_features,
        spoof_probability=0.78
    )

    assert result["primary_architecture"] in ["Neural Vocoder (HiFi-GAN/BigVGAN)", "Autoregressive Codec (Bark/AudioLM)"]
    assert "comb_ripple_index" in result
