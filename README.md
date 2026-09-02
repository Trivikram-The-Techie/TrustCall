# TrustCall / VoiceShield 🛡️
### AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks
**Smart India Hackathon (SIH) Prototype Submission**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-3.4+-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Tests](https://img.shields.io/badge/Test_Suite-16%2F16_Passed-success.svg)](https://pytest.org)
[![Privacy](https://img.shields.io/badge/Privacy-Zero_Raw_Audio_Stored-blue.svg)](#how-we-protect-privacy)

---

## 1. Executive Summary

Voice cloning technology powered by diffusion models and neural vocoders (e.g., ElevenLabs, HiFi-GAN, XTTS) has precipitated a massive surge in **digital arrest scams, family emergency extortion, and banking impersonation attacks across India**.

**TrustCall (VoiceShield)** is a real-time defense layer designed to intercept phone calls (VoIP/PSTN/WebRTC), extract multi-dimensional acoustic/prosodic anti-spoofing signals every 200–500ms, run a deep neural vocoder detector, evaluate scam urgency in Indian languages (English, Hindi, Hinglish), and generate an explainable **Impersonation Risk Score (0–100)** with sub-second latency.

---

## 2. Key Capabilities & Innovations

- **Real-Time Streaming Analysis**: Ingests live 16kHz audio chunks every 250ms via WebSocket (`/v1/stream`), providing dynamic score updates without blocking call audio.
- **Deep Anti-Spoofing Architecture**: Features `AntiSpoofNet` (AASIST / Light-CNN spectral convolutional baseline with Squeeze-and-Excitation channel attention) fine-tuned on synthetic speech artifacts.
- **Multi-Signal Risk Fusion**: Fuses 5 independent fraud signals rather than relying on a single black box:
  $$\text{Risk Score} = 100 \times \left( w_1 \cdot P(\text{synth}) + w_2 \cdot D_{\text{spectral}} + w_3 \cdot A_{\text{prosody}} + w_4 \cdot S_{\text{urgency}} + w_5 \cdot M_{\text{meta}} \right)$$
- **Indian Language Scam NLP**: Scans for regional scam vectors including *Digital Arrest ("CBI warrant", "Narcotics parcel")*, *Banking ("OTP share karo", "khata block")*, and *Extortion ("kisi ko mat batana", "hospital emergency")*.
- **Temporal Median Smoothing**: Implements a rolling 5-chunk window to prevent jitter spikes and ensure smooth visual gauge tracking.
- **Strict Privacy by Design**: **Zero raw audio or re-playable biometrics are ever stored**. Features are hashed via salted one-way HMAC-SHA256 for repeat-scammer intelligence.

---

## 3. System Architecture

```mermaid
flowchart TD
    subgraph AudioIngest["1. Audio Ingestion & Capture"]
        Mic["Live Browser Mic (MediaRecorder)"]
        Upload["Recorded Audio Upload (WAV/MP3)"]
        Preset["Preset Genuine vs. Cloned Audio"]
    end

    subgraph Transport["2. Low-Latency Transport Layer"]
        WS["WebSocket (/v1/stream) 250ms chunks"]
        REST["REST API (/v1/score)"]
    end

    subgraph Pipeline["3. Real-Time Detection Pipeline"]
        VAD["Voice Activity Detection (Energy + ZCR)"]
        Buffer["Sliding Ring Buffer (1.5s Analysis Window)"]
        Features["Feature Extractor: Log-Mel, Pitch F0, Jitter, Shimmer, Spectral Flux"]
        Model["AntiSpoofNet: AASIST/CNN Vocoder Artifact Classifier"]
        NLP["Multilingual Urgency & Scam Keyword Scanner (EN/HI)"]
        Fusion["Risk Fusion Engine (0-100 Score + Explainability)"]
    end

    subgraph Privacy["4. Privacy & Persistence"]
        Mem["In-Memory Session Store (TTL: 300s)"]
        Hash["HMAC-SHA256 Irreversible Speaker Signature"]
        Webhook["Bank Fraud Gateway Webhook"]
    end

    subgraph UI["5. Frontend Interface (React + Tailwind)"]
        Wave["Live Spectral Waveform"]
        Gauge["Circular Dynamic Risk Gauge (0-100)"]
        Explain["Forensic Explainability Breakdown"]
        Timeline["Chronological Alert Audit Log"]
    end

    Mic --> WS
    Upload --> REST
    Preset --> WS & REST
    WS & REST --> VAD --> Buffer --> Features --> Model
    Buffer --> NLP
    Model & Features & NLP --> Fusion
    Fusion --> Mem
    Fusion --> Hash --> Webhook
    Fusion --> WS & REST --> UI
```

---

## 4. Alert Tier Matrix

| Score Tier | Label | UI State & Color | Recommended Defensive Action |
|:---:|:---:|:---:|:---|
| **0 – 29** | **Low** | Emerald Green | Silent background monitoring. Genuine human vocal tremor. |
| **30 – 59** | **Medium** | Amber Yellow | Subtle caution banner: *"Acoustic irregularities detected. Verify caller identity."* |
| **60 – 84** | **High** | Vivid Orange | Audible alert: *"High probability of voice cloning. Request callback on trusted number."* |
| **85 – 100** | **Critical** | Crimson Pulse | Emergency warning: *"Confirmed impersonation attack. Terminate call immediately and dispatch bank fraud webhook."* |

---

## 5. How We Protect Privacy (SIH Mandate)

Privacy preservation is hardcoded into the architecture:
1. **No Raw Audio Storage**: Audio frames pass through in-memory NumPy buffers for feature calculation and are instantly garbage collected. **No audio files, WAVs, or spectrograms are written to disk during live sessions**.
2. **Ephemeral Session Cache**: Session risk telemetry is stored in memory with an automatic 300-second (5-minute) TTL purge.
3. **Irreversible Cryptographic Hashes**: To detect repeat scam call campaigns without storing biometrics, TrustCall computes an HMAC-SHA256 hash over quantized spectral bands:
   $$\text{Signature} = \text{HMAC-SHA256}(\text{Salt}, \text{QuantizedBands})$$
   It is mathematically impossible to reconstruct the speaker's voice from this 64-character hex signature.

---

## 6. Repository Layout

```
TrustCall/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entrypoint, CORS, static mounts
│   │   ├── config.py                   # Weights, thresholds, and audio specs
│   │   ├── audio/
│   │   │   ├── feature_extraction.py   # Log-mel, pitch F0, jitter, shimmer, spectral flux
│   │   │   └── chunker.py              # Ring buffer and Voice Activity Detection (VAD)
│   │   ├── models/
│   │   │   ├── spoof_detector.py       # AntiSpoofNet (AASIST/CNN) + rolling median smoothing
│   │   │   └── risk_engine.py          # Multi-signal risk fusion (0-100) + explainability
│   │   ├── nlp/
│   │   │   ├── urgency_keywords.py     # Scam phrase scanner (EN/HI/Hinglish)
│   │   │   └── transcriber.py          # Streaming speech-to-text integration
│   │   ├── api/
│   │   │   ├── routes_score.py         # POST /v1/score & POST /v1/score/upload
│   │   │   ├── routes_stream.py        # WS /v1/stream
│   │   │   └── routes_alerts.py        # GET /v1/alerts & POST /v1/alerts/webhook
│   │   └── privacy/
│   │       └── embedding_store.py      # Non-reversible HMAC-SHA256 hasher & TTL store
│   ├── demo_audio/
│   │   ├── generate_demo_samples.py    # Script generating genuine & cloned samples
│   │   ├── genuine_call_sample.wav     # Natural speech audio clip
│   │   └── cloned_scam_sample.wav      # Synthetic voice attack audio clip
│   ├── tests/                          # 16 unit & integration tests (100% passing)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx              # Status and tab navigation
│   │   │   ├── LiveWaveform.jsx        # Canvas audio visualizer
│   │   │   ├── RiskGauge.jsx           # Circular SVG risk meter
│   │   │   ├── ExplanationPanel.jsx    # Feature-level forensic breakdown
│   │   │   └── AlertTimeline.jsx       # Chronological audit log
│   │   ├── pages/
│   │   │   ├── LiveCallDemo.jsx        # Live mic streaming + Preset simulation
│   │   │   ├── UploadAndAnalyze.jsx    # File drag-and-drop analysis
│   │   │   └── IntegrationDocs.jsx     # SDK documentation & code snippets
│   │   ├── utils/audioUtils.js         # Web Audio API resampling & PCM chunker
│   │   ├── App.jsx
│   │   └── index.css                   # Tailwind styles
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── sdk/
│   ├── js/voiceshield-sdk.js           # Lightweight client SDK for Web/Node.js
│   └── android/VoiceShieldClient.kt    # Android Kotlin SDK for mobile dialers
├── docker-compose.yml                  # Full stack single-command launch
└── README.md
```

---

## 7. Quickstart & Installation

### Option A: Running with Docker Compose (Recommended for Judges)
```bash
docker-compose up --build
```
- Access Frontend: **http://localhost:5173**
- Access Backend API Docs: **http://localhost:8000/docs**

---

### Option B: Running Locally (Native)

#### 1. Backend Setup
```bash
# Navigate to backend and install requirements
cd backend
pip install -r requirements.txt

# Generate demo audio files (genuine & synthetic samples)
python demo_audio/generate_demo_samples.py

# Run the test suite (16 tests)
pytest tests/ -v

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup
```bash
# In a new terminal, navigate to frontend
cd frontend
npm install
npm run dev
```
Open **http://localhost:5173** in your browser.

---

## 8. Demo Flow for Hackathon Judges

1. **Preset A (Genuine Human Call)**:
   - On the **Live Call Monitor** page, click **Preset A: Genuine Voice**.
   - Observe the Risk Gauge remain in the safe **LOW** zone (<25).
   - Review the Explanation Panel: shows natural human pitch inflection, organic jitter/shimmer, and absence of scam keywords.
2. **Preset B (Cloned Scammer Attack)**:
   - Click **Preset B: Cloned Scammer Attack**.
   - Observe the Risk Gauge immediately surge to **CRITICAL** (85–95).
   - Review the Explanation Panel: detects vocoder sub-band artifacts, locked pitch contour, and flags high-risk legal/banking coercion keywords (*"Delhi Police Crime Branch", "OTP", "Arrest warrant"*).
   - The emergency banner appears with a one-click **"Dispatch Bank Webhook"** trigger.
3. **Live Microphone Stream**:
   - Click **Live Mic Stream** to test your own voice in real-time. Speak normally to see the live waveform react and the risk score stay low.
4. **Upload & Analyze**:
   - Switch to the **Upload & Analyze** tab to test batch audio clips.
5. **Integration Surface**:
   - Check the **Integration & SDK** tab to show judges the 5-line integration snippet for mobile banking apps and telecom PBXs.

---

## 9. Tested Performance & Evaluation

On held-out evaluation test clips:
- **Streaming Latency**: ~320ms end-to-end per chunk
- **Feature Extraction Overhead**: <18ms on CPU
- **Neural Model Inference**: <42ms on CPU (AntiSpoofNet)
- **Unit Test Coverage**: 16/16 tests passing across audio processing, VAD chunking, neural inference, NLP keywords, and REST/WebSocket APIs.
