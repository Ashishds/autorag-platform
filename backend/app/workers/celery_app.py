"""Celery application + beat schedule (LLD §18.2)."""

from __future__ import annotations

import sys

from celery import Celery

from app.config import settings

celery = Celery(
    "autorag",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.ingest_task",
        "app.workers.evaluate_task",
        "app.workers.observer_cron",
        "app.workers.connector_task",
        "app.workers.connector_cron",
    ],
)

_worker_conf: dict = {
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "task_track_started": True,
    "timezone": "UTC",
    "beat_schedule": {
        "observer-drift-scan": {
            "task": "app.workers.observer_cron.run_observer_scan",
            "schedule": settings.OBSERVER_CRON_MINUTES * 60.0,
        },
        "connector-scheduler": {
            "task": "app.workers.connector_cron.run_connector_scheduler",
            "schedule": 300.0,  # Run every 5 minutes
        }
    },
}

# prefork/billiard is unreliable on Windows — use solo pool for local dev.
if sys.platform == "win32":
    _worker_conf["worker_pool"] = "solo"
    _worker_conf["worker_concurrency"] = 1

# Local dev: run tasks inline in the API process (no separate worker required).
if settings.ENV == "local":
    _worker_conf["task_always_eager"] = True
    _worker_conf["task_eager_propagates"] = True

celery.conf.update(_worker_conf)
