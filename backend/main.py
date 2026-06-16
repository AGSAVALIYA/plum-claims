"""FastAPI application entry point for Plum Claims Processing System."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from backend.api.middleware import CorrelationIDMiddleware, RateLimitMiddleware
from backend.api.router import api_router
from backend.core.config import settings
from backend.core.exceptions import DocumentValidationError, PlumException
from backend.core.logging import get_logger, setup_logging
from backend.core.telemetry import instrument_app, setup_telemetry, get_prometheus_metrics

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — setup and teardown."""
    setup_logging()
    setup_telemetry()

    logger.info(
        "app_starting",
        env=settings.app_env,
        debug=settings.app_debug,
        tracing=settings.enable_tracing,
        metrics=settings.enable_metrics,
    )

    # Initialize database tables in dev mode
    if settings.app_env == "development":
        try:
            from backend.providers.db.session import get_db

            db = get_db()
            await db.create_all()
            logger.info("db_tables_created")
        except Exception as e:
            logger.warning("db_init_skipped", error=str(e))

    # Instrument with OpenTelemetry
    try:
        instrument_app(app)
        if settings.enable_tracing:
            from backend.core.telemetry import instrument_sqlalchemy
            from backend.providers.db.session import get_db

            db = get_db()
            # SQLAlchemyInstrumentor doesn't support async events.
            # Instrument the sync engine instead — it proxies to the same connection pool.
            sync_engine = db.engine.sync_engine
            instrument_sqlalchemy(sync_engine)
    except Exception as e:
        logger.warning("telemetry_instrumentation_skipped", error=str(e))

    # Start embedded Celery worker in a background thread
    import threading
    from celery import shared_task

    worker_thread = None

    def _start_worker():
        """Start a solo-pool Celery worker in-process."""
        from backend.core.celery_app import celery_app

        celery_app.worker_main(
            argv=["worker", "--pool=solo", "--loglevel=info", "-n", "embedded@%h"]
        )

    worker_thread = threading.Thread(target=_start_worker, daemon=True, name="celery-worker")
    worker_thread.start()
    logger.info("celery_worker_started", mode="embedded")

    yield

    # Teardown
    try:
        from backend.providers.db.session import get_db

        db = get_db()
        await db.close()
    except Exception:
        pass
    logger.info("app_shutdown")


app = FastAPI(
    title="Plum Claims Processing System",
    description="AI-powered health insurance claims processing with full explainability.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware (order matters: last added = first executed) ─────

# Correlation ID — injects X-Request-Id into every request/response
app.add_middleware(CorrelationIDMiddleware)

# Rate Limiting — per-member or per-IP sliding window
app.add_middleware(RateLimitMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


# ── Exception Handlers ──────────────────────────────────────────


@app.exception_handler(PlumException)
async def plum_exception_handler(request: Request, exc: PlumException) -> JSONResponse:
    """Handle all Plum domain exceptions."""
    status_code = 422 if isinstance(exc, DocumentValidationError) else 500
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.error("unhandled_error", error=str(exc), path=str(request.url))
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "details": {},
            }
        },
    )


# ── Health Check ────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "plum-claims",
        "version": "0.1.0",
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check — verifies DB, Redis, and LLM connectivity."""
    checks = {}

    # DB check
    try:
        from backend.providers.db.session import get_db

        db = get_db()
        async with db.session_factory() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis check
    try:
        from backend.core.container import get_container

        cache = get_container().cache
        if cache:
            await cache.set("plum:health", "1", 5)
            await cache.get("plum:health")
            checks["redis"] = "ok"
        else:
            checks["redis"] = "disabled"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    # LLM check
    try:
        from backend.core.container import get_container

        llm = get_container().llm
        if llm:
            alive = await llm.health_check()
            checks["llm"] = "ok" if alive else "unhealthy"
    except Exception as e:
        checks["llm"] = f"error: {e}"

    all_ok = all(v == "ok" or v == "disabled" for v in checks.values())
    return {
        "status": "ready" if all_ok else "degraded",
        "checks": checks,
    }


# ── Prometheus Metrics ──────────────────────────────────────────


@app.get("/metrics")
async def prometheus_metrics():
    """Expose Prometheus metrics in text format."""
    metrics_data, content_type = get_prometheus_metrics()
    return Response(
        content=metrics_data,
        media_type=content_type,
    )
