"""
Tests for Voice Activity Detection and streaming sliding buffer.
"""

import numpy as np
import pytest
from app.audio.chunker import VoiceActivityDetector, StreamingAudioBuffer

def test_vad_silence_vs_speech():
    vad = VoiceActivityDetector(energy_threshold=0.01)
    
    silence = np.zeros(16000, dtype=np.float32)
    is_voiced_silence, energy_silence = vad.is_speech(silence)
    assert not is_voiced_silence
    assert energy_silence < 0.001

    t = np.linspace(0, 1.0, 16000, endpoint=False)
    speech = (0.5 * np.sin(2 * np.pi * 200 * t)).astype(np.float32)
    is_voiced_speech, energy_speech = vad.is_speech(speech)
    assert is_voiced_speech
    assert energy_speech > 0.1

def test_streaming_buffer_accumulation():
    # 1.5s window at 16kHz = 24000 samples, 50% overlap = 12000 hop
    buffer = StreamingAudioBuffer(sample_rate=16000, window_sec=1.5, overlap_ratio=0.5)
    
    # Send 250ms chunks (4000 samples each)
    chunk = np.random.uniform(-0.1, 0.1, 4000).astype(np.float32)
    
    # 1st chunk (4000 samples): Not enough for 24000
    res1 = buffer.add_chunk(chunk)
    assert len(res1) == 0
    
    # Send 5 more chunks (total 24000 samples)
    for _ in range(4):
        buffer.add_chunk(chunk)
    res_ready = buffer.add_chunk(chunk)
    assert len(res_ready) >= 1
    window, is_voiced, energy = res_ready[0]
    assert len(window) == 24000
