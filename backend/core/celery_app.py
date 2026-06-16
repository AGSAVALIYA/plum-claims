"""Celery application configuration for async task processing."""

from __future__ import annotations

from celery import Celery

from backend.core.config import settings

celery_app = Celery(
    "plum_claims",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "backend.orchestrator.tasks.process_claim_async": {"queue": "claims"},
    },
    task_default_queue="claims",
)

# Auto-discover tasks in the orchestrator package
celery_app.autodiscover_tasks(["backend.orchestrator"])
