"""Celery task that orchestrates batch processing and finalises batch status."""
import logging
import time

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.batch_tasks.process_batch",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def process_batch(self, batch_id: int) -> dict:
    """
    Orchestrate all detections inside *batch_id*.

    1. Load the Batch and its pending Detections.
    2. Submit a process_detection Celery task for each pending detection.
    3. Poll until all are done (with a timeout).
    4. Call batch_service to compute and persist the final summary.
    """
    from app.models.database import Batch, Detection
    from app.utils.db import SessionLocal

    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch is None:
            logger.error("Batch not found", extra={"batch_id": batch_id})
            return {"error": "Batch not found"}

        # Update task id on the batch row
        batch.celery_task_id = self.request.id
        batch.status = "processing"
        db.commit()

        # Find all pending detections in this batch
        pending = (
            db.query(Detection)
            .filter(
                Detection.batch_id == batch_id,
                Detection.processing_status.in_(["pending", "error"]),
            )
            .all()
        )

        # Submit individual detection tasks
        submitted_ids: list[int] = []
        for det in pending:
            celery_app.send_task(
                "app.tasks.detection_tasks.process_detection",
                args=[det.id],
            )
            submitted_ids.append(det.id)

        logger.info(
            "Batch tasks submitted",
            extra={"batch_id": batch_id, "submitted": len(submitted_ids)},
        )

        # Poll for completion (max ~10 minutes, checking every 5 s)
        max_polls = 120
        for _ in range(max_polls):
            time.sleep(5)
            db.expire_all()
            total = db.query(Detection).filter(Detection.batch_id == batch_id).count()
            done = (
                db.query(Detection)
                .filter(
                    Detection.batch_id == batch_id,
                    Detection.processing_status.in_(["completed", "error"]),
                )
                .count()
            )
            if done >= total:
                break

        # Finalise batch
        from app.services.batch_service import batch_service

        summary = batch_service.get_batch_summary(db, batch_id)

        # batch status is set inside get_batch_status; refresh it
        db.expire(batch)
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch and batch.status != "completed":
            from datetime import datetime
            batch.status = "completed"
            batch.completed_at = datetime.utcnow()
            db.commit()

        logger.info("Batch completed", extra={"batch_id": batch_id, "summary": summary})
        return {"batch_id": batch_id, "status": "completed", "summary": summary}

    except Exception as exc:
        logger.error("Batch processing failed", extra={"batch_id": batch_id, "error": str(exc)}, exc_info=True)
        try:
            from app.models.database import Batch
            batch = db.query(Batch).filter(Batch.id == batch_id).first()
            if batch:
                batch.status = "error"
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc)
    finally:
        db.close()
