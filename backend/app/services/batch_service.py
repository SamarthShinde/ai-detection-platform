"""Batch processing service — manages collections of detections submitted together."""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.database import Batch, Detection

logger = logging.getLogger(__name__)


class BatchService:
    """Create and track batches of detection jobs."""

    def create_batch(self, db: Session, user_id: int, batch_name: str) -> Batch:
        """Create a new Batch record (files added later via add_detection_to_batch)."""
        batch = Batch(
            user_id=user_id,
            batch_name=batch_name,
            status="created",
            files_total=0,
            files_completed=0,
            files_failed=0,
            created_at=datetime.utcnow(),
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        logger.info("Batch created", extra={"batch_id": batch.id, "user_id": user_id})
        return batch

    def add_detection_to_batch(self, db: Session, batch_id: int, detection_id: int) -> None:
        """Link a detection to a batch and increment files_total."""
        detection = db.query(Detection).filter(Detection.id == detection_id).first()
        if detection is None:
            raise ValueError(f"Detection {detection_id} not found")

        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch is None:
            raise ValueError(f"Batch {batch_id} not found")

        detection.batch_id = batch_id
        batch.files_total += 1
        if batch.status == "created":
            batch.status = "processing"
        db.commit()

    def get_batch_status(self, db: Session, batch_id: int, user_id: int) -> dict:
        """Return current progress dict for a batch owned by user_id."""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch is None:
            return None  # caller should raise 404

        if batch.user_id != user_id:
            return None  # caller should raise 403

        # Live counts from detections table
        total = batch.files_total
        completed = (
            db.query(Detection)
            .filter(Detection.batch_id == batch_id, Detection.processing_status == "completed")
            .count()
        )
        processing = (
            db.query(Detection)
            .filter(Detection.batch_id == batch_id, Detection.processing_status.in_(["pending", "processing"]))
            .count()
        )
        failed = (
            db.query(Detection)
            .filter(Detection.batch_id == batch_id, Detection.processing_status == "error")
            .count()
        )

        # Sync counters back to the batch row
        batch.files_completed = completed
        batch.files_failed = failed
        if total > 0 and (completed + failed) >= total and batch.status != "completed":
            batch.status = "completed"
            batch.completed_at = datetime.utcnow()
        db.commit()

        progress_percent = round((completed / total * 100) if total > 0 else 0)

        # Rough ETA: assume average 30 s per file remaining
        remaining = total - completed - failed
        eta_seconds = remaining * 30 if remaining > 0 else 0

        return {
            "batch_id": batch.id,
            "batch_name": batch.batch_name,
            "status": batch.status,
            "files_total": total,
            "files_completed": completed,
            "files_processing": processing,
            "files_failed": failed,
            "progress_percent": progress_percent,
            "eta_seconds": eta_seconds,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
        }

    def get_batch_summary(self, db: Session, batch_id: int) -> Optional[dict]:
        """Return a summary dict for a completed batch."""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch is None:
            return None

        detections = db.query(Detection).filter(Detection.batch_id == batch_id).all()
        completed = [d for d in detections if d.processing_status == "completed"]

        ai_probs = [d.ai_probability for d in completed if d.ai_probability is not None]
        ai_detections = sum(1 for p in ai_probs if p >= 0.5)
        confidence_avg = round(
            sum(d.confidence_score for d in completed if d.confidence_score is not None) / len(completed), 4
        ) if completed else 0.0
        total_time_ms = sum(d.processing_time_ms or 0 for d in completed)

        return {
            "batch_id": batch.id,
            "batch_name": batch.batch_name,
            "summary": {
                "total_files": len(detections),
                "completed_files": len(completed),
                "failed_files": len(detections) - len(completed),
                "ai_detections": ai_detections,
                "human_detections": len(completed) - ai_detections,
                "confidence_avg": confidence_avg,
                "processing_time_total_ms": total_time_ms,
                "exported_at": datetime.utcnow().isoformat(),
            },
        }

    def list_user_batches(self, db: Session, user_id: int, skip: int = 0, limit: int = 20) -> tuple[list[Batch], int]:
        """Return (batches, total) for a user."""
        q = db.query(Batch).filter(Batch.user_id == user_id)
        total = q.count()
        batches = q.order_by(Batch.created_at.desc()).offset(skip).limit(limit).all()
        return batches, total

    def update_batch_task_id(self, db: Session, batch_id: int, task_id: str) -> None:
        """Store the Celery orchestration task ID on the batch."""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch:
            batch.celery_task_id = task_id
            db.commit()


batch_service = BatchService()
