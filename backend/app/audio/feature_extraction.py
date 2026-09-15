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
    Accommodates human vocal range from bass (65 Hz) to soprano/children (650 Hz).
    TTS/Voice clones typically exhibit unnaturally flattened or stepped pitch contours.
    """
    frame_size = int(sr * 0.03)  # 30ms frame
    hop_size = int(sr * 0.01)    # 10ms hop
    min_lag = int(sr / 650.0)    # 650 Hz max pitch (covers soprano, female, and child pitch)
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
        if rms < 0.012:
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
            "pitch_mean_hz": 160.0,
            "pitch_std_hz": 0.0,
            "contour_flatness_score": 0.50,
            "pitch_values": []
        }
        
    pitches = np.array(pitches)
    mean_pitch = float(np.mean(pitches))
    std_pitch = float(np.std(pitches))
    cv_pitch = std_pitch / (mean_pitch + 1e-6)
    
    # In natural human speech, intonation naturally moves across syllables:
    # - Standard deviation of F0 is typically > 14 Hz, or coefficient of variation CV >= 0.05 (5%).
    # - Monotone robotic / synthetic speech has unnaturally flat pitch (<8 Hz std and CV < 0.035).
    if std_pitch < 8.0 and cv_pitch < 0.035:
        flatness_score = 0.85  # High synthetic tell (artificially monotone)
    elif std_pitch < 14.0 and cv_pitch < 0.05:
        flatness_score = 0.45
    else:
        flatness_score = 0.12  # Natural human inflection across low or high pitch
        
    return {
        "pitch_mean_hz": round(mean_pitch, 2),
        "pitch_std_hz": round(std_pitch, 2),
        "pitch_cv": round(cv_pitch, 3),
        "contour_flatness_score": round(flatness_score, 3),
        "pitch_values": [round(float(p), 1) for p in pitches[:50]]
    }


def extract_jitter_and_shimmer(audio: np.ndarray, sr: int = 16000) -> dict:
    """
    Computes local cycle-to-cycle perturbation across voiced speech segments:
    - Jitter: perturbation in fundamental period length (human: 0.5% - 2.5%, TTS: often <0.3% or erratic >6.0%)
    - Shimmer: perturbation in cycle peak amplitude (human: 2% - 9%)
    Accurately tracks glottal pitch periods in voiced frames, rejecting octave jumps.
    """
    frame_size = int(sr * 0.03)
    hop_size = int(sr * 0.01)
    min_lag = int(sr / 650.0)
    max_lag = int(sr / 65.0)
    
    if len(audio) < frame_size * 2:
        return {"jitter_percent": 1.1, "shimmer_percent": 3.2, "jitter_anomaly": 0.15}

    periods = []
    amplitudes = []
    num_frames = max(1, (len(audio) - frame_size) // hop_size)
    
    for i in range(num_frames):
        start = i * hop_size
        frame = audio[start:start + frame_size]
        rms = np.sqrt(np.mean(frame ** 2))
        if rms < 0.015:
            continue
            
        corr = np.correlate(frame, frame, mode='full')
        corr = corr[len(corr)//2:]
        if len(corr) > max_lag:
            peak_idx = np.argmax(corr[min_lag:max_lag]) + min_lag
            if corr[peak_idx] > 0.40 * corr[0]:
                periods.append(peak_idx)
                amplitudes.append(rms)
                
    if len(periods) < 4:
        return {"jitter_percent": 1.1, "shimmer_percent": 3.2, "jitter_anomaly": 0.15}
        
    periods = np.array(periods, dtype=float)
    amplitudes = np.array(amplitudes, dtype=float)
    
    # Calculate cycle-to-cycle perturbation for consecutive voiced frames of the same phoneme
    diffs_p = []
    diffs_a = []
    for i in range(1, len(periods)):
        ratio = periods[i] / (periods[i-1] + 1e-6)
        if 0.82 <= ratio <= 1.18:  # Continuous voiced phonation (rejects octave jumps / unvoiced breaks)
            diffs_p.append(abs(periods[i] - periods[i-1]))
            diffs_a.append(abs(amplitudes[i] - amplitudes[i-1]))

    mean_p = float(np.mean(periods))
    mean_a = float(np.mean(amplitudes)) if len(amplitudes) > 0 else 0.05
    
    jitter = (np.mean(diffs_p) / mean_p * 100.0) if diffs_p else 1.25
    shimmer = (np.mean(diffs_a) / (mean_a + 1e-6) * 100.0) if diffs_a else 3.5
    
    # Anomaly indicator:
    # - <0.30%: unnaturally low jitter (over-smoothed neural vocoder / robotic synthesizer)
    # - >6.0%: erratic phase-vocoder artifacts or diffusion discontinuities
    # - 0.5% - 2.5%: normal healthy human vocal fold micro-tremor
    if jitter < 0.30:
        anomaly = 0.80  # Over-smoothed neural vocoder
    elif jitter > 6.0:
        anomaly = 0.75  # Phase jitter smearing
    else:
        anomaly = 0.12  # Natural human vocal tract micro-tremor
        
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
    Calculates frame-by-frame spectral flux across active speech segments.
    Detects splicing, concatenation, or diffusion model chunk discontinuities.
    Excludes silence-to-speech transitions to prevent false alarms on natural plosives.
    """
    frame_size = 512
    hop_size = 256
    
    if len(audio) < frame_size * 2:
        return {"spectral_flux_mean": 0.25, "discontinuity_detected": False, "discontinuity_score": 0.12}

    num_frames = (len(audio) - frame_size) // hop_size
    spectra = []
    energies = []
    for i in range(num_frames):
        st = i * hop_size
        frame = audio[st:st + frame_size]
        rms = np.sqrt(np.mean(frame ** 2))
        energies.append(rms)
        spec = np.abs(rfft(frame * np.hanning(frame_size)))
        norm = np.linalg.norm(spec) + 1e-6
        spectra.append(spec / norm)
        
    if len(spectra) < 2:
        return {"spectral_flux_mean": 0.25, "discontinuity_detected": False, "discontinuity_score": 0.12}
        
    # Evaluate flux between consecutive speech frames (avoiding silence/plosive onset false alarms)
    fluxes = []
    for i in range(1, len(spectra)):
        if energies[i] > 0.015 and energies[i - 1] > 0.015:
            fluxes.append(float(np.linalg.norm(spectra[i] - spectra[i - 1])))
            
    if not fluxes:
        flux_mean = 0.35
        flux_max = 0.50
    else:
        flux_mean = float(np.mean(fluxes))
        flux_max = float(np.max(fluxes))
        
    # Natural human phoneme shifts average 0.30 - 0.52 flux.
    # Discontinuity anomaly: abnormally high average flux (>0.65) or severe spliced discontinuity (>1.28).
    if flux_mean > 0.65 or flux_max > 1.28:
        discontinuity_score = min(1.0, max(0.12, (flux_mean - 0.50) / 0.30))
        discontinuity_flag = True
    else:
        discontinuity_score = 0.12
        discontinuity_flag = False
        
    return {
        "spectral_flux_mean": round(flux_mean, 3),
        "spectral_flux_max": round(flux_max, 3),
        "discontinuity_detected": bool(discontinuity_flag),
        "discontinuity_score": round(float(discontinuity_score), 3)
    }


