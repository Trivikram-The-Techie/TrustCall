"""
Unit tests for CLI scanner and Python SDK client.
"""

import os
import sys
import pytest

# Ensure backend and sdk are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from cli import scan_file, check_health
from sdk.python.voiceshield import VoiceShieldClient

def test_cli_scan_demo_audio(capsys):
    demo_wav = os.path.join(os.path.dirname(__file__), "..", "demo_audio", "cloned_scam_sample.wav")
    assert os.path.exists(demo_wav)

    scan_file(demo_wav, transcript="CBI police arrest warrant transfer money", as_json=True)
    captured = capsys.readouterr()
    assert "risk_score" in captured.out
    assert "verdict" in captured.out
    assert "speaker_hash" in captured.out
    assert "model_confidence" in captured.out

def test_cli_health(capsys):
    check_health()
    captured = capsys.readouterr()
    assert "healthy" in captured.out
    assert "AntiSpoofNet" in captured.out

def test_python_sdk_initialization():
    client = VoiceShieldClient(base_url="http://localhost:8000")
    assert client.base_url == "http://localhost:8000"
