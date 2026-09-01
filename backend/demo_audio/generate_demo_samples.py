"""
Generates realistic WAV samples for genuine human speech and synthetic voice clone attack.
Used for judge demonstration, unit testing, and preset simulation.
"""

import os
import wave
import struct
import numpy as np

def generate_natural_human_sample(duration_sec: float = 4.0, sr: int = 16000) -> np.ndarray:
    """
    Synthesizes authentic human voice characteristics:
    - Undulating, organic pitch contour (110 - 185 Hz)
    - Natural human vocal cord micro-jitter (1.2%)
    - Natural cycle amplitude shimmer (3.5%)
    - Realistic formant resonances (F1=600Hz, F2=1600Hz, F3=2600Hz)
    - Natural breath pauses between words
    """
    total_samples = int(duration_sec * sr)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)
    
    # Smooth, undulating pitch contour simulating human conversational intonation
    pitch_contour = 135.0 + 35.0 * np.sin(2 * np.pi * 0.8 * t) + 15.0 * np.sin(2 * np.pi * 1.7 * t)
    
    # Phase accumulator with natural cycle-to-cycle micro-jitter
    phases = np.zeros(total_samples)
    current_phase = 0.0
    for i in range(total_samples):
        # 1.2% micro-jitter
        jitter = 1.0 + np.random.normal(0, 0.012)
        inst_freq = pitch_contour[i] * jitter
        current_phase += (2 * np.pi * inst_freq / sr)
        phases[i] = current_phase
        
    # Glottal pulse train harmonics
    glottal = (
        1.0 * np.sin(phases) +
        0.55 * np.sin(2 * phases) +
        0.35 * np.sin(3 * phases) +
        0.20 * np.sin(4 * phases) +
        0.10 * np.sin(5 * phases)
    )
    
    # Syllabic envelope modulation (word pauses)
    syllable_env = np.clip(np.sin(2 * np.pi * 2.5 * t) ** 2, 0.05, 1.0)
    
    # Natural shimmer (amplitude perturbation)
    shimmer = 1.0 + np.random.normal(0, 0.035, total_samples)
    
    # Add gentle vocal tract formant filters (formants at 600, 1600, 2600 Hz)
    formants = (
        0.5 * np.sin(2 * np.pi * 600 * t) * np.exp(-t % 0.1 * 10) +
        0.3 * np.sin(2 * np.pi * 1600 * t) * np.exp(-t % 0.1 * 15) +
        0.15 * np.sin(2 * np.pi * 2600 * t) * np.exp(-t % 0.1 * 20)
    )
    
    signal = (glottal * syllable_env * shimmer) + 0.25 * formants
    signal = signal / (np.max(np.abs(signal)) + 1e-6) * 0.75
    return signal.astype(np.float32)


def generate_cloned_synthetic_sample(duration_sec: float = 4.0, sr: int = 16000) -> np.ndarray:
    """
    Synthesizes characteristic voice clone / neural vocoder spoofing artifacts:
    - Abnormally invariant / locked fundamental frequency (TTS robotic pitch flatness)
    - Unnaturally low micro-jitter (<0.1% or phase-vocoder smearing)
    - High-frequency metallic buzz & vocoder sub-band harmonic ripples (6-8 kHz)
    - Concatenative / diffusion frame splice discontinuities
    """
    total_samples = int(duration_sec * sr)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)
    
    # Locked pitch contour with virtually zero human variance (std < 3 Hz)
    flat_pitch = 145.0 + 1.2 * np.sin(2 * np.pi * 0.2 * t)
    
    # Phase accumulator with synthetic regularity (insufficient natural jitter)
    phases = np.zeros(total_samples)
    current_phase = 0.0
    for i in range(total_samples):
        inst_freq = flat_pitch[i]
        current_phase += (2 * np.pi * inst_freq / sr)
        phases[i] = current_phase

    # Rigid artificial harmonics
    synthetic_glottal = (
        1.0 * np.sin(phases) +
        0.7 * np.sin(2 * phases) +
        0.5 * np.sin(3 * phases) +
        0.35 * np.sin(4 * phases) +
        0.25 * np.sin(5 * phases) +
        0.18 * np.sin(6 * phases)
    )

    # Monotonous speech envelope
    envelope = np.clip(np.abs(np.sin(2 * np.pi * 2.0 * t)), 0.2, 0.95)
    
    # Neural vocoder artifact: high-frequency metallic buzzing in 6500 - 7500 Hz band
    vocoder_buzz = 0.22 * np.sin(2 * np.pi * 7000 * t) * np.sin(2 * np.pi * 120 * t)
    
    # Concatenative splice transients at 1.0s and 2.5s
    splice_clicks = np.zeros(total_samples)
    for splice_t in [1.0, 2.5]:
        idx = int(splice_t * sr)
        if idx < total_samples - 100:
            splice_clicks[idx:idx + 50] = np.random.uniform(-0.8, 0.8, 50)
            
    signal = (synthetic_glottal * envelope) + vocoder_buzz + splice_clicks
    signal = signal / (np.max(np.abs(signal)) + 1e-6) * 0.75
    return signal.astype(np.float32)


def write_wav(filepath: str, audio: np.ndarray, sr: int = 16000):
    audio_int16 = (audio * 32767.0).astype(np.int16)
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())
    print(f"Generated WAV file: {filepath} ({len(audio_int16)} samples)")


if __name__ == "__main__":
    out_dir = os.path.dirname(__file__)
    
    genuine_path = os.path.join(out_dir, "genuine_call_sample.wav")
    cloned_path = os.path.join(out_dir, "cloned_scam_sample.wav")
    
    genuine_audio = generate_natural_human_sample(duration_sec=4.5)
    cloned_audio = generate_cloned_synthetic_sample(duration_sec=4.5)
    
    write_wav(genuine_path, genuine_audio)
    write_wav(cloned_path, cloned_audio)
    print("Demo audio samples successfully generated!")
