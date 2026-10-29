"""
REST API routes for Red-Team Attack Lab.
POST /v1/redteam/run
GET  /v1/redteam/presets
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.redteam.redteam_runner import run_redteam_attack

router = APIRouter(prefix="/v1/redteam", tags=["Red-Team Lab"])

class RedTeamRequest(BaseModel):
    preset_id: Optional[str] = Field(default="cloned_scam", description="'cloned_scam' or 'genuine_call'")
    audio_base64: Optional[str] = Field(default=None, description="Optional uploaded base64 WAV/PCM audio")
    attack_type: str = Field(
        default="codec_laundering",
        description="One of: 'codec_laundering', 'packet_loss', 'noise_mix', 're_recording', 'splicing'"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Attack specific parameters (e.g. codec, drop_rate, snr_db, room_size, splice_ratio)"
    )

@router.post("/run")
async def execute_redteam_attack(payload: RedTeamRequest):
    """
    Executes a red-team adversarial evasion attack on audio in-memory,
    measuring baseline detector degradation and active CUSUM/Max-Burst mitigation resilience.
    """
    valid_attacks = {"codec_laundering", "packet_loss", "noise_mix", "re_recording", "splicing"}
    if payload.attack_type not in valid_attacks:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid attack_type '{payload.attack_type}'. Must be one of: {list(valid_attacks)}"
        )

    try:
        result = run_redteam_attack(
            preset_id=payload.preset_id,
            audio_base64=payload.audio_base64,
            attack_type=payload.attack_type,
            parameters=payload.parameters
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Red-team attack execution failed: {str(e)}")

@router.get("/presets")
async def get_redteam_presets():
    """
    Returns available presets, attack types, and configurable parameter ranges for the Red-Team Lab.
    """
    return {
        "presets": [
            {
                "id": "cloned_scam",
                "label": "Preset B: Cloned Scam Sample (ElevenLabs / Diffusion Vocoder)",
                "nominal_score": 92
            },
            {
                "id": "genuine_call",
                "label": "Preset A: Genuine Human Call (Authentic Vocal Fold Dynamics)",
                "nominal_score": 14
            }
        ],
        "attack_types": [
            {
                "id": "codec_laundering",
                "name": "Lossy Codec Laundering",
                "description": "Pushes audio through telephony companding or low-bitrate psychoacoustic codecs to strip high-frequency vocoder cues.",
                "parameter_schema": {
                    "codec": {"type": "select", "options": ["amr_nb", "g711", "mp3"], "default": "amr_nb"}
                }
            },
            {
                "id": "packet_loss",
                "name": "RTP Packet Loss (PLC Decay)",
                "description": "Simulates cellular transmission drops with G.711 Appendix I packet loss concealment frame attenuation.",
                "parameter_schema": {
                    "drop_rate": {"type": "select", "options": [0.05, 0.10, 0.20], "default": 0.10}
                }
            },
            {
                "id": "noise_mix",
                "name": "Background Noise / Music Mix",
                "description": "Injects additive acoustic noise or multi-harmonic music chords at a selectable Signal-to-Noise Ratio (SNR).",
                "parameter_schema": {
                    "snr_db": {"type": "slider", "min": 5, "max": 25, "step": 5, "default": 10},
                    "noise_type": {"type": "select", "options": ["ambient", "music", "white"], "default": "ambient"}
                }
            },
            {
                "id": "re_recording",
                "name": "Speaker-to-Mic Re-recording",
                "description": "Simulates loudspeaker replay in a physical room captured by a telephone microphone (RIR reverb + coloration + room hiss).",
                "parameter_schema": {
                    "room_size": {"type": "select", "options": ["small", "medium", "large"], "default": "medium"}
                }
            },
            {
                "id": "splicing",
                "name": "Segment Splicing (Hybrid Attack)",
                "description": "Interleaves genuine speech or silence bursts with synthetic clone speech to dilute the rolling median filter.",
                "parameter_schema": {
                    "splice_ratio": {"type": "slider", "min": 0.25, "max": 0.75, "step": 0.25, "default": 0.50},
                    "splice_mode": {"type": "select", "options": ["prefix_suffix", "interleaved", "silence_bursts"], "default": "prefix_suffix"}
                }
            }
        ]
    }
