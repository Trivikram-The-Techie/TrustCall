"""
Multi-signal Risk Fusion Engine for TrustCall / VoiceShield.
Combines:
1. Neural spoof detector confidence (AASIST/CNN)
2. Spectral discontinuity and splice artifacts
3. Prosodic anomalies (pitch contour flatness, jitter/shimmer distortion)
4. NLP scam & urgency keyword triggers (multilingual EN/HI)
5. Caller metadata risk (spoofed caller ID, unusual timing)
Generates an explainable 0-100 Impersonation Risk Score and tiered alerts.
"""

from typing import Dict, Any, Optional
from app.config import settings

class RiskFusionEngine:
    """
    Fuses multiple independent fraud signals into a single calibrated 0-100 risk score
    with granular feature-level explainability.
    """
    def __init__(self):
        self.w_model = settings.WEIGHT_SPOOF_MODEL
        self.w_spectral = settings.WEIGHT_SPECTRAL_FLUX
        self.w_prosody = settings.WEIGHT_PROSODIC
        self.w_nlp = settings.WEIGHT_URGENCY_NLP
        self.w_meta = settings.WEIGHT_CALLER_META

    def evaluate_risk(
        self,
        model_result: Dict[str, Any],
        acoustic_features: Dict[str, Any],
        nlp_result: Dict[str, Any],
        caller_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates risk score and constructs forensic explainability breakdown.
        """
        # 1. Neural Model Signal [0.0 - 1.0]
        model_prob = model_result.get("smoothed_probability", 0.0)
        
        # 2. Spectral Discontinuity Signal [0.0 - 1.0]
        spectral_data = acoustic_features.get("discontinuity", {})
        spectral_score = spectral_data.get("discontinuity_score", 0.1)
        
        # 3. Prosodic Anomaly Signal [0.0 - 1.0]
        prosody_score = acoustic_features.get("prosodic_spoof_score", 0.15)
        
        # 4. Scam Urgency NLP Signal [0.0 - 1.0]
        nlp_score = nlp_result.get("urgency_score", 0.0)
        
        # 5. Caller Metadata Risk [0.0 - 1.0]
        meta_score = 0.0
        if caller_metadata:
            if caller_metadata.get("is_unknown_number", False):
                meta_score += 0.4
            if caller_metadata.get("is_voip_spoofed", False):
                meta_score += 0.5
            if caller_metadata.get("country_mismatch", False):
                meta_score += 0.3
            meta_score = min(1.0, meta_score)

        # Weighted Linear Fusion
        raw_weighted_sum = (
            (self.w_model * model_prob) +
            (self.w_spectral * spectral_score) +
            (self.w_prosody * prosody_score) +
            (self.w_nlp * nlp_score) +
            (self.w_meta * meta_score)
        )
        
        # Scale to 0-100
        risk_score = int(round(np_clip(raw_weighted_sum * 100.0, 0.0, 100.0)))
        
        # Tier classification
        if risk_score < settings.THRESHOLD_LOW:
            verdict = "Low"
            status_text = "Authentic Voice Detected"
            color = "#10B981"  # Emerald Green
            action_recommendation = "Silent monitoring. No threats detected."
        elif risk_score < settings.THRESHOLD_MEDIUM:
            verdict = "Medium"
            status_text = "Acoustic Irregularities"
            color = "#F59E0B"  # Amber / Yellow
            action_recommendation = "Verify identity. Subtle voice synthesis artifacts detected."
        elif risk_score < settings.THRESHOLD_HIGH:
            verdict = "High"
            status_text = "Probable Voice Clone"
            color = "#F97316"  # Orange
            action_recommendation = "Warning: High likelihood of cloned audio. Call back via verified number."
        else:
            verdict = "Critical"
            status_text = "Confirmed Impersonation Attack"
            color = "#EF4444"  # Crimson Red
            action_recommendation = "TERMINATE CALL IMMEDIATELY. Dispatching fraud alert to bank/security."

        # Generate Human-Centric Forensic Explanations
        reasons = []
        if model_prob >= 0.60:
            reasons.append(f"Deep neural vocoder artifacts detected ({int(model_prob * 100)}% model confidence)")
        elif model_prob >= 0.40:
            reasons.append("Slight synthetic speech harmonic patterns observed")
            
        pitch_info = acoustic_features.get("pitch", {})
        if pitch_info.get("contour_flatness_score", 0.0) >= 0.70:
            reasons.append(f"Unnaturally flat pitch contour ({pitch_info.get('pitch_std_hz', 0)} Hz std, typical human is >18 Hz)")
            
        perturb = acoustic_features.get("perturbation", {})
        if perturb.get("jitter_anomaly", 0.0) >= 0.60:
            reasons.append(f"Artificial cycle perturbation (Jitter: {perturb.get('jitter_percent', 0)}%, Shimmer: {perturb.get('shimmer_percent', 0)}%)")
            
        if spectral_score >= 0.60:
            reasons.append("Phase flux discontinuity detected at audio slice points")

        vocoder_info = acoustic_features.get("vocoder_metrics", {})
        if vocoder_info.get("vocoder_cutoff_detected", False):
            reasons.append("High-frequency vocoder cutoff anomaly (>7.2 kHz brickwall/buzz)")

        hnr_info = acoustic_features.get("hnr", {})
        if hnr_info.get("hnr_anomaly_score", 0.0) >= 0.50:
            reasons.append(f"Abnormal Harmonic-to-Noise Ratio ({hnr_info.get('hnr_db', 0)} dB)")
            
        if nlp_score >= 0.50:
            matched = nlp_result.get("matched_phrases", [])
            phrases_str = f" ('{', '.join(matched[:2])}')" if matched else ""
            reasons.append(f"High-risk financial coercion/urgency keywords detected{phrases_str}")
            
        if meta_score >= 0.40:
            reasons.append("Suspicious caller metadata (unknown or VoIP routed line)")

        if not reasons:
            reasons.append("Natural human prosody, organic pitch variations, and authentic vocal tract tremor")

        primary_explanation = "; ".join(reasons)

        components = {
            "model_confidence": round(model_prob * 100, 1),
            "spectral_discontinuity": round(spectral_score * 100, 1),
            "prosodic_irregularity": round(prosody_score * 100, 1),
            "urgency_nlp": round(nlp_score * 100, 1),
            "caller_metadata": round(meta_score * 100, 1)
        }

        component_contributions = {
            "model_contribution": round(self.w_model * model_prob * 100, 1),
            "spectral_contribution": round(self.w_spectral * spectral_score * 100, 1),
            "prosody_contribution": round(self.w_prosody * prosody_score * 100, 1),
            "urgency_contribution": round(self.w_nlp * nlp_score * 100, 1),
            "meta_contribution": round(self.w_meta * meta_score * 100, 1)
        }

        layers = acoustic_features.get("layers", {})

        return {
            "risk_score": risk_score,
            "verdict": verdict,
            "status_text": status_text,
            "color": color,
            "action_recommendation": action_recommendation,
            "explanation": primary_explanation,
            "forensic_reasons": reasons,
            "components": components,
            "contributions": component_contributions,
            "layers": layers
        }

def np_clip(val: float, low: float, high: float) -> float:
    return max(low, min(high, val))

# Global instance
risk_engine = RiskFusionEngine()
