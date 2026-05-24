"""Celery application and periodic schedule.

The worker shares the backend's models and async DB layer. Celery tasks are
synchronous entrypoints that drive async coroutines via ``asyncio.run`` against
a short-lived session.
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery = Celery(
    "control_plane",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "health-sweep-every-2-min": {
            "task": "app.tasks.jobs.sweep_service_health",
            "schedule": 120.0,
        },
        "peer-staleness-every-5-min": {
            "task": "app.tasks.jobs.sweep_peer_staleness",
            "schedule": 300.0,
        },
        "render-config-hourly": {
            "task": "app.tasks.jobs.render_config_revision",
            "schedule": crontab(minute=0),
        },
    },
)

# Ensure tasks are registered.
from app.tasks import jobs  # noqa: E402,F401
