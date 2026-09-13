"""
TrustCall / VoiceShield CLI
Command-line forensic audio scanner powered by pre-trained AASIST-L.
Usage:
  python cli.py scan <audio_path> [--transcript "text"] [--json]
  python cli.py health
"""

import sys
import os
import argparse
import json
import time

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.audio.feature_extraction import extract_acoustic_features
from app.models.spoof_detector import spoof_detector
from app.nlp.urgency_keywords import urgency_scanner
from app.models.risk_engine import risk_engine
from app.privacy.embedding_store import privacy_hasher
from app.models.vocoder_fingerprint import vocoder_fingerprinter
import soundfile as sf
import numpy as np

def print_banner():
    print(r"""
========================================================================
   ____             __  _____     ____
  |_   _|____ _   _/ /_/ ___/__ _/ / /
    | |/ __/ // / / __/ /__/ _ `/ / / 
    |_/_/  \_,_/_/\__/\___/\_,_/_/_/  
  VoiceShield AI Voice Clone Forensic Scanner
========================================================================
""")

def scan_file(filepath: str, transcript: str = None, as_json: bool = False):
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' does not exist.", file=sys.stderr)
        sys.exit(1)

    audio, sr = sf.read(filepath)
    if len(audio.shape) > 1:
        audio = audio[:, 0]
    audio = audio.astype(np.float32)

    t0 = time.perf_counter()
    
    # 1. Acoustic Features
    features = extract_acoustic_features(audio, sr=sr)
    
    # 2. AASIST-L Model Inference
    model_res = spoof_detector.predict_chunk(audio, sr=sr, use_history=False)
    
    # 3. Urgency NLP
    nlp_res = urgency_scanner.scan_text(transcript or "")
    
    # 4. Multi-Signal Fusion
    risk_res = risk_engine.evaluate_risk(
        model_result=model_res,
        acoustic_features=features,
        nlp_result=nlp_res,
        caller_metadata={"filename": os.path.basename(filepath)}
    )
    
    # 5. Vocoder Fingerprint
    fingerprint = vocoder_fingerprinter.analyze_audio_fingerprint(
        audio=audio,
        acoustic_features=features,
        spoof_probability=model_res["raw_probability"]
    )
    
    # 6. Irreversible Speaker Hash
    speaker_hash = privacy_hasher.generate_hash(audio)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    result = {
        "file": filepath,
        "sample_rate": sr,
        "duration_sec": round(len(audio) / sr, 2),
        "risk_score": risk_res["risk_score"],
        "verdict": risk_res["verdict"],
        "status_text": risk_res["status_text"],
        "action_recommendation": risk_res["action_recommendation"],
        "model_confidence": round(model_res["raw_probability"] * 100, 2),
        "primary_architecture": fingerprint["primary_architecture"],
        "forensic_reasons": risk_res["forensic_reasons"],
        "speaker_hash": speaker_hash,
        "elapsed_ms": round(elapsed_ms, 1)
    }

    if as_json:
        print(json.dumps(result, indent=2))
        return

    print_banner()
    print(f"File Analyzed      : {filepath} ({result['duration_sec']}s @ {sr}Hz)")
    print(f"Latency            : {result['elapsed_ms']} ms")
    print(f"Risk Score         : {result['risk_score']} / 100 [{result['verdict'].upper()}]")
    print(f"Status             : {result['status_text']}")
    print(f"Recommendation     : {result['action_recommendation']}")
    print(f"AASIST-L Conf      : {result['model_confidence']}% synthetic likelihood")
    print(f"Vocoder Match      : {result['primary_architecture']}")
    print(f"HMAC Speaker Hash  : {result['speaker_hash']}")
    print("\nForensic Observations:")
    for reason in result["forensic_reasons"]:
        print(f"  - {reason}")
    print("=" * 72 + "\n")

def check_health():
    print(json.dumps({
        "status": "healthy",
        "neural_model": "AntiSpoofNet (AASIST-L Pre-Trained Deep Graph Attention)",
        "nlp_scanner": "Multilingual Urgency Engine (EN/HI)",
        "privacy_compliance": "Zero-Raw-Audio-Persisted"
    }, indent=2))

def main():
    parser = argparse.ArgumentParser(description="TrustCall VoiceShield CLI Scanner")
    subparsers = parser.add_subparsers(dest="command")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan an audio file for voice cloning")
    scan_parser.add_argument("file", help="Path to WAV audio file")
    scan_parser.add_argument("--transcript", "-t", default=None, help="Text transcript for scam scanning")
    scan_parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    # Health command
    subparsers.add_parser("health", help="Check detection engine health")

    args = parser.parse_args()
    if args.command == "scan":
        scan_file(args.file, transcript=args.transcript, as_json=args.json)
    elif args.command == "health":
        check_health()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
