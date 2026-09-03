"""
WebSocket route for real-time live call streaming.
WS /v1/stream
Ingests streaming audio chunks (200-500ms) over WebSocket,
runs VAD, extracts features, updates rolling risk score, and streams back forensic telemetry.
"""

import json
import time
import uuid
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings
from app.audio.chunker import StreamingAudioBuffer, TemporalVoiceAccumulator
from app.audio.feature_extraction import decode_audio_bytes, decode_base64_audio, extract_acoustic_features
from app.models.spoof_detector import SpoofDetector
from app.nlp.urgency_keywords import urgency_scanner
from app.nlp.transcriber import transcriber
from app.models.risk_engine import risk_engine
from app.privacy.embedding_store import privacy_hasher, session_store

router = APIRouter(prefix="/v1", tags=["Streaming"])

@router.websocket("/stream")
async def websocket_audio_stream(websocket: WebSocket):
    """
    Real-time bidirectional WebSocket connection for live call analysis.
    Client sends binary PCM or JSON messages containing audio chunks.
    Server returns immediate risk score evaluations and alert updates.
    """
    await websocket.accept()
    
    session_id = str(uuid.uuid4())
    audio_buffer = StreamingAudioBuffer(sample_rate=settings.SAMPLE_RATE)
    voice_accumulator = TemporalVoiceAccumulator(sample_rate=settings.SAMPLE_RATE, max_duration_sec=10.0)
    # Use dedicated session detector instance for localized rolling smoothing
    session_detector = SpoofDetector()
    
    caller_meta = {}
    current_transcript = ""

    try:
        # Handshake confirmation
        await websocket.send_json({
            "event": "connected",
            "session_id": session_id,
            "message": "TrustCall live audio stream initialized",
            "sample_rate": settings.SAMPLE_RATE
        })

        while True:
            # Receive either binary audio or text JSON
            message = await websocket.receive()
            
            raw_audio = None
            if "bytes" in message and message["bytes"]:
                raw_audio = decode_audio_bytes(message["bytes"], target_sr=settings.SAMPLE_RATE)
            elif "text" in message and message["text"]:
                try:
                    payload = json.loads(message["text"])
                    event_type = payload.get("event", "audio_chunk")
                    
                    if event_type == "set_metadata":
                        caller_meta = payload.get("metadata", {})
                        continue
                    elif event_type == "transcript_update":
                        current_transcript = payload.get("transcript", "")
                        continue
                    elif "audio_base64" in payload:
                        raw_audio = decode_base64_audio(payload["audio_base64"], target_sr=settings.SAMPLE_RATE)
                        if "transcript" in payload:
                            current_transcript = payload["transcript"]
                except Exception:
                    continue

            if raw_audio is None or len(raw_audio) == 0:
                continue

            # Ingest into streaming sliding buffer
            analysis_windows = audio_buffer.add_chunk(raw_audio)
            
            for window, is_voiced, rms_energy in analysis_windows:
                now_ts = round(time.time(), 3)
                
                # If silent or unvoiced, return low quiescent score without heavy computation
                if not is_voiced:
                    await websocket.send_json({
                        "event": "score_update",
                        "session_id": session_id,
                        "timestamp": now_ts,
                        "is_voiced": False,
                        "rms_energy": rms_energy,
                        "risk_score": 12,
                        "verdict": "Low",
                        "status_text": "Ambient Silence / Monitoring",
                        "color": "#10B981",
                        "explanation": "No active speech in current window",
                        "components": {
                            "model_confidence": 5.0,
                            "spectral_discontinuity": 0.0,
                            "prosodic_irregularity": 5.0,
                            "urgency_nlp": 0.0,
                            "caller_metadata": 0.0
                        },
                        "transcript_snippet": current_transcript
                    })
                    continue

                # 1. Accumulate active voiced frames into the 10-second buffer
                voice_accumulator.add_voiced_samples(window)
                accum_stats = voice_accumulator.get_stats()
                accum_audio = voice_accumulator.get_accumulated_audio()

                # If enough audio has accumulated (>2.5s), run deep profiling on accumulated audio; else on window
                eval_audio = accum_audio if len(accum_audio) >= int(settings.SAMPLE_RATE * 2.5) else window

                # 2. Feature Extraction on Voiced Speech Window
                features = extract_acoustic_features(eval_audio, sr=settings.SAMPLE_RATE)
                
                # 3. Neural Anti-Spoofing Inference with Rolling Smoothing
                model_result = session_detector.predict_chunk(window, sr=settings.SAMPLE_RATE)
                
                # 4. Transcribe & Urgency Scan
                nlp_result = urgency_scanner.scan_text(current_transcript)
                
                # 5. Irreversible Hashing
                emb_hash = privacy_hasher.generate_hash(window)
                
                # 6. Risk Score Multi-Signal Fusion
                risk_eval = risk_engine.evaluate_risk(
                    model_result=model_result,
                    acoustic_features=features,
                    nlp_result=nlp_result,
                    caller_metadata=caller_meta
                )
                
                # 7. Ephemeral Session Record
                session_store.record_chunk_risk(
                    session_id=session_id,
                    risk_score=risk_eval["risk_score"],
                    alert_tier=risk_eval["verdict"],
                    components=risk_eval["components"],
                    explanation=risk_eval["explanation"],
                    embedding_hash=emb_hash
                )
                
                # 8. Real-Time Telemetry Payload to Client with 10-Second Accumulator & 5 Layers
                await websocket.send_json({
                    "event": "score_update",
                    "session_id": session_id,
                    "timestamp": now_ts,
                    "is_voiced": True,
                    "rms_energy": rms_energy,
                    "risk_score": risk_eval["risk_score"],
                    "verdict": risk_eval["verdict"],
                    "status_text": risk_eval["status_text"],
                    "color": risk_eval["color"],
                    "action_recommendation": risk_eval["action_recommendation"],
                    "explanation": risk_eval["explanation"],
                    "forensic_reasons": risk_eval["forensic_reasons"],
                    "components": risk_eval["components"],
                    "contributions": risk_eval["contributions"],
                    "transcript_snippet": current_transcript,
                    "embedding_hash": emb_hash,
                    "accumulator": accum_stats,
                    "layers": risk_eval.get("layers", {})
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"event": "error", "message": str(e)})
        except Exception:
            pass
