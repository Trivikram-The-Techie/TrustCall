"""
Acoustic and prosodic feature extraction for synthetic speech & voice clone detection.
Extracts log-mel spectrogram, pitch contour, jitter, shimmer, spectral flatness, and flux.
"""

import base64
import io
import wave
import numpy as np
from scipy import signal
from scipy.fft import rfft, rfftfreq

def decode_audio_bytes(audio_bytes: bytes, target_sr: int = 16000) -> np.ndarray:
    """
    Decodes raw audio bytes (WAV or raw PCM 16-bit) to float32 numpy array normalized to [-1, 1]
    and resamples to target_sr if necessary.
    """
    if len(audio_bytes) == 0:
        return np.zeros(0, dtype=np.float32)

    # Check for RIFF/WAV header
    if audio_bytes[:4] == b'RIFF':
        try:
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                raw_data = wf.readframes(n_frames)
                
                if sampwidth == 2:
                    audio = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                elif sampwidth == 1:
                    audio = (np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
                elif sampwidth == 4:
                    audio = np.frombuffer(raw_data, dtype=np.int32).astype(np.float32) / 2147483648.0
                else:
                    audio = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

                if n_channels > 1:
                    audio = audio.reshape(-1, n_channels).mean(axis=1)

                if framerate != target_sr and len(audio) > 0:
                    num_samples = int(len(audio) * target_sr / framerate)
                    audio = signal.resample(audio, num_samples)

                return audio.astype(np.float32)
        except Exception:
            pass

    # Treat as raw 16-bit signed PCM mono
    try:
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        return audio
    except Exception:
        # Fallback float32
        return np.frombuffer(audio_bytes, dtype=np.float32)


def decode_base64_audio(b64_str: str, target_sr: int = 16000) -> np.ndarray:
    """Decodes base64 encoded audio string to float32 numpy array."""
    # Strip data URL prefix if present
    if ',' in b64_str:
        b64_str = b64_str.split(',', 1)[1]
    audio_bytes = base64.b64decode(b64_str)
    return decode_audio_bytes(audio_bytes, target_sr=target_sr)


def compute_log_mel_spectrogram(
    audio: np.ndarray, 
    sr: int = 16000, 
    n_mels: int = 80, 
    n_fft: int = 512, 
    hop_length: int = 160
) -> np.ndarray:
    """
    Computes log-mel spectrogram using numpy/scipy filterbanks.
    Returns (n_mels, time_frames).
    """
    if len(audio) < n_fft:
        # Pad short audio
        audio = np.pad(audio, (0, n_fft - len(audio)), mode='constant')

    # STFT using ShortTimeFFT or spectrogram
    window = np.hanning(n_fft)
    freqs, times, Sxx = signal.spectrogram(
        audio, 
        fs=sr, 
        window=window, 
        nperseg=n_fft, 
        noverlap=n_fft - hop_length,
        mode='magnitude'
    )
    
    # Mel filterbank construction
    mel_min = 0.0
    mel_max = 2595.0 * np.log10(1.0 + (sr / 2.0) / 700.0)
    mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
    hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)
    
    bin_points = np.floor((n_fft + 1) * hz_points / sr).astype(int)
    bin_points = np.clip(bin_points, 0, Sxx.shape[0] - 1)
    
    fbank = np.zeros((n_mels, Sxx.shape[0]), dtype=np.float32)
    for m in range(1, n_mels + 1):
        f_m_minus = bin_points[m - 1]
        f_m = bin_points[m]
        f_m_plus = bin_points[m + 1]
        
        if f_m > f_m_minus:
            fbank[m - 1, f_m_minus:f_m] = (np.arange(f_m_minus, f_m) - f_m_minus) / (f_m - f_m_minus)
        if f_m_plus > f_m:
            fbank[m - 1, f_m:f_m_plus] = (f_m_plus - np.arange(f_m, f_m_plus)) / (f_m_plus - f_m)
            
    mel_spectrogram = np.dot(fbank, Sxx)
    mel_spectrogram = np.maximum(mel_spectrogram, 1e-6)
    log_mel = np.log10(mel_spectrogram)
    return log_mel.astype(np.float32)


