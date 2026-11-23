# Worker containers must set PHISHGUARD_WORKER=1 so app.database uses NullPool
# (each task runs in a fresh event loop). See docker-compose.yml.
from celery import Celery

from app.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "phishguard",
    broker=_settings.CELERY_BROKER_URL,
    backend=_settings.CELERY_RESULT_BACKEND,
    include=["app.workers.scan_tasks", "app.workers.report_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=86400,
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=900,
    task_soft_time_limit=840,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=200,
    broker_connection_retry_on_startup=True,
    task_default_queue="default",
    task_routes={
        "app.workers.scan_tasks.*": {"queue": "scans"},
        "app.workers.report_tasks.*": {"queue": "reports"},
    },
)

celery_app.conf.beat_schedule = {}