def extract_high_freq_vocoder_metrics(audio: np.ndarray, sr: int = 16000) -> dict:
    """
    Detects neural vocoder high-frequency artifacts:
    - Brickwall cutoff above 7.0 - 7.5 kHz (common in 22.05/24kHz trained TTS models)
    - High-frequency comb-filtering ripple spikes in the 6.5 - 7.8 kHz region.
    Uses spectral crest factor (peak-to-mean) to distinguish vocoder comb spikes from
    natural human breathiness, fricatives ('s', 'sh'), and high-pitched speech.
    """
    if len(audio) < 512:
        return {"vocoder_cutoff_detected": False, "high_freq_ratio": 0.15, "crest_factor": 2.5, "vocoder_layer_score": 0.12}

    fft_vals = np.abs(rfft(audio * np.hanning(len(audio))))
    freqs = rfftfreq(len(audio), 1.0 / sr)

    # Energy bands
    mid_band = (freqs >= 2000) & (freqs <= 5000)
    high_band = (freqs >= 6500) & (freqs <= 7800)

    mid_energy = np.mean(fft_vals[mid_band] ** 2) if np.any(mid_band) else 1e-6
    high_energy = np.mean(fft_vals[high_band] ** 2) if np.any(high_band) else 1e-6

    # Ratio of high to mid energy
    hf_ratio = float(high_energy / (mid_energy + 1e-6))
    
    # Spectral crest factor in high band
    high_vals = fft_vals[high_band] if np.any(high_band) else np.array([1.0])
    crest_factor = float(np.max(high_vals) / (np.mean(high_vals) + 1e-7))
    
    # Abnormal conditions:
    # 1. Extreme brickwall drop: high energy drops by > 35dB relative to mid (typical of TTS cutoff)
    # 2. Elevated vocoder buzz: comb-filtering harmonic spikes (hf_ratio > 0.40 AND crest_factor > 8.5)
    is_brickwall = hf_ratio < 0.0008
    is_vocoder_buzz = bool(hf_ratio > 0.40 and crest_factor > 8.5)
    
    if is_brickwall:
        score = 0.85  # Strong synthetic tell (band-limited neural generation)
    elif is_vocoder_buzz:
        score = 0.80  # Neural vocoder harmonic comb artifact
    else:
        score = 0.12  # Natural human spectral slope
        
    return {
        "vocoder_cutoff_detected": bool(is_brickwall or is_vocoder_buzz),
        "high_freq_ratio": round(hf_ratio, 5),
        "crest_factor": round(crest_factor, 2),
        "vocoder_layer_score": round(score, 3)
    }


