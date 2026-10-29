"""
Unit tests for GET /v1/metrics (Prometheus exporter) and GET /v1/scale.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.monitoring.metrics import record_chunk_metrics, set_active_sessions


def test_prometheus_metrics_endpoint():
    client = TestClient(app)

    # Record some mock metrics
    record_chunk_metrics(
        total_seconds=0.012,
        stage1_seconds=0.0015,
        stage2_seconds=0.0105,
        stage2_triggered=True,
        is_fail_open=False,
        alert_tier="Low"
    )
    set_active_sessions(3)

    response = client.get("/v1/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")

    body = response.text
    assert "voice_clone_chunks_total" in body
    assert "voice_clone_active_sessions" in body
    assert "voice_clone_stage2_escalation_rate" in body
    assert "voice_clone_total_latency_seconds" in body


def test_scale_benchmark_endpoint():
    client = TestClient(app)
    response = client.get("/v1/scale")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["measured", "not_measured"]
