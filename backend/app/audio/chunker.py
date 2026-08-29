"""
Streaming audio buffer and Voice Activity Detection (VAD).
Accumulates short incoming frames (200-500ms) into overlapping analysis windows (1.0-2.0s)
and drops dead air / silence chunks.
"""

import numpy as np
from typing import Optional, List, Tuple
from app.config import settings

class VoiceActivityDetector:
    """
    Lightweight energy and zero-crossing rate (ZCR) based Voice Activity Detector.
    Filters out background air, line hum, and silence frames.
    """
    def __init__(
        self, 
        energy_threshold: float = settings.VAD_ENERGY_THRESHOLD, 
        zcr_threshold: float = settings.VAD_ZCR_THRESHOLD
    ):
        self.energy_threshold = energy_threshold
        self.zcr_threshold = zcr_threshold

    def is_speech(self, audio: np.ndarray) -> Tuple[bool, float]:
        """
        Determines if the frame contains voiced speech.
        Returns: (is_voiced: bool, rms_energy: float)
        """
        if len(audio) == 0:
            return False, 0.0

        # Root-mean-square energy
        rms = float(np.sqrt(np.mean(audio ** 2)))
        
        # Zero-crossing rate
        zero_crossings = np.sum(np.abs(np.diff(audio > 0))) / len(audio)
        
        # Voiced speech condition
        has_energy = rms >= self.energy_threshold
        has_zcr = zero_crossings >= self.zcr_threshold
        
        is_active = bool(has_energy and has_zcr)
        return is_active, round(rms, 5)


class StreamingAudioBuffer:
    """
    Circular sliding audio buffer for live WebSocket call ingestion.
    Collects 200-500ms chunks and emits overlapping 1.5s analysis windows.
    """
    def __init__(
        self, 
        sample_rate: int = settings.SAMPLE_RATE,
        window_sec: float = settings.ANALYSIS_WINDOW_SEC,
        overlap_ratio: float = settings.OVERLAP_RATIO
    ):
        self.sample_rate = sample_rate
        self.window_samples = int(sample_rate * window_sec)
        self.hop_samples = int(self.window_samples * (1.0 - overlap_ratio))
        self.buffer = np.zeros(0, dtype=np.float32)
        self.vad = VoiceActivityDetector()
        self.unprocessed_samples = 0

    def add_chunk(self, chunk: np.ndarray) -> List[Tuple[np.ndarray, bool, float]]:
        """
        Appends incoming audio chunk to buffer.
        Returns a list of tuples: [(analysis_window, is_voiced, energy_rms), ...]
        """
        if len(chunk) == 0:
            return []

        self.buffer = np.concatenate([self.buffer, chunk.astype(np.float32)])
        self.unprocessed_samples += len(chunk)
        
        ready_windows = []
        
        # Extract analysis windows when enough samples have accumulated
        while len(self.buffer) >= self.window_samples and self.unprocessed_samples >= self.hop_samples:
            window = self.buffer[:self.window_samples].copy()
            is_voiced, energy = self.vad.is_speech(window)
            
            ready_windows.append((window, is_voiced, energy))
            
            # Slide window forward by hop_samples
            self.buffer = self.buffer[self.hop_samples:]
            self.unprocessed_samples = max(0, self.unprocessed_samples - self.hop_samples)

        # Prevent unbounded buffer growth if quiet
        max_buffer = self.window_samples * 4
        if len(self.buffer) > max_buffer:
            self.buffer = self.buffer[-max_buffer:]
            self.unprocessed_samples = min(self.unprocessed_samples, max_buffer)

        return ready_windows

    def reset(self):
        """Clears the buffer."""
        self.buffer = np.zeros(0, dtype=np.float32)
        self.unprocessed_samples = 0
