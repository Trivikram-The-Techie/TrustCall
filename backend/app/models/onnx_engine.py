"""
ONNX Runtime Export and Edge Inference Engine for AASIST-L.
Enables low-footprint anti-spoofing inference on edge devices (Android NDK, Raspberry Pi, PBX trunks).
"""

import os
import logging
import numpy as np
import torch

from app.models.spoof_detector import spoof_detector

logger = logging.getLogger("TrustCall-ONNX")

class AASISTONNXEngine:
    """
    Manages export and execution of AASIST-L via ONNX Runtime.
    Provides fallback to PyTorch when onnxruntime is absent.
    """
    def __init__(self, onnx_path: str = None):
        if onnx_path is None:
            models_dir = os.path.dirname(os.path.abspath(__file__))
            onnx_path = os.path.join(models_dir, "weights", "AASIST-L.onnx")
        self.onnx_path = onnx_path
        self.session = None
        self._init_session()

    def _init_session(self):
        if os.path.exists(self.onnx_path):
            try:
                import onnxruntime as ort
                self.session = ort.InferenceSession(self.onnx_path, providers=["CPUExecutionProvider"])
                logger.info(f"Loaded AASIST-L ONNX model from {self.onnx_path}")
            except Exception as e:
                logger.info(f"ONNX session initialization skipped: {e}")

    def export_onnx(self, output_path: str = None) -> str:
        """Exports the active AASIST-L PyTorch model to ONNX format."""
        target_path = output_path or self.onnx_path
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        model = spoof_detector.model
        model.eval()

        dummy_input = torch.randn(1, 64600, device=spoof_detector.device)
        torch.onnx.export(
            model,
            dummy_input,
            target_path,
            export_params=True,
            opset_version=14,
            do_constant_folding=True,
            input_names=["waveform"],
            output_names=["logits"],
            dynamic_axes={"waveform": {0: "batch_size"}, "logits": {0: "batch_size"}}
        )
        logger.info(f"Exported AASIST-L ONNX model to {target_path}")
        return target_path

    def predict_chunk(self, audio: np.ndarray, sr: int = 16000) -> dict:
        """
        Runs inference using ONNX session if available, else delegates to PyTorch detector.
        """
        if self.session is not None:
            # Prepare 64,600 samples
            target_len = 64600
            if len(audio) < target_len:
                repeats = (target_len // len(audio)) + 1
                audio = np.tile(audio, repeats)[:target_len]
            else:
                audio = audio[:target_len]

            inp = audio.astype(np.float32).reshape(1, -1)
            ort_inputs = {self.session.get_inputs()[0].name: inp}
            ort_outs = self.session.run(None, ort_inputs)
            logits = ort_outs[0][0]
            # Softmax
            exp_l = np.exp(logits - np.max(logits))
            probs = exp_l / np.sum(exp_l)
            spoof_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])

            return {
                "raw_probability": round(spoof_prob, 4),
                "is_synthetic": spoof_prob >= 0.50,
                "engine": "onnx"
            }
        else:
            res = spoof_detector.predict_chunk(audio, sr=sr, use_history=False)
            res["engine"] = "pytorch_fallback"
            return res

onnx_engine = AASISTONNXEngine()
