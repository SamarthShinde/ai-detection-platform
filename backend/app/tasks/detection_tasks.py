"""Celery tasks for async detection processing."""
import logging
import time
from datetime import datetime

from app.celery_app import celery_app
from app.services.monitoring_service import monitoring_service

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.detection_tasks.process_detection",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_detection(self, detection_id: int) -> dict:
    """
    Async detection processing task.

    Stages:
    1. Load Detection record
    2. Set status → 'processing'
    3. Reconstruct file path from metadata
    4. Run ML ensemble (EfficientNet-B4 + Xception)
    5. Persist results → 'completed'
    6. On error → set status 'error', retry up to 3×
    """
    from app.models.database import Detection
    from app.utils.db import SessionLocal

    db = SessionLocal()
    start = time.perf_counter()

    try:
        detection = db.query(Detection).filter(Detection.id == detection_id).first()
        if not detection:
            logger.error("Detection not found", extra={"detection_id": detection_id})
            return {"error": "Detection not found"}

        # ── Mark processing ──────────────────────────────────────────────────
        detection.processing_status = "processing"
        detection.celery_task_id = self.request.id
        db.commit()
        if self.request.id:
            self.update_state(state="PROGRESS", meta={"progress": 10, "message": "Starting detection…"})
        logger.info("Detection started", extra={"detection_id": detection_id, "file_type": detection.file_type})

        # ── Reconstruct file path ────────────────────────────────────────────
        from app.services.file_service import file_service

        file_path = file_service.get_file_path(
            user_id=detection.user_id,
            file_hash=detection.file_hash,
            original_filename=detection.original_filename or f"file.{detection.file_type}",
        )

        # ── ML Inference ─────────────────────────────────────────────────────
        if self.request.id:
            self.update_state(state="PROGRESS", meta={"progress": 30, "message": "Loading ML models…"})

        from app.ml.ensemble import detection_ensemble

        if detection.file_type == "image":
            if self.request.id:
                self.update_state(state="PROGRESS", meta={"progress": 50, "message": "Running image ensemble…"})
            ml_result = detection_ensemble.predict_image(file_path)
        else:
            if self.request.id:
                self.update_state(state="PROGRESS", meta={"progress": 50, "message": "Sampling video frames…"})
            ml_result = detection_ensemble.predict_video(file_path, max_frames=10)

        # ── Persist results ──────────────────────────────────────────────────
        elapsed_ms = round((time.perf_counter() - start) * 1000)

        detection.processing_status = "completed"
        detection.ai_probability = ml_result.ai_probability
        detection.confidence_score = ml_result.confidence_score
        detection.detection_methods = ml_result.detection_methods[:500]   # VARCHAR(500) limit
        detection.result_json = {
            "ai_probability": ml_result.ai_probability,
            "confidence_score": ml_result.confidence_score,
            "model_scores": ml_result.model_scores,
            "artifacts_found": ml_result.artifacts_found,
            "processing_time_ms": ml_result.processing_time_ms,
        }
        detection.processing_time_ms = elapsed_ms
        detection.completed_at = datetime.utcnow()
        db.commit()

        logger.info(
            "Detection completed",
            extra={
                "detection_id": detection_id,
                "ai_probability": ml_result.ai_probability,
                "ms": elapsed_ms,
            },
        )
        monitoring_service.log_detection_completed(
            detection_id=detection.id,
            user_id=detection.user_id,
            ai_probability=ml_result.ai_probability,
            processing_time_ms=float(elapsed_ms),
        )
        return {
            "detection_id": detection_id,
            "status": "completed",
            "ai_probability": ml_result.ai_probability,
        }

    except FileNotFoundError as exc:
        _handle_error(db, detection_id, "File not found (may have been deleted)", exc, self, start)
        raise self.retry(exc=exc)
    except MemoryError as exc:
        _handle_error(db, detection_id, "Insufficient memory for processing", exc, self, start)
        raise self.retry(exc=exc)
    except Exception as exc:
        _handle_error(db, detection_id, f"Detection processing failed: {exc}", exc, self, start)
        raise self.retry(exc=exc)
    finally:
        db.close()


def _handle_error(db, detection_id: int, message: str, exc: Exception, task, start: float) -> None:
    """Set detection status to 'error' and log."""
    try:
        from app.models.database import Detection

        detection = db.query(Detection).filter(Detection.id == detection_id).first()
        if detection:
            detection.processing_status = "error"
            detection.error_message = message[:500]
            detection.processing_time_ms = round((time.perf_counter() - start) * 1000)
            db.commit()
    except Exception:
        pass
    logger.error("Detection failed", extra={"detection_id": detection_id, "error": str(exc)}, exc_info=True)
    monitoring_service.log_error(
        error_type=type(exc).__name__,
        error_message=str(exc),
        endpoint="/detections",
    )
