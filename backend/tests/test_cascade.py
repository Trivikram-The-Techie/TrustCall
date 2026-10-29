"""
Unit tests for Phase 4 Two-Stage Cascade Detector & Telecom Fail-Open Guard.
"""

import numpy as np
import pytest
from app.models.cascade_detector import ScreeningGate, CascadeSpoofDetector
from app.models.spoof_detector import SpoofDetector


def _generate_synthetic_speech_proxy():
    t = np.linspace(0, 1.5, 24000, endpoint=False)
    # Natural human voice proxy: fundamental with natural harmonic decay
    audio = np.zeros(24000, dtype=np.float32)
    for k in range(1, 35):
        freq = 140.0 * k
        if freq < 7500:
            audio += (0.25 / np.sqrt(k)) * np.sin(2 * np.pi * freq * t).astype(np.float32)
    # Add subtle pink noise
    audio += 0.01 * np.random.normal(0, 1, 24000).astype(np.float32)
    return audio / (np.max(np.abs(audio)) + 1e-6)


def test_stage1_screening_gate_bonafide():
    gate = ScreeningGate(threshold=0.35)
    audio = _generate_synthetic_speech_proxy()

    # Warmup
    _ = gate.screen_chunk(audio, sr=16000)

    res = gate.screen_chunk(audio, sr=16000)
    assert "stage1_score" in res
    assert "latency_ms" in res
    assert res["latency_ms"] < 25.0  # Fast DSP screening under 25ms
    assert 0.0 <= res["stage1_score"] <= 1.0


def test_stage1_screening_gate_vocoder_anomaly():
    gate = ScreeningGate(threshold=0.35)
    # Synthetic vocoder artifact: strong comb spikes in high band (6500-7800Hz)
    t = np.linspace(0, 1.5, 24000, endpoint=False)
    carrier = 0.15 * np.sin(2 * np.pi * 200 * t)
    hf_comb = 0.35 * np.sin(2 * np.pi * 7100 * t) + 0.35 * np.sin(2 * np.pi * 7400 * t)
    audio = (carrier + hf_comb).astype(np.float32)

    res = gate.screen_chunk(audio, sr=16000)
    assert res["stage1_score"] > 0.30  # Elevated screening score for vocoder artifact
    assert res["spectral_crest"] > 4.0


def test_cascade_detector_routing():
    heavy = SpoofDetector()
    cascade = CascadeSpoofDetector(heavy_detector=heavy, threshold=0.45, periodic_interval=10)

    # 1. Benign audio chunk
    benign_audio = _generate_synthetic_speech_proxy()
    res1 = cascade.predict_chunk(benign_audio, sr=16000)

    assert "cascade" in res1
    # Check that cascade metadata is present
    assert "stage1_score" in res1["cascade"]
    assert "stage2_triggered" in res1["cascade"]

    # 2. Strong synthetic artifact chunk - should trigger Stage 2 immediately via gate
    t = np.linspace(0, 1.5, 24000, endpoint=False)
    hf_comb = (0.45 * np.sin(2 * np.pi * 7100 * t) + 0.45 * np.sin(2 * np.pi * 7400 * t)).astype(np.float32)
    scam_audio = benign_audio + hf_comb
    res2 = cascade.predict_chunk(scam_audio, sr=16000)

    assert res2["cascade"]["stage2_triggered"]
    assert res2["cascade"]["decision_reason"] == "gate_exceeded_suspicious"
    assert res2["cascade"]["stage2_latency_ms"] > 0.0


def test_cascade_periodic_surveillance():
    heavy = SpoofDetector()
    # Interval = 3: every 3rd chunk triggers stage 2 even if score is low
    cascade = CascadeSpoofDetector(heavy_detector=heavy, threshold=0.95, periodic_interval=3)

    clean = _generate_synthetic_speech_proxy()

    r1 = cascade.predict_chunk(clean, sr=16000)
    assert not r1["cascade"]["stage2_triggered"]

    r2 = cascade.predict_chunk(clean, sr=16000)
    assert not r2["cascade"]["stage2_triggered"]

    r3 = cascade.predict_chunk(clean, sr=16000)
    assert r3["cascade"]["stage2_triggered"]
    assert r3["cascade"]["decision_reason"] == "periodic_surveillance"


def test_cascade_fail_open_guard():
    heavy = SpoofDetector()
    # Very small budget to trigger fail-open simulation
    cascade = CascadeSpoofDetector(heavy_detector=heavy, threshold=0.01, fail_open_timeout_ms=0.0001)

    t = np.linspace(0, 1.5, 24000, endpoint=False)
    audio = (0.2 * np.sin(2 * np.pi * 200 * t)).astype(np.float32)
    res = cascade.predict_chunk(audio, sr=16000)

    # Fail open should trigger due to tiny timeout, but prediction is returned safely without raising
    assert res["cascade"]["fail_open"] is True
    assert cascade.fail_open_events >= 1
    assert "raw_probability" in res