def extract_harmonic_to_noise_ratio(audio: np.ndarray, sr: int = 16000) -> dict:
    """
    Estimates Harmonic-to-Noise Ratio (HNR) across voiced speech phonemes.
    Natural human conversational speech exhibits dynamic HNR (6 - 25 dB) with micro-variations.
    Artificial voices frequently have mathematically rigid HNR or phase-smearing noise (<4 dB).
    """
    if len(audio) < 1024:
        return {"hnr_db": 15.0, "hnr_anomaly_score": 0.15}

    frame_sz = 512
    hop_sz = 256
    min_lag = int(sr / 650.0)
    max_lag = int(sr / 65.0)

    hnr_list = []
    num_frames = (len(audio) - frame_sz) // hop_sz
    for i in range(num_frames):
        st = i * hop_sz
        frame = audio[st:st + frame_sz]
        rms = np.sqrt(np.mean(frame ** 2))
        if rms < 0.02:
            continue
            
        raw_c = np.correlate(frame, frame, mode='full')[len(frame)-1:]
        weights = np.arange(len(frame), 0, -1)
        unb_c = raw_c / weights
        
        if len(unb_c) > max_lag:
            p_lag = np.argmax(unb_c[min_lag:max_lag]) + min_lag
            r_p = unb_c[p_lag]
            r_0 = unb_c[0]
            if r_p > 0.40 * r_0:
                noise = max(1e-5, r_0 - r_p)
                hnr_val = 10.0 * np.log10(r_p / noise)
                hnr_list.append(hnr_val)

    if not hnr_list:
        mean_hnr = 14.0
    else:
        mean_hnr = float(np.mean(hnr_list))
        
    mean_hnr = float(np.clip(mean_hnr, -5.0, 35.0))

    # Anomaly condition: unnaturally low HNR for voiced speech (<4.0 dB) or unrealistically high (>32.0 dB)
    if mean_hnr < 4.0 or mean_hnr > 32.0:
        hnr_anomaly = 0.75
    else:
        hnr_anomaly = 0.12

    return {
        "hnr_db": round(mean_hnr, 2),
        "hnr_anomaly_score": round(hnr_anomaly, 3)
    }


