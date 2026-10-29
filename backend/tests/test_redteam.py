"""
Unit and integration tests for Red-Team Attack Lab & CUSUM Burst Aggregator Mitigation.
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.redteam.attack_simulator import attack_simulator
from app.models.burst_aggregator import BurstRobustAggregator

client = TestClient(app)

def test_attack_codec_laundering():
    audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1.0, 16000)).astype(np.float32)
    for codec in ["g711", "amr_nb", "mp3"]:
        processed = attack_simulator.codec_laundering(audio, codec=codec)
        assert len(processed) == len(audio)
        assert np.isfinite(processed).all()

def test_attack_packet_loss():
    audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1.0, 16000)).astype(np.float32)
    for drop in [0.05, 0.10, 0.20]:
        processed = attack_simulator.packet_loss(audio, drop_rate=drop)
        assert len(processed) == len(audio)
        assert np.isfinite(processed).all()

def test_attack_noise_mix():
    audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1.0, 16000)).astype(np.float32)
    for noise_type in ["ambient", "music", "white"]:
        mixed = attack_simulator.noise_mix(audio, snr_db=15.0, noise_type=noise_type)
        assert len(mixed) == len(audio)
        assert np.max(np.abs(mixed)) <= 1.0

def test_attack_re_recording():
    audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1.0, 16000)).astype(np.float32)
    re_rec = attack_simulator.re_recording(audio, room_size="medium")
    assert len(re_rec) == len(audio)
    assert np.isfinite(re_rec).all()

def test_attack_splicing():
    cloned = np.ones(16000, dtype=np.float32)
    genuine = np.zeros(16000, dtype=np.float32)
    spliced = attack_simulator.splicing(cloned, genuine, splice_ratio=0.50, splice_mode="prefix_suffix")
    assert len(spliced) == 16000
    # Prefix should contain genuine (zeros) and middle should contain cloned (ones)
    assert spliced[0] == 0.0
    assert spliced[8000] == 1.0

def test_burst_aggregator_cusum_mitigation():
    """
    Core Phase 2 Mitigation Test:
    Verifies that a spliced synthetic burst in an otherwise genuine/silent stream
    is washed out by standard rolling median (causing evasion),
    but caught and escalated by the CUSUM / Max-burst aggregator.
    """
    agg = BurstRobustAggregator(window_size=4)
    # Sequence of chunk probabilities: 3 genuine chunks, 1 synthetic clone burst
    chunk_scores = [0.08, 0.09, 0.98, 0.07]

    # Standard rolling median:
    diluted_median = float(np.median(chunk_scores))
    assert diluted_median < 0.20, f"Standard median {diluted_median} should be diluted by genuine chunks"

    # Mitigated CUSUM Aggregator:
    step_results = []
    for score in chunk_scores:
        step_results.append(agg.update(score))

    # At turn 3 (when 0.98 synthetic burst arrives):
    burst_step = step_results[2]
    assert burst_step["burst_detected"] is True
    assert burst_step["cusum_statistic"] >= 0.45

    # At turn 4 (after burst, returning to genuine 0.07):
    final_step = step_results[3]
    # Max-window retains the burst memory, preventing median dilution
    assert final_step["burst_detected"] is True
    assert final_step["mitigated_probability"] >= 0.75, (
        f"Mitigated probability {final_step['mitigated_probability']} should catch synthetic burst"
    )

def test_redteam_api_presets():
    response = client.get("/v1/redteam/presets")
    assert response.status_code == 200
    data = response.json()
    assert "presets" in data
    assert len(data["presets"]) >= 2
    assert "attack_types" in data
    assert len(data["attack_types"]) == 5

def test_redteam_api_all_attacks():
    """Verifies that all 5 red-team attacks execute end-to-end via POST /v1/redteam/run."""
    attacks = [
        {"attack_type": "codec_laundering", "parameters": {"codec": "amr_nb"}},
        {"attack_type": "packet_loss", "parameters": {"drop_rate": 0.10}},
        {"attack_type": "noise_mix", "parameters": {"snr_db": 10.0, "noise_type": "ambient"}},
        {"attack_type": "re_recording", "parameters": {"room_size": "medium"}},
        {"attack_type": "splicing", "parameters": {"splice_ratio": 0.50, "splice_mode": "prefix_suffix"}},
    ]

    for payload in attacks:
        payload["preset_id"] = "cloned_scam"
        res = client.post("/v1/redteam/run", json=payload)
        assert res.status_code == 200, f"Failed for {payload['attack_type']}: {res.text}"
        data = res.json()
        assert "original" in data
        assert "attacked_baseline" in data
        assert "attacked_mitigated" in data
        assert "verdict_summary" in data
        assert len(data["original"]["waveform"]) == 120
        assert len(data["attacked_baseline"]["waveform"]) == 120
        assert "low_band_pct" in data["original"]["spectral"]
