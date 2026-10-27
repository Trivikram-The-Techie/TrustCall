"""
Tests for Packet Loss Concealment (PLC) Detector.
"""

import numpy as np
from app.audio.plc_detector import plc_detector

def test_clean_audio_no_plc():
    audio = np.sin(2 * np.pi * 220 * np.linspace(0, 1, 16000)).astype(np.float32)
    res = plc_detector.analyze_plc_artifacts(audio)
    assert "plc_detected" in res
    assert res["repeated_frames_count"] == 0

def test_simulated_plc_repetition():
    # Simulate repeated frames with attenuation (PLC behavior)
    frame = np.random.normal(0, 0.2, 320).astype(np.float32)
    # Repeated 3 times with 0.85 attenuation
    audio = np.concatenate([frame, frame * 0.85, frame * 0.72, frame * 0.61])
    res = plc_detector.analyze_plc_artifacts(audio)
    assert res["repeated_frames_count"] >= 1
