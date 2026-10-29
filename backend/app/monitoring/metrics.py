"""
Prometheus Metrics Registry for Real-Time Telemetry & Scalability Monitoring.
Exposes standard Prometheus metrics at GET /v1/metrics for Grafana / SIEM scraping.
"""

from typing import Tuple, Optional
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY
)

# Standard metrics
ACTIVE_SESSIONS = Gauge(
    "voice_clone_active_sessions",
    "Number of currently active streaming sessions"
)

CHUNKS_TOTAL = Counter(
    "voice_clone_chunks_total",
    "Total audio chunks processed by detection pipeline"
)

STAGE1_SCREENED_TOTAL = Counter(
    "voice_clone_stage1_screened_total",
    "Total chunks evaluated by Stage 1 screening gate"
)

STAGE2_ESCALATED_TOTAL = Counter(
    "voice_clone_stage2_escalated_total",
    "Total chunks escalated to Stage 2 heavy neural model"
)

STAGE2_ESCALATION_RATE = Gauge(
    "voice_clone_stage2_escalation_rate",
    "Fraction of chunks reaching Stage 2 heavy neural model (0.0 to 1.0)"
)

FAIL_OPEN_TOTAL = Counter(
    "voice_clone_fail_open_total",
    "Total fail-open occurrences due to deadline timeout"
)

TOTAL_LATENCY_HISTOGRAM = Histogram(
    "voice_clone_total_latency_seconds",
    "End-to-end chunk processing latency in seconds",
    buckets=[0.001, 0.002, 0.005, 0.010, 0.025, 0.050, 0.100, 0.150, 0.250, 0.500]
)

STAGE1_LATENCY_HISTOGRAM = Histogram(
    "voice_clone_stage1_latency_seconds",
    "Stage 1 screening gate latency in seconds",
    buckets=[0.0005, 0.001, 0.002, 0.005, 0.010, 0.020]
)

STAGE2_LATENCY_HISTOGRAM = Histogram(
    "voice_clone_stage2_latency_seconds",
    "Stage 2 heavy neural AASIST latency in seconds",
    buckets=[0.005, 0.010, 0.020, 0.035, 0.050, 0.100, 0.150]
)

ALERTS_TOTAL = Counter(
    "voice_clone_alerts_total",
    "Total threat alerts issued",
    ["tier"]
)

# Internal counters to calculate rolling escalation rate
_total_chunks_processed = 0
_total_stage2_escalated = 0


def record_chunk_metrics(
    total_seconds: float,
    stage1_seconds: float,
    stage2_seconds: float,
    stage2_triggered: bool,
    is_fail_open: bool = False,
    alert_tier: Optional[str] = None
):
    """
    Records Prometheus telemetry on every audio chunk.
    """
    global _total_chunks_processed, _total_stage2_escalated

    CHUNKS_TOTAL.inc()
    STAGE1_SCREENED_TOTAL.inc()
    TOTAL_LATENCY_HISTOGRAM.observe(total_seconds)
    STAGE1_LATENCY_HISTOGRAM.observe(stage1_seconds)

    _total_chunks_processed += 1

    if stage2_triggered:
        STAGE2_ESCALATED_TOTAL.inc()
        STAGE2_LATENCY_HISTOGRAM.observe(stage2_seconds)
        _total_stage2_escalated += 1

    if _total_chunks_processed > 0:
        STAGE2_ESCALATION_RATE.set(_total_stage2_escalated / _total_chunks_processed)

    if is_fail_open:
        FAIL_OPEN_TOTAL.inc()

    if alert_tier and alert_tier in ["Medium", "High", "Critical"]:
        ALERTS_TOTAL.labels(tier=alert_tier).inc()


def set_active_sessions(count: int):
    """Updates gauge of active concurrent sessions."""
    ACTIVE_SESSIONS.set(count)


def get_prometheus_metrics() -> Tuple[bytes, str]:
    """Generates Prometheus text exposition format payload."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
