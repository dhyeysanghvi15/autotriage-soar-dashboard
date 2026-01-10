from __future__ import annotations

from prometheus_client import Counter, Histogram

PIPELINE_STAGE_TOTAL = Counter(
    "autotriage_pipeline_stage_total",
    "Total pipeline stage executions",
    labelnames=("stage",),
)

PIPELINE_STAGE_SECONDS = Histogram(
    "autotriage_pipeline_stage_seconds",
    "Pipeline stage latency seconds",
    labelnames=("stage",),
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

INGEST_TOTAL = Counter("autotriage_ingest_total", "Total webhook ingests accepted")
INGEST_IDEMPOTENT_HIT_TOTAL = Counter(
    "autotriage_ingest_idempotent_hit_total", "Idempotency key hits"
)
