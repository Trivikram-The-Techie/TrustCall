"""
Configuration settings for TrustCall / VoiceShield.
Defines signal weights, alert thresholds, and audio processing parameters.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "TrustCall / VoiceShield"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Audio Specs
    SAMPLE_RATE: int = 16000           # Standard 16 kHz mono
    CHUNK_DURATION_SEC: float = 0.25   # Incoming streaming chunk duration (250ms)
    ANALYSIS_WINDOW_SEC: float = 1.5   # Window size for neural & spectral analysis
    OVERLAP_RATIO: float = 0.5         # 50% overlap for rolling window analysis
    
    # VAD Parameters
    VAD_ENERGY_THRESHOLD: float = 0.008 # Minimum RMS energy for active speech
    VAD_ZCR_THRESHOLD: float = 0.02    # Minimum zero-crossing rate
    
    # Risk Fusion Weights (Sum = 1.0)
    # risk_score = 100 * (w1 * model + w2 * spectral + w3 * prosody + w4 * urgency + w5 * metadata)
    WEIGHT_SPOOF_MODEL: float = 0.45    # Neural anti-spoofing confidence
    WEIGHT_SPECTRAL_FLUX: float = 0.15  # Spectral discontinuity & splice flags
    WEIGHT_PROSODIC: float = 0.15       # Pitch contour unnaturalness, jitter/shimmer
    WEIGHT_URGENCY_NLP: float = 0.15    # Financial / legal coercion keywords
    WEIGHT_CALLER_META: float = 0.10    # Spoofed caller ID / anomaly flag
    
    # Alert Tiers (0-100)
    THRESHOLD_LOW: int = 30        # <30: Low (Normal, silent monitoring)
    THRESHOLD_MEDIUM: int = 60     # 30-60: Medium (Caution, identity verification advised)
    THRESHOLD_HIGH: int = 85       # 60-85: High (Impersonation likely, audible warning)
    # >85: Critical (Definite attack, recommend call termination & bank webhook)
    
    # Privacy & Session Cache
    SESSION_TTL_SECONDS: int = 300      # 5 minutes in-memory TTL
    SALT_KEY: str = "trustcall_sih2024_irreversible_salt_vector"
    
    # Rolling smoothing window size
    ROLLING_WINDOW_CHUNKS: int = 5

    # Phase 4: Two-Stage Cascade & Scalability Settings
    ENABLE_CASCADE: bool = True
    CASCADE_STAGE1_THRESHOLD: float = 0.35      # Screening gate threshold triggering Stage 2
    CASCADE_PERIODIC_INTERVAL: int = 10         # Background periodic surveillance (every K chunks)
    CASCADE_FAIL_OPEN_TIMEOUT_MS: float = 150.0 # Strict fail-open budget (ms) for telecom safety
    SESSION_STORE_BACKEND: str = "memory"       # "memory" | "redis"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Phase 5: Metadata Signal Sub-Weights (must sum to 1.0 within the metadata component)
    META_WEIGHT_NUMBER_REPUTATION: float = 0.35   # Blocklist hit
    META_WEIGHT_CALL_BURST_VELOCITY: float = 0.25  # Calls-per-window burst
    META_WEIGHT_SHORT_REPEAT_CALLS: float = 0.20   # Repeated very short calls
    META_WEIGHT_VOIP_PREFIX: float = 0.20           # VoIP gateway prefix detection

    # Phase 5: Velocity / burst thresholds
    CALL_BURST_WINDOW_SEC: int = 300             # 5-minute rolling window
    CALL_BURST_THRESHOLD: int = 4                # >4 calls in window = burst
    SHORT_CALL_THRESHOLD_SEC: int = 15           # Calls under 15 s = short

    # Phase 5: Known VoIP prefixes (US + Indian non-geo ranges for demo)
    VOIP_PREFIXES: list = [
        "1646", "1347", "1929", "1212", "1718",
        "91140", "9161", "91180", "91720",
    ]

    # Phase 5: Intent Classifier
    INTENT_CLASSIFIER_ENABLED: bool = True
    INTENT_CLASSIFIER_THRESHOLD: float = 0.10   # min cosine similarity to flag

    # Phase 5: Trusted Contact Alert (mock / SIMULATED DEMO)
    TRUSTED_CONTACT_MOCK_NUMBER: str = "+91 9876543210"
    TRUSTED_CONTACT_MOCK_NAME: str = "Family Contact (Demo)"
    BANK_WEBHOOK_DEMO_HOLD_AMOUNT: str = "₹50,000"

    # Phase 6: Security Hardening & Controls
    # Rate Limiting (requests per minute per IP / API key)
    RATE_LIMIT_SCORE_PER_MIN: int = 60
    RATE_LIMIT_REDTEAM_PER_MIN: int = 20
    RATE_LIMIT_STREAM_PER_MIN: int = 30

    # Upload Constraints & Safeguards
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB max
    MAX_AUDIO_DURATION_SEC: float = 120.0          # 120 seconds max audio
    ALLOWED_AUDIO_MIME_TYPES: list = [
        "audio/wav", "audio/x-wav", "audio/wave",
        "audio/mpeg", "audio/mp3", "audio/ogg",
        "audio/flac", "audio/webm", "audio/x-m4a",
        "audio/mp4", "audio/aac", "audio/basic"
    ]

    # Webhook Verification & Nonce Store
    WEBHOOK_SECRET: str = "trustcall_default_webhook_hmac_secret_key"
    WEBHOOK_TIMESTAMP_TOLERANCE_SEC: int = 300  # 5 minutes replay window

    # API Key Authentication for non-demo routes
    API_KEY_AUTH_ENABLED: bool = False
    API_KEYS: list = [
        "trustcall-admin-key-2024",
        "trustcall-demo-key-2024"
    ]

    # CORS Restricted Origins
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://trivikram-the-techie.github.io"
    ]

    model_config = SettingsConfigDict(env_prefix="TRUSTCALL_")

settings = Settings()
