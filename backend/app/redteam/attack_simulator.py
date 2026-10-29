"""
Red-Team Audio Adversarial Attack Simulator.
Applies realistic physical and telecommunications attacks to speech audio:
1. Codec Laundering (G.711 mu-law, AMR-NB 8kHz, MP3 round-trip)
2. Packet Loss (5%, 10%, 20% drops with ITU-T PLC attenuation)
3. Background Noise & Music Mix at selectable SNR (5 - 30 dB)
4. Speaker-to-Mic Re-recording (Room impulse response reverberation + speaker coloration + room hiss)
5. Silence & Segment Splicing (Hybrid attack: genuine speech / silence interleaving to bypass median smoothing)

All transformations are performed strictly in-memory on NumPy arrays (zero audio written to disk).
"""

import numpy as np
from scipy import signal
from typing import Dict, Any, Tuple, Optional

class RedTeamAttackSimulator:
    """
    Executes red-team adversarial evasion transformations on in-memory audio buffers.
    """
    def __init__(self, sample_rate: int = 16000):
        self.sr = sample_rate

    # -------------------------------------------------------------------------
    # Attack 1: Codec Laundering
    # -------------------------------------------------------------------------
    def codec_laundering(self, audio: np.ndarray, codec: str = "amr_nb") -> np.ndarray:
        """
        Forces audio through lossy telephony companding and low-bitrate perceptual compression.
        codec: 'g711' | 'amr_nb' | 'mp3'
        """
        audio = audio.astype(np.float32)
        if len(audio) == 0:
            return audio

        if codec == "g711":
            # G.711 mu-law 8-bit companding + 8 kHz decimation
            num_8k = int(len(audio) * 8000 / self.sr)
            a8k = signal.resample(audio, num_8k)
            mu = 255.0
            s = np.sign(a8k) * np.log(1.0 + mu * np.abs(a8k)) / np.log(1.0 + mu)
            quant = np.round((s + 1.0) / 2.0 * 255.0) / 255.0 * 2.0 - 1.0
            decomp = np.sign(quant) * (1.0 / mu) * ((1.0 + mu) ** np.abs(quant) - 1.0)
            return signal.resample(decomp, len(audio)).astype(np.float32)

        elif codec == "amr_nb":
            # AMR-NB: 8 kHz downsampling + 300-3400 Hz bandpass + ACELP non-linear tanh saturation
            num_8k = int(len(audio) * 8000 / self.sr)
            a8k = signal.resample(audio, num_8k)
            sos = signal.butter(4, [300.0, 3400.0], btype='bandpass', fs=8000, output='sos')
            filtered = signal.sosfilt(sos, a8k)
            # ACELP CELP linear prediction quantization distortion
            distorted = np.tanh(filtered * 1.25) / 1.25
            return signal.resample(distorted, len(audio)).astype(np.float32)

        elif codec == "mp3":
            # MP3 MDCT subband quantization with 7.5 kHz brickwall rolloff
            sos = signal.butter(6, 7500.0, btype='lowpass', fs=self.sr, output='sos')
            filtered = signal.sosfilt(sos, audio)
            step = 1.0 / 64.0  # Coarse MDCT psychoacoustic quantizer
            return (np.round(filtered / step) * step).astype(np.float32)

        return audio

    # -------------------------------------------------------------------------
    # Attack 2: Packet Loss
    # -------------------------------------------------------------------------
    def packet_loss(self, audio: np.ndarray, drop_rate: float = 0.10) -> np.ndarray:
        """
        Simulates random VoIP RTP packet drops with ITU-T G.711 App I Packet Loss Concealment (PLC).
        drop_rate: 0.05 (5%), 0.10 (10%), 0.20 (20%)
        """
        audio = audio.astype(np.float32)
        frame_len = int(self.sr * 0.02)  # 20ms = 320 samples
        if len(audio) < frame_len:
            return audio

        num_frames = len(audio) // frame_len
        out = np.copy(audio)
        rng = np.random.RandomState(42)

        last_good = np.zeros(frame_len, dtype=np.float32)
        consecutive_drops = 0

        for i in range(num_frames):
            start = i * frame_len
            end = start + frame_len
            if rng.uniform(0, 1) < drop_rate and i > 0:
                consecutive_drops += 1
                # PLC attenuation: 0.8^consecutive_drops
                attenuation = 0.8 ** consecutive_drops
                out[start:end] = last_good * attenuation
            else:
                consecutive_drops = 0
                last_good = out[start:end]

        return out.astype(np.float32)

    # -------------------------------------------------------------------------
    # Attack 3: Background Noise / Music Mix
    # -------------------------------------------------------------------------
    def noise_mix(self, audio: np.ndarray, snr_db: float = 10.0, noise_type: str = "ambient") -> np.ndarray:
        """
        Blends additive ambient noise, harmonic music chords, or white noise at exact selectable SNR.
        noise_type: 'ambient' | 'music' | 'white'
        """
        audio = audio.astype(np.float32)
        signal_power = np.mean(audio ** 2) + 1e-9
        noise_power_target = signal_power / (10.0 ** (snr_db / 10.0))
        rng = np.random.RandomState(42)

        n_samples = len(audio)
        if noise_type == "white":
            raw_noise = rng.normal(0, 1.0, n_samples)
        elif noise_type == "music":
            # Multi-tone harmonic chord (A4 440Hz + C#5 554Hz + E5 659Hz) simulating background radio music
            t = np.linspace(0, n_samples / self.sr, n_samples)
            raw_noise = (
                0.5 * np.sin(2 * np.pi * 440.0 * t) +
                0.3 * np.sin(2 * np.pi * 554.37 * t) +
                0.2 * np.sin(2 * np.pi * 659.25 * t)
            )
        else: # ambient street / room pink noise
            white = rng.normal(0, 1.0, n_samples)
            # 1/f pink noise approximation via IIR filter
            b, a = [0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400]
            try:
                raw_noise = signal.lfilter(b, a, white)
            except Exception:
                raw_noise = white

        # Normalize and scale to target SNR
        noise_power = np.mean(raw_noise ** 2) + 1e-9
        scaled_noise = raw_noise * np.sqrt(noise_power_target / noise_power)
        mixed = np.clip(audio + scaled_noise, -1.0, 1.0)
        return mixed.astype(np.float32)

    # -------------------------------------------------------------------------
    # Attack 4: Speaker-to-Mic Re-recording Simulation
    # -------------------------------------------------------------------------
    def re_recording(self, audio: np.ndarray, room_size: str = "medium") -> np.ndarray:
        """
        Simulates physical acoustic replay on a loudspeaker captured by a phone microphone:
        - Synthetic Room Impulse Response (RIR) convolution
        - Speaker/Mic frequency coloration (120 Hz - 6.5 kHz bandpass + 3 kHz presence peak)
        - Ambient room acoustic hiss
        room_size: 'small' (RT60 ~ 200ms) | 'medium' (RT60 ~ 450ms) | 'large' (RT60 ~ 800ms)
        """
        audio = audio.astype(np.float32)
        if len(audio) < 256:
            return audio

        rt60_map = {"small": 0.20, "medium": 0.45, "large": 0.80}
        rt60 = rt60_map.get(room_size, 0.45)
        rir_len = int(self.sr * rt60)

        # Generate synthetic RIR: early reflections + decaying diffuse tail
        rng = np.random.RandomState(42)
        t = np.linspace(0, rt60, rir_len)
        decay = np.exp(-3.0 * t / (rt60 / 2.0))
        rir = rng.normal(0, 1.0, rir_len) * decay
        # Early reflections at 15ms, 25ms, 45ms
        for delay_ms, amp in [(15, 0.6), (25, 0.4), (45, 0.25)]:
            idx = int(self.sr * (delay_ms / 1000.0))
            if idx < rir_len:
                rir[idx] += amp
        # Normalize RIR
        rir = rir / (np.sum(np.abs(rir)) + 1e-9)

        # Convolve audio with RIR
        reverbed = signal.fftconvolve(audio, rir, mode='same')

        # Speaker & Mic frequency coloration:
        # Bandpass 120 Hz to 6500 Hz
        sos = signal.butter(4, [120.0, 6500.0], btype='bandpass', fs=self.sr, output='sos')
        colored = signal.sosfilt(sos, reverbed)

        # Mild presence resonance around 3 kHz
        w0 = 3000.0 / (self.sr / 2.0)
        b_res, a_res = signal.iirpeak(w0, Q=3.0)
        boosted = signal.lfilter(b_res, a_res, colored) * 0.4 + colored * 0.6

        # Room acoustic ambient noise at 26 dB SNR
        out = self.noise_mix(boosted, snr_db=26.0, noise_type="ambient")
        # Normalize amplitude
        max_val = np.max(np.abs(out)) + 1e-9
        if max_val > 0.05:
            out = out / max_val * 0.90
        return out.astype(np.float32)

    # -------------------------------------------------------------------------
    # Attack 5: Silence & Segment Splicing (Hybrid Attack)
    # -------------------------------------------------------------------------
    def splicing(
        self,
        cloned_audio: np.ndarray,
        genuine_audio: Optional[np.ndarray] = None,
        splice_ratio: float = 0.50,
        splice_mode: str = "interleaved"
    ) -> np.ndarray:
        """
        Interleaves cloned audio segments with genuine speech or silence to fool rolling median smoothing.
        splice_ratio: fraction of audio replaced with genuine/silence (e.g. 0.50 = 50% real / 50% clone)
        splice_mode: 'interleaved' | 'prefix_suffix' | 'silence_bursts'
        """
        cloned = cloned_audio.astype(np.float32)
        total_len = len(cloned)
        if total_len == 0:
            return cloned

        if genuine_audio is not None and len(genuine_audio) > 0:
            gen = genuine_audio.astype(np.float32)
            if len(gen) < total_len:
                repeats = int(np.ceil(total_len / len(gen)))
                gen = np.tile(gen, repeats)[:total_len]
            else:
                gen = gen[:total_len]
        else:
            # Fallback natural human speech waveform synthesized physiologically
            from demo_audio.generate_demo_samples import generate_natural_human_sample
            gen = generate_natural_human_sample(duration_sec=total_len / self.sr, sr=self.sr)[:total_len]

        out = np.copy(cloned)

        if splice_mode == "prefix_suffix":
            # Genuine greeting (first portion) + Cloned demand (middle) + Genuine signoff (last)
            prefix_len = int(total_len * (splice_ratio / 2.0))
            suffix_len = int(total_len * (splice_ratio / 2.0))
            if prefix_len > 0:
                out[:prefix_len] = gen[:prefix_len]
            if suffix_len > 0:
                out[-suffix_len:] = gen[-suffix_len:]

        elif splice_mode == "silence_bursts":
            # Injects low-level room silence bursts every 500ms
            seg_len = int(self.sr * 0.50)
            for i in range(0, total_len - seg_len, seg_len * 2):
                # Silence with minor room ambient hiss (-50 dB)
                out[i:i + seg_len] = np.random.normal(0, 0.003, seg_len).astype(np.float32)

        else: # 'interleaved' alternating chunks
            chunk_size = int(self.sr * 0.40) # 400ms chunks
            n_chunks = total_len // chunk_size
            for i in range(n_chunks):
                if i % 2 == 0: # Alternate real and cloned
                    start = i * chunk_size
                    end = start + chunk_size
                    out[start:end] = gen[start:end]

        return out.astype(np.float32)

attack_simulator = RedTeamAttackSimulator()
