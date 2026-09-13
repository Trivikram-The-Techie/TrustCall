"""
VoiceShield Client SDK for Python.
Enables instant integration of TrustCall voice spoofing defense into telephony servers,
IVR systems, banking gateways, and automated fraud triage bots.
"""

import os
import base64
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

class VoiceShieldClient:
    """
    Official Python client for TrustCall / VoiceShield AI detection API.
    """
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def get_health(self) -> Dict[str, Any]:
        """Checks API health and loaded neural model status."""
        url = f"{self.base_url}/health"
        req = urllib.request.Request(url, headers={"User-Agent": "VoiceShield-Python-SDK/1.0"})
        with urllib.request.urlopen(req, timeout=5) as res:
            return json.loads(res.read().decode("utf-8"))

    def score_audio_bytes(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000,
        transcript: Optional[str] = None,
        caller_metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submits raw audio bytes (WAV/PCM) for deep spoof detection and risk scoring.
        """
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        payload = {
            "audio_base64": b64_audio,
            "sample_rate": sample_rate,
            "text_transcript": transcript,
            "caller_metadata": caller_metadata or {},
            "session_id": session_id
        }

        url = f"{self.base_url}/v1/score"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "VoiceShield-Python-SDK/1.0"
            }
        )

        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))

    def score_audio_file(
        self,
        filepath: str,
        transcript: Optional[str] = None,
        is_unknown_number: bool = False
    ) -> Dict[str, Any]:
        """
        Loads a local audio file and evaluates it against the VoiceShield pipeline.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Audio file not found: {filepath}")

        with open(filepath, "rb") as f:
            audio_bytes = f.read()

        caller_meta = {
            "is_unknown_number": is_unknown_number,
            "filename": os.path.basename(filepath)
        }

        return self.score_audio_bytes(
            audio_bytes=audio_bytes,
            sample_rate=16000,
            transcript=transcript,
            caller_metadata=caller_meta
        )
