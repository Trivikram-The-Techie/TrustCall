"""
Tests for Telephony Codec Normalizer.
"""

import numpy as np
from app.audio.codec_normalizer import codec_normalizer

def test_dc_bias_removal():
    signal = np.ones(1000) * 0.5 + np.random.normal(0, 0.05, 1000)
    cleaned = codec_normalizer.strip_dc_bias(signal)
    assert abs(np.mean(cleaned)) < 1e-4

def test_telecom_bandpass_compensation():
    signal = np.random.normal(0, 0.2, 16000).astype(np.float32)
    normalized = codec_normalizer.apply_telecom_bandpass_compensation(signal)
    assert len(normalized) == len(signal)
    assert not np.isnan(normalized).any()
    assert abs(np.mean(normalized)) < 0.05
