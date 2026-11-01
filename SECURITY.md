# Security Policy & Threat Model — TrustCall / VoiceShield 🛡️

TrustCall / VoiceShield is an enterprise-grade AI defense platform designed to intercept real-time voice clone impersonation attacks on telecom and banking infrastructure. This document outlines our threat model, asset classification, attack surface analysis, vulnerability disclosure policy, and mitigation architecture.

---

## 1. Threat Model & Security Posture

### 1.1 Protected Assets

| Asset Classification | Description | Confidentiality | Integrity | Availability | Retention Period |
|---|---|---|---|---|---|
| **Raw Voice Audio** | Ingested streaming audio frames from microphone or telephony SIP trunks | **CRITICAL** | High | High | **0 ms (Never stored on disk)** |
| **Speaker Embeddings** | Ephemeral feature vectors (Log-Mel, MFCC, Pitch F0) | High | High | Medium | **1.5s sliding RAM buffer** |
| **Speaker Signatures** | Salted one-way HMAC-SHA256 hashes for repeat scammer detection | Medium | **CRITICAL** | Medium | 300s ephemeral session TTL |
| **Fraud Risk Scores** | 0–100 calibrated risk evaluation and alert tier | Medium | **CRITICAL** | High | Ephemeral session cache |
| **Audit Certificates** | Tamper-proof Section 65B forensic audit certificates | Low (Publicly verify) | **CRITICAL** | High | Downloaded by user / SOC |
| **API & Webhook Keys** | Cryptographic secrets for core banking HMAC dispatch | **CRITICAL** | **CRITICAL** | High | Environment variables only |

---

### 1.2 Threat Actors & Adversary Profiles

1. **Organized Cybercrime Syndicates ("Digital Arrest" & Extortion Rings)**:
   - *Motivation*: High-value financial extortion, coercive bank transfers.
   - *Capabilities*: Automated cloud TTS pipelines, VoIP caller ID spoofing, offshore SIP trunks, rapid SIM-box churn.
2. **Acoustic Adversarial Attackers**:
   - *Motivation*: Evade machine learning detectors by injecting adversarial perturbation, adding background acoustic masks, or laundering audio through codecs.
   - *Capabilities*: PyTorch/DSP knowledge, audio manipulation tools, ffmpeg pipelines.
3. **Automated Robocall / Telephony Botnets**:
   - *Motivation*: High-throughput scanning for vulnerable victims via burst dialing.
   - *Capabilities*: High-concurrency SIP autodialers, randomized caller IDs.
4. **Malicious Intermediaries / Man-in-the-Middle (MitM)**:
   - *Motivation*: Replaying legitimate authorization tokens or snooping user calls.
   - *Capabilities*: Local network sniffing, rogue Wi-Fi access points.

---

### 1.3 Red-Team Attack Lab Vectors & Defensive Mitigations

The TrustCall Red-Team Lab (`/v1/redteam`) continuously assesses detector robustness against 5 primary evasion attacks:

```
[Adversary Attack Pipeline] ──> [Red-Team Lab Stress Engine] ──> [Active Mitigation Defense]
  ├── 1. Codec Laundering       ├── G.711 / AMR / MP3         ├── Codec Normalizer & Comb Analysis
  ├── 2. Packet Loss Evasion    ├── 5% / 10% / 20% Drop       ├── PLC Concealment Disambiguator
  ├── 3. Noise / Music Mix      ├── 20 / 10 / 5 dB SNR        ├── Jitter Stability & Energy VAD
  ├── 4. Re-recording Sim       ├── Reverb + Mic Impulse      ├── Room Transfer Subtraction
  └── 5. Hybrid Splicing        ├── Real + Cloned Segments    └── CUSUM Max-Burst Aggregator
```

#### Vector 1: Codec Laundering (G.711 $\mu$-law, AMR-NB, MP3 Round-Trip)
- **Attack**: Running synthetic speech through lossy telecom codecs bandlimits frequencies ($300\text{--}3,400\text{ Hz}$) and introduces quantization noise, attempting to wash away neural vocoder phase artifacts.
- **Mitigation**: Telephony Codec Normalizer with adaptive bandpass equalization and high-frequency comb-ripple harmonic reconstruction.

#### Vector 2: Packet Loss Concealment (PLC) Evasion (5%, 10%, 20% Random Drops)
- **Attack**: Simulating bad cellular connectivity so frame drops create phase discontinuities that resemble splice boundaries, causing false alarms or masking clone glitches.
- **Mitigation**: PLC Disambiguation engine detects RTP frame interpolation and energy attenuation envelopes to distinguish organic cellular packet loss from generative vocoder boundaries.

#### Vector 3: Background Noise & Music Mixing (20 dB, 10 dB, 5 dB SNR)
- **Attack**: Adding street traffic, cafeteria noise, or loud music to drown out robotic pitch flatness and micro-jitter anomalies.
- **Mitigation**: Spectral subtraction pre-filtering combined with vocal fold fundamental frequency ($F_0$) trajectory tracking that operates independently of ambient noise floor.

#### Vector 4: Speaker-to-Mic Re-recording (Reverberation + Bandlimit + Acoustic Noise)
- **Attack**: Playing cloned audio through a cheap loudspeaker into a physical microphone, adding physical room reverb to mask dry digital artifacts.
- **Mitigation**: Early-to-late reverberation energy ratio ($C_{50}$) estimation and inverse room impulse response deconvolution.

