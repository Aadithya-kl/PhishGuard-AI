import os
from celery import Celery

# Get Redis URL from environment or use a default
broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/1")
result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

celery_app = Celery(
    "phishguard",
    broker=broker_url,
    backend=result_backend,
    include=["app.workers.scan_tasks", "app.workers.report_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_default_queue="default",
)

# Optional: setup periodic tasks
celery_app.conf.beat_schedule = {
    # 'sample-task': {
    #     'task': 'app.workers.scan_tasks.sample_task',
    #     'schedule': 3600.0,
    # },
}
