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

    model_config = SettingsConfigDict(env_prefix="TRUSTCALL_")

settings = Settings()
