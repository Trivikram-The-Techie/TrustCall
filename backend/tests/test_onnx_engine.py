"""
Tests for AASIST-L ONNX Runtime and edge engine interface.
"""

import numpy as np
from app.models.onnx_engine import onnx_engine

def test_onnx_engine_initialization():
    assert onnx_engine is not None
    assert hasattr(onnx_engine, "predict_chunk")
    assert hasattr(onnx_engine, "export_onnx")

def test_onnx_engine_prediction_fallback():
    dummy_audio = np.random.uniform(-0.5, 0.5, 32000).astype(np.float32)
    res = onnx_engine.predict_chunk(dummy_audio, sr=16000)
    assert "raw_probability" in res
    assert "is_synthetic" in res
    assert res["engine"] in ["onnx", "pytorch_fallback"]