def extract_pitch_and_contour(audio: np.ndarray, sr: int = 16000) -> dict:
    """
    Computes pitch contour via autocorrelation windowing.
    Evaluates mean pitch, pitch variance, and contour gradient smoothness.
    TTS/Voice clones typically exhibit unnaturally flattened or stepped pitch contours.
    """
    frame_size = int(sr * 0.03)  # 30ms frame
    hop_size = int(sr * 0.01)    # 10ms hop
    min_lag = int(sr / 400.0)    # 400 Hz max pitch
    max_lag = int(sr / 65.0)     # 65 Hz min pitch
    
    if len(audio) < frame_size:
        return {
            "pitch_mean_hz": 0.0,
            "pitch_std_hz": 0.0,
            "contour_flatness_score": 0.5,
            "pitch_values": []
        }

    pitches = []
    num_frames = max(1, (len(audio) - frame_size) // hop_size)
    
    for i in range(num_frames):
        start = i * hop_size
        frame = audio[start:start + frame_size]
        # Energy check for voiced frame
        rms = np.sqrt(np.mean(frame ** 2))
        if rms < 0.01:
            continue
            
        corr = np.correlate(frame, frame, mode='full')
        corr = corr[len(corr)//2:]
        
        if len(corr) > max_lag:
            windowed_corr = corr[min_lag:max_lag]
            peak_idx = np.argmax(windowed_corr) + min_lag
            if corr[peak_idx] > 0.35 * corr[0]:
                pitch_hz = sr / peak_idx
                pitches.append(pitch_hz)
                
    if len(pitches) < 3:
        return {
            "pitch_mean_hz": 120.0,
            "pitch_std_hz": 0.0,
            "contour_flatness_score": 0.7,
            "pitch_values": []
        }
        
    pitches = np.array(pitches)
    mean_pitch = float(np.mean(pitches))
    std_pitch = float(np.std(pitches))
    
    # In natural human speech, standard deviation of F0 is typically 18-50 Hz.
    # In robotic or synthesized speech, F0 is either unnaturally invariant (<10 Hz)
    # or shows mechanical steps.
    if std_pitch < 10.0:
        flatness_score = 0.85  # High synthetic tell
    elif std_pitch < 18.0:
        flatness_score = 0.55
    else:
        flatness_score = 0.15  # Natural human inflection
        
    return {
        "pitch_mean_hz": round(mean_pitch, 2),
        "pitch_std_hz": round(std_pitch, 2),
        "contour_flatness_score": round(flatness_score, 3),
        "pitch_values": [round(p, 1) for p in pitches[:50]]
    }


def extract_jitter_and_shimmer(audio: np.ndarray, sr: int = 16000) -> dict:
    """
    Computes local cycle-to-cycle perturbation:
    - Jitter: variation in fundamental period length (human: 0.5% - 2.5%, TTS: often <0.3% or erratic)
    - Shimmer: variation in cycle peak amplitude (human: 2% - 6%)
    """
    frame_size = int(sr * 0.025)
    hop_size = int(sr * 0.01)
    
    if len(audio) < frame_size * 2:
        return {"jitter_percent": 1.0, "shimmer_percent": 3.0, "jitter_anomaly": 0.2}

    peaks = []
    amplitudes = []
    num_frames = (len(audio) - frame_size) // hop_size
    
    for i in range(num_frames):
        start = i * hop_size
        frame = audio[start:start + frame_size]
        rms = np.sqrt(np.mean(frame ** 2))
        if rms > 0.015:
            max_idx = np.argmax(np.abs(frame))
            peaks.append(start + max_idx)
            amplitudes.append(np.abs(frame[max_idx]))
            
    if len(peaks) < 4:
        return {"jitter_percent": 1.1, "shimmer_percent": 3.2, "jitter_anomaly": 0.25}
        
    periods = np.diff(peaks)
    periods = periods[periods > 0]
    
    if len(periods) < 3:
        return {"jitter_percent": 1.1, "shimmer_percent": 3.2, "jitter_anomaly": 0.25}
        
    # Relative Jitter (RAP approximation)
    mean_period = np.mean(periods)
    jitter = (np.mean(np.abs(np.diff(periods))) / (mean_period + 1e-6)) * 100.0
    
    # Relative Shimmer
    amps = np.array(amplitudes)
    mean_amp = np.mean(amps)
    shimmer = (np.mean(np.abs(np.diff(amps))) / (mean_amp + 1e-6)) * 100.0
    
    # Anomaly indicator: synthetic voices often have unnaturally low jitter (<0.4%)
    # or extreme jitter due to phase-vocoder artifacts (>6.0%)
    if jitter < 0.4:
        anomaly = 0.80  # Too perfect (robotic / vocoded)
    elif jitter > 5.5:
        anomaly = 0.75  # Phase jitter artifacts
    else:
        anomaly = 0.15  # Natural human vocal tract micro-tremor
        
    return {
        "jitter_percent": round(float(jitter), 3),
        "shimmer_percent": round(float(shimmer), 3),
        "jitter_anomaly": round(float(anomaly), 3)
    }


def extract_spectral_flatness(audio: np.ndarray) -> float:
    """
    Computes Wiener spectral flatness (ratio of geometric mean to arithmetic mean).
    Values near 1 represent white noise, values near 0 represent pure tone.
    Neural vocoders often leave characteristic flatness imbalances across sub-bands.
    """
    if len(audio) < 256:
        return 0.1
    spectrum = np.abs(rfft(audio * np.hanning(len(audio))))
    spectrum = np.maximum(spectrum, 1e-7)
    
    geometric_mean = np.exp(np.mean(np.log(spectrum)))
    arithmetic_mean = np.mean(spectrum)
    flatness = geometric_mean / (arithmetic_mean + 1e-7)
    return round(float(np.clip(flatness, 0.0, 1.0)), 4)


def extract_spectral_flux_and_discontinuity(audio: np.ndarray, sr: int = 16000) -> dict:
    """
    Calculates frame-by-frame spectral flux. Detects splicing, concatenation,
    or diffusion model chunk discontinuities.
    """
    frame_size = 512
    hop_size = 256
    
    if len(audio) < frame_size * 2:
        return {"spectral_flux_mean": 0.2, "discontinuity_detected": False, "discontinuity_score": 0.1}

    # Consecutive frame spectra
    num_frames = (len(audio) - frame_size) // hop_size
    spectra = []
    for i in range(num_frames):
        st = i * hop_size
        windowed = audio[st:st + frame_size] * np.hanning(frame_size)
        spec = np.abs(rfft(windowed))
        norm = np.linalg.norm(spec) + 1e-6
        spectra.append(spec / norm)
        
    if len(spectra) < 2:
        return {"spectral_flux_mean": 0.2, "discontinuity_detected": False, "discontinuity_score": 0.1}
        
    spectra = np.array(spectra)
    fluxes = np.linalg.norm(np.diff(spectra, axis=0), axis=1)
    
    flux_mean = float(np.mean(fluxes))
    flux_max = float(np.max(fluxes)) if len(fluxes) > 0 else 0.0
    
    # Anomaly condition: sharp discontinuous jump between consecutive speech frames
    discontinuity_score = min(1.0, max(0.0, (flux_max - 0.75) / 0.5)) if flux_max > 0.75 else 0.1
    discontinuity_flag = flux_max > 0.85
    
    return {
        "spectral_flux_mean": round(flux_mean, 3),
        "spectral_flux_max": round(flux_max, 3),
        "discontinuity_detected": bool(discontinuity_flag),
        "discontinuity_score": round(float(discontinuity_score), 3)
    }


def extract_acoustic_features(audio: np.ndarray, sr: int = 16000) -> dict:
    """
    Extracts all classical and prosodic anti-spoofing features into a unified dictionary.
    """
    if len(audio) == 0:
        return {
            "energy_rms": 0.0,
            "pitch": {"pitch_mean_hz": 0.0, "pitch_std_hz": 0.0, "contour_flatness_score": 0.0},
            "perturbation": {"jitter_percent": 0.0, "shimmer_percent": 0.0, "jitter_anomaly": 0.0},
            "spectral_flatness": 0.0,
            "discontinuity": {"discontinuity_detected": False, "discontinuity_score": 0.0},
            "prosodic_spoof_score": 0.0
        }

    rms_energy = float(np.sqrt(np.mean(audio ** 2)))
    pitch_data = extract_pitch_and_contour(audio, sr=sr)
    perturb_data = extract_jitter_and_shimmer(audio, sr=sr)
    flatness = extract_spectral_flatness(audio)
    discontinuity_data = extract_spectral_flux_and_discontinuity(audio, sr=sr)
    
    # Prosodic composite score [0, 1]
    prosodic_composite = (
        0.45 * pitch_data["contour_flatness_score"] +
        0.35 * perturb_data["jitter_anomaly"] +
        0.20 * (1.0 if flatness > 0.35 or flatness < 0.02 else 0.2)
    )
    
    return {
        "energy_rms": round(rms_energy, 4),
        "pitch": pitch_data,
        "perturbation": perturb_data,
        "spectral_flatness": flatness,
        "discontinuity": discontinuity_data,
        "prosodic_spoof_score": round(float(prosodic_composite), 3)
    }
