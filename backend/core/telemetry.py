"""OpenTelemetry setup — distributed tracing and metrics for the multi-agent pipeline."""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.metrics import (
    Counter,
    Histogram,
    Meter,
    get_meter_provider,
    set_meter_provider,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer, set_tracer_provider

# Prometheus exporter
try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from backend.core.config import settings

# ── Globals ────────────────────────────────────────────────────

_tracer: Tracer | None = None
_meter: Meter | None = None

# ── Business metrics ───────────────────────────────────────────

CLAIMS_SUBMITTED: Counter | None = None
CLAIMS_DECIDED: Counter | None = None
AGENT_DURATION: Histogram | None = None
AGENT_CONFIDENCE: Histogram | None = None
LLM_TOKEN_USAGE: Counter | None = None
LLM_CACHE_HITS: Counter | None = None
LLM_CACHE_MISSES: Counter | None = None
FRAUD_RISK_SCORE: Histogram | None = None
PIPELINE_DURATION: Histogram | None = None
PIPELINE_ERRORS: Counter | None = None


def setup_telemetry() -> None:
    """Initialize OpenTelemetry tracing and metrics if enabled."""
    global _tracer, _meter
    global CLAIMS_SUBMITTED, CLAIMS_DECIDED, AGENT_DURATION, AGENT_CONFIDENCE
    global LLM_TOKEN_USAGE, LLM_CACHE_HITS, LLM_CACHE_MISSES, FRAUD_RISK_SCORE
    global PIPELINE_DURATION, PIPELINE_ERRORS

    if not settings.enable_tracing and not settings.enable_metrics:
        return

    resource = Resource.create({SERVICE_NAME: settings.otel_service_name})

    # ── Tracing ──────────────────────────────────────────────
    if settings.enable_tracing:
        tracer_provider = TracerProvider(resource=resource)
        otlp_exporter = settings.otel_exporter_otlp_endpoint
        if otlp_exporter:
            tracer_provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_exporter, insecure=True))
            )
        set_tracer_provider(tracer_provider)
        _tracer = trace.get_tracer(__name__)

    # ── Metrics ──────────────────────────────────────────────
    if settings.enable_metrics:
        from opentelemetry.exporter.prometheus import PrometheusMetricReader

        # Set up metric readers - both OTLP (for Jaeger) and Prometheus (for scraping)
        metric_readers = []

        # Prometheus reader for /metrics endpoint
        prometheus_reader = PrometheusMetricReader()
        metric_readers.append(prometheus_reader)

        # OTLP reader for Jaeger
        otlp_exporter = settings.otel_exporter_otlp_endpoint
        if otlp_exporter:
            otlp_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=otlp_exporter, insecure=True)
            )
            metric_readers.append(otlp_reader)

        meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
        set_meter_provider(meter_provider)
        _meter = get_meter_provider().get_meter("plum-claims")

        # Business metrics
        CLAIMS_SUBMITTED = _meter.create_counter(
            "plum_claims_submitted_total",
            description="Total number of claims submitted",
        )
        CLAIMS_DECIDED = _meter.create_counter(
            "plum_claims_decided_total",
            description="Total number of claims decided",
        )
        AGENT_DURATION = _meter.create_histogram(
            "plum_agent_execution_duration_seconds",
            description="Agent execution duration in seconds",
        )
        AGENT_CONFIDENCE = _meter.create_histogram(
            "plum_agent_confidence_score",
            description="Confidence score per agent",
        )
        LLM_TOKEN_USAGE = _meter.create_counter(
            "plum_llm_token_usage_total",
            description="Total LLM tokens used",
        )
        LLM_CACHE_HITS = _meter.create_counter(
            "plum_llm_cache_hits_total",
            description="LLM cache hits",
        )
        LLM_CACHE_MISSES = _meter.create_counter(
            "plum_llm_cache_misses_total",
            description="LLM cache misses",
        )
        FRAUD_RISK_SCORE = _meter.create_histogram(
            "plum_fraud_risk_score",
            description="Fraud risk score distribution",
        )
        PIPELINE_DURATION = _meter.create_histogram(
            "plum_pipeline_duration_seconds",
            description="Pipeline execution duration in seconds",
        )
        PIPELINE_ERRORS = _meter.create_counter(
            "plum_pipeline_errors_total",
            description="Total number of pipeline errors",
        )


def instrument_app(app) -> None:
    """Instrument a FastAPI app with OpenTelemetry."""
    if settings.enable_tracing:
        FastAPIInstrumentor.instrument_app(app)


def instrument_sqlalchemy(engine) -> None:
    """Instrument a SQLAlchemy engine."""
    if settings.enable_tracing:
        SQLAlchemyInstrumentor().instrument(engine=engine)


def instrument_redis() -> None:
    """Instrument Redis."""
    if settings.enable_tracing:
        RedisInstrumentor().instrument()


def get_tracer() -> Tracer:
    """Get the configured tracer, or a no-op tracer."""
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer(__name__)
    return _tracer


def record_agent_execution(
    agent_name: str,
    duration_s: float,
    confidence: float,
    success: bool = True,
) -> None:
    """Record agent execution metrics."""
    if AGENT_DURATION is not None:
        AGENT_DURATION.record(duration_s, {"agent": agent_name, "success": str(success)})
    if AGENT_CONFIDENCE is not None:
        AGENT_CONFIDENCE.record(confidence, {"agent": agent_name})


def record_claim_submitted(category: str) -> None:
    """Record a claim submission."""
    if CLAIMS_SUBMITTED is not None:
        CLAIMS_SUBMITTED.add(1, {"category": category})


def record_claim_decided(decision: str) -> None:
    """Record a claim decision."""
    if CLAIMS_DECIDED is not None:
        CLAIMS_DECIDED.add(1, {"decision": decision})


def record_llm_usage(model: str, input_tokens: int, output_tokens: int) -> None:
    """Record LLM token usage."""
    if LLM_TOKEN_USAGE is not None:
        LLM_TOKEN_USAGE.add(input_tokens, {"model": model, "direction": "input"})
        LLM_TOKEN_USAGE.add(output_tokens, {"model": model, "direction": "output"})


def record_llm_cache_hit(model: str) -> None:
    """Record an LLM cache hit."""
    if LLM_CACHE_HITS is not None:
        LLM_CACHE_HITS.add(1, {"model": model})


def record_llm_cache_miss(model: str) -> None:
    """Record an LLM cache miss."""
    if LLM_CACHE_MISSES is not None:
        LLM_CACHE_MISSES.add(1, {"model": model})


def record_fraud_score(score: float) -> None:
    """Record a fraud risk score."""
    if FRAUD_RISK_SCORE is not None:
        FRAUD_RISK_SCORE.record(score)


def record_pipeline_duration(duration_s: float) -> None:
    """Record pipeline execution duration."""
    if PIPELINE_DURATION is not None:
        PIPELINE_DURATION.record(duration_s)


def record_pipeline_error(error_type: str) -> None:
    """Record a pipeline error."""
    if PIPELINE_ERRORS is not None:
        PIPELINE_ERRORS.add(1, {"error_type": error_type})


def get_prometheus_metrics() -> tuple[bytes, str]:
    """Get Prometheus metrics in text format.

    Returns:
        Tuple of (metrics_bytes, content_type)
    """
    if PROMETHEUS_AVAILABLE:
        return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
    return b"# Prometheus client not available\n", "text/plain"
