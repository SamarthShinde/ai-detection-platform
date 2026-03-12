"""Monitoring, metrics collection, and structured event logging."""
import logging
import traceback
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class MonitoringService:
    """Provides structured event logging and system health metrics."""

    # ── Request / response logging ────────────────────────────────────────────

    def log_request(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[int],
        status_code: int,
        response_time_ms: float,
        error_message: Optional[str] = None,
    ) -> None:
        """Log a single HTTP request with performance metrics."""
        extra = {
            "event": "http_request",
            "endpoint": endpoint,
            "method": method,
            "user_id": user_id,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
        }
        if error_message:
            extra["error_message"] = error_message
            logger.warning("HTTP request error", extra=extra)
        else:
            logger.info("HTTP request", extra=extra)

    # ── Error logging ─────────────────────────────────────────────────────────

    def log_error(
        self,
        error_type: str,
        error_message: str,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None,
    ) -> None:
        """Log an application error with full context."""
        logger.error(
            "Application error",
            extra={
                "event": "application_error",
                "error_type": error_type,
                "error_message": error_message,
                "user_id": user_id,
                "endpoint": endpoint,
                "stack_trace": traceback.format_exc(),
            },
        )

    # ── Quota events ──────────────────────────────────────────────────────────

    def log_quota_event(
        self,
        event_type: str,
        user_id: int,
        subscription_tier: str,
        scans_used: int,
        scans_limit: int,
    ) -> None:
        """Log quota-related events such as 'quota_exceeded' or 'tier_upgraded'."""
        logger.info(
            "Quota event",
            extra={
                "event": event_type,
                "user_id": user_id,
                "subscription_tier": subscription_tier,
                "scans_used": scans_used,
                "scans_limit": scans_limit,
            },
        )

    # ── Detection events ──────────────────────────────────────────────────────

    def log_detection_completed(
        self,
        detection_id: int,
        user_id: int,
        ai_probability: float,
        processing_time_ms: float,
    ) -> None:
        """Log a successfully completed detection."""
        logger.info(
            "Detection completed",
            extra={
                "event": "detection_completed",
                "detection_id": detection_id,
                "user_id": user_id,
                "ai_probability": ai_probability,
                "processing_time_ms": processing_time_ms,
            },
        )

    # ── System health metrics ─────────────────────────────────────────────────

    def get_system_metrics(self) -> dict:
        """Collect and return current system health metrics."""
        return {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "database": self._check_database(),
            "redis": self._check_redis(),
            "celery": self._check_celery(),
            "api": {"status": "operational"},
        }

    def _check_database(self) -> dict:
        try:
            from app.utils.db import engine
            from sqlalchemy import text

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            pool = engine.pool
            return {
                "healthy": True,
                "connections": pool.checkedout(),
                "pool_size": pool.size(),
            }
        except Exception as exc:
            return {"healthy": False, "error": str(exc)}

    def _check_redis(self) -> dict:
        try:
            import redis as redis_sync
            from app.utils.config import settings

            r = redis_sync.from_url(settings.REDIS_URL, socket_connect_timeout=2)
            info = r.info("memory")
            memory_mb = round(info.get("used_memory", 0) / (1024 * 1024), 1)
            return {"healthy": True, "memory_mb": memory_mb}
        except Exception as exc:
            return {"healthy": False, "error": str(exc)}

    def _check_celery(self) -> dict:
        try:
            from app.celery_app import celery_app

            inspect = celery_app.control.inspect(timeout=1)
            active = inspect.active() or {}
            active_tasks = sum(len(v) for v in active.values())
            workers = len(active)
            return {"workers": workers, "active_tasks": active_tasks, "healthy": True}
        except Exception as exc:
            return {"workers": 0, "active_tasks": 0, "healthy": False, "error": str(exc)}


monitoring_service = MonitoringService()
