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
)

celery_app.autodiscover_tasks(["app.tasks"])
