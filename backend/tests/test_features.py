"""
Tests for acoustic and prosodic feature extraction.
"""

import os
import wave
import numpy as np
import pytest
from app.audio.feature_extraction import (
    decode_audio_bytes,
    compute_log_mel_spectrogram,
    extract_pitch_and_contour,
    extract_jitter_and_shimmer,
    extract_spectral_flatness,
    extract_acoustic_features
)

@pytest.fixture
def sample_wavs():
    base_dir = os.path.join(os.path.dirname(__file__), "..", "demo_audio")
    genuine_path = os.path.join(base_dir, "genuine_call_sample.wav")
    cloned_path = os.path.join(base_dir, "cloned_scam_sample.wav")
    
    with open(genuine_path, "rb") as f:
        gen_bytes = f.read()
    with open(cloned_path, "rb") as f:
        clone_bytes = f.read()
        
    return {
        "genuine": decode_audio_bytes(gen_bytes, target_sr=16000),
        "cloned": decode_audio_bytes(clone_bytes, target_sr=16000)
    }

def test_log_mel_spectrogram_shape(sample_wavs):
    audio = sample_wavs["genuine"][:16000]  # 1 second
    mel = compute_log_mel_spectrogram(audio, sr=16000, n_mels=80)
    assert mel.shape[0] == 80
    assert mel.shape[1] > 0
    assert not np.isnan(mel).any()

def test_pitch_contour_distinction(sample_wavs):
    gen_pitch = extract_pitch_and_contour(sample_wavs["genuine"], sr=16000)
    clone_pitch = extract_pitch_and_contour(sample_wavs["cloned"], sr=16000)
    
    # Natural speech should have higher standard deviation in F0 than synthetic speech
    assert gen_pitch["pitch_std_hz"] > clone_pitch["pitch_std_hz"]
    # Cloned speech should have higher flatness score
    assert clone_pitch["contour_flatness_score"] >= gen_pitch["contour_flatness_score"]

def test_jitter_and_shimmer_extraction(sample_wavs):
    gen_perturb = extract_jitter_and_shimmer(sample_wavs["genuine"], sr=16000)
    assert "jitter_percent" in gen_perturb
    assert "shimmer_percent" in gen_perturb
    assert gen_perturb["jitter_percent"] > 0

def test_spectral_flatness(sample_wavs):
    flatness_gen = extract_spectral_flatness(sample_wavs["genuine"])
    flatness_clone = extract_spectral_flatness(sample_wavs["cloned"])
    assert 0.0 <= flatness_gen <= 1.0
    assert 0.0 <= flatness_clone <= 1.0

def test_full_acoustic_features_composite(sample_wavs):
    features = extract_acoustic_features(sample_wavs["cloned"], sr=16000)
    assert "energy_rms" in features
    assert "pitch" in features
    assert "perturbation" in features
    assert "prosodic_spoof_score" in features
    assert 0.0 <= features["prosodic_spoof_score"] <= 1.0
