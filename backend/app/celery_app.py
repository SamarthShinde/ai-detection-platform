from celery import Celery
from app.utils.config import settings

celery_app = Celery(
    "ai_detection",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=600,
    task_time_limit=700,
    # Use solo pool to prevent MPS GPU context corruption on Apple Silicon.
    # The default prefork pool forks child processes; the Metal compiler
    # service is not fork-safe and causes SIGABRT in all worker processes.
    worker_pool="solo",
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

celery_app.autodiscover_tasks(["app.tasks"])

# Explicitly import tasks so they register when the worker starts
import app.tasks.detection_tasks  # noqa: E402, F401