def extract_acoustic_features(audio: np.ndarray, sr: int = 16000) -> dict:
    """
    Extracts all 5 forensic layers of acoustic and prosodic anti-spoofing features.
    """
    if len(audio) == 0:
        return {
            "energy_rms": 0.0,
            "pitch": {"pitch_mean_hz": 0.0, "pitch_std_hz": 0.0, "contour_flatness_score": 0.0},
            "perturbation": {"jitter_percent": 0.0, "shimmer_percent": 0.0, "jitter_anomaly": 0.0},
            "spectral_flatness": 0.0,
            "discontinuity": {"discontinuity_detected": False, "discontinuity_score": 0.0},
            "vocoder_metrics": {"vocoder_cutoff_detected": False, "vocoder_layer_score": 0.0},
            "hnr": {"hnr_db": 0.0, "hnr_anomaly_score": 0.0},
            "prosodic_spoof_score": 0.0,
            "layers": {}
        }

    rms_energy = float(np.sqrt(np.mean(audio ** 2)))
    pitch_data = extract_pitch_and_contour(audio, sr=sr)
    perturb_data = extract_jitter_and_shimmer(audio, sr=sr)
    flatness = extract_spectral_flatness(audio)
    discontinuity_data = extract_spectral_flux_and_discontinuity(audio, sr=sr)
    vocoder_data = extract_high_freq_vocoder_metrics(audio, sr=sr)
    hnr_data = extract_harmonic_to_noise_ratio(audio, sr=sr)
    
    # 5-Layer Forensic Decision Matrix
    # Layer 1: Pitch Dynamic Inflection
    l1_score = pitch_data["contour_flatness_score"]
    l1_pass = l1_score < 0.50

    # Layer 2: Vocal Fold Jitter / Shimmer
    l2_score = perturb_data["jitter_anomaly"]
    l2_pass = l2_score < 0.40

    # Layer 3: High-Frequency Vocoder Cutoff / Buzz
    l3_score = vocoder_data["vocoder_layer_score"]
    l3_pass = not vocoder_data["vocoder_cutoff_detected"]

    # Layer 4: Harmonic-to-Noise Naturalness
    l4_score = hnr_data["hnr_anomaly_score"]
    l4_pass = l4_score < 0.45

    # Layer 5: Spectral Discontinuity & Phase Flux
    l5_score = discontinuity_data["discontinuity_score"]
    l5_pass = not discontinuity_data["discontinuity_detected"]

    # Weighted Prosodic Composite Score [0.0 - 1.0]
    prosodic_composite = (
        0.30 * l1_score +
        0.25 * l2_score +
        0.20 * l3_score +
        0.15 * l4_score +
        0.10 * l5_score
    )

    layers_summary = {
        "l1_pitch_naturalness": {"score": round(l1_score, 3), "passed": l1_pass, "label": "Pitch Dynamic Inflection"},
        "l2_vocal_fold_tremor": {"score": round(l2_score, 3), "passed": l2_pass, "label": "Vocal Fold Micro-Jitter"},
        "l3_vocoder_cutoff": {"score": round(l3_score, 3), "passed": l3_pass, "label": "High-Freq Vocoder Roll-off"},
        "l4_harmonic_hnr": {"score": round(l4_score, 3), "passed": l4_pass, "label": "Harmonic-to-Noise Naturalness"},
        "l5_phase_continuity": {"score": round(l5_score, 3), "passed": l5_pass, "label": "Phase & Splice Continuity"}
    }
    
    return {
        "energy_rms": round(rms_energy, 4),
        "pitch": pitch_data,
        "perturbation": perturb_data,
        "spectral_flatness": flatness,
        "discontinuity": discontinuity_data,
        "vocoder_metrics": vocoder_data,
        "hnr": hnr_data,
        "prosodic_spoof_score": round(float(prosodic_composite), 3),
        "layers": layers_summary
    }