#### Vector 5: Hybrid Splicing / Burst Insertion
- **Attack**: Alternating genuine human speech (e.g., "Hello, yes...") with brief 1–2 second cloned bursts containing coercive commands, attempting to hide under the median smoothing window.
- **Mitigation**: Two-tier **CUSUM (Cumulative Sum) Anomaly Aggregator** and Max-Window detector running alongside median smoothing. Any transient synthetic burst $>0.80$ immediately trips the high-alert threshold without waiting for window decay.

---

## 2. Platform Security Architecture

### 2.1 Privacy by Design (DPDP Act 2023 Compliance)
- **Zero Raw Audio Persisted**: Audio chunks stream exclusively through ephemeral RAM buffers (1.5s sliding window). Once features are extracted, the raw audio buffer is immediately zeroed and deallocated.
- **No Biometric Inversion**: Speaker identity is stored solely as a one-way HMAC-SHA256 hash incorporating a private cryptographic salt (`SALT_KEY`). The raw voice cannot be reconstructed from the signature.
- **Data Minimization**: In accordance with Section 6 of the Digital Personal Data Protection (DPDP) Act 2023, only non-personal acoustic variance metrics and mathematical features are processed.
- **Instant Erasure**: On WebSocket disconnect or call termination, all in-memory session frames are wiped.

---

### 2.2 Transport & HTTP Security Headers
All web traffic across frontend (Vercel) and backend (FastAPI) enforces strict enterprise security headers:

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; media-src 'self' blob: data:; connect-src 'self' ws: wss: http: https:; font-src 'self' data:; frame-ancestors 'none';
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: microphone=(self), camera=(), geolocation=()
```

- **CSP Exception Justification**:
  - `style-src 'unsafe-inline'`: Required for React dynamic styling and Tailwind CSS runtime classes.
  - `script-src 'wasm-unsafe-eval'`: Required for WebAssembly audio worklets, ONNX Web Runtime, and high-frequency in-browser client DSP.
  - `frame-ancestors 'none'` / `X-Frame-Options: DENY`: Prevents clickjacking by forbidding embedding in iframes.
  - `Permissions-Policy: microphone=(self)`: Grants microphone access exclusively to the TrustCall application origin, blocking third-party iframes from eavesdropping.

---

### 2.3 Rate Limiting & DoS Prevention
In-memory sliding-window rate limiters protect compute-heavy neural endpoints:
- `POST /v1/score`: 60 requests / minute per IP or API key.
- `POST /v1/redteam/run`: 20 requests / minute per IP or API key.
- `WS /v1/stream`: 30 connection handshakes / minute per IP.
Exceeding limits triggers an HTTP `429 Too Many Requests` response with a `Retry-After` header.

---

### 2.4 Upload Constraints & Constrained Decoding
To prevent memory exhaustion, decompression bombs, and malformed buffer crashes:
- **Max Upload Size**: 15 MB (`15,728,640` bytes). Larger payloads rejected with HTTP `413 Payload Too Large`.
- **Max Audio Duration**: 120 seconds ($16\text{ kHz} \times 120 = 1,920,000$ samples max). Decoded buffers are strictly bounded.
- **Allowed MIME Types**: `audio/wav`, `audio/mpeg`, `audio/mp3`, `audio/ogg`, `audio/flac`, `audio/webm`, `audio/x-m4a`, `audio/mp4`, `audio/aac`. Disallowed types rejected with HTTP `415 Unsupported Media Type`.
- **Constrained Decoding**: RIFF magic byte verification, framerate sanity bounds ($4,000 \le sr \le 192,000$), channel bounds ($\le 2$), buffer multiple checks, and automatic `NaN`/`Inf` sanitization to prevent unhandled float exceptions.

---

### 2.5 Webhook Cryptographic Verification & Replay Protection
Alert dispatches to core banking systems utilize RFC-2104 HMAC-SHA256 signatures:
```
Header: X-VoiceShield-Signature: t={timestamp},v1={hmac_sha256},nonce={uuid}
```
1. **Timestamp Tolerance**: Discards any webhook payload with timestamp skew $>300\text{ seconds}$ to defeat stale message replay.
2. **Nonce Store**: Unique cryptographic nonces are recorded in an in-memory TTL cache. Re-submitting a previously consumed nonce immediately triggers verification rejection.
3. **Constant-Time Comparison**: Signatures are compared via `hmac.compare_digest()` to eliminate timing attack side-channels.

---

## 3. Residual Risks & Operational Limitations

1. **Live Human-in-the-Loop Voice Morphing**:
   - *Risk*: A human scammer speaking through an ultra-low-latency physical voice converter in real-time.
   - *Mitigation*: Our dynamic out-of-band challenge-response protocol measures cognitive response latency. However, a skilled human operator may answer correctly within acceptable latency windows.
2. **Analog Handset Wiretapping**:
   - *Risk*: Physical compromise of the victim's local handset microphone hardware before audio enters the telecom or browser stack.
   - *Mitigation*: Out of scope for application-layer software; requires hardware-level cryptographic attestation (e.g., Android Keystore / Apple Secure Enclave).

---

## 4. Vulnerability Disclosure Policy

If you discover a security vulnerability in TrustCall / VoiceShield:
1. **Do NOT open a public GitHub issue**.
2. Email full technical details and reproduction steps to the security team at:
   `security@trustcall.internal` or `trivikram.techie@gmail.com`.
3. Include:
   - Vulnerability category (e.g. rate limit bypass, replay attack, memory exhaustion)
   - Step-by-step reproduction script or curl command
   - Expected vs observed behavior
4. **SLA**: We acknowledge reports within **24 hours** and aim to release patches within **72 hours** for high or critical vulnerabilities.
