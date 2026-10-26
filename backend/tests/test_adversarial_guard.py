"""
Tests for Adversarial Perturbation Guard & Dithering Sanitizer.
"""

import numpy as np
from app.models.adversarial_guard import adversarial_guard

def test_waveform_sanitization():
    # Signal with single-sample spike (adversarial impulsive noise)
    audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000)).astype(np.float32)
    audio[100] = 5.0  # Adversarial spike
    
    sanitized = adversarial_guard.sanitize_waveform(audio)
    assert len(sanitized) == len(audio)
    assert abs(sanitized[100]) < 1.5  # Spike stripped

def test_synthetic_dithering_detection():
    # Injected uniform white noise
    noise = np.random.normal(0, 0.1, 16000).astype(np.float32)
    res = adversarial_guard.detect_synthetic_dithering(noise)
    assert "dither_detected" in res
    assert "dither_kurtosis" in res
    assert res["residual_variance"] > 0
