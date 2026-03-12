"""Detection endpoints: upload, status polling, listing, deletion, retry."""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.models.database import Detection, User
from app.schemas.detection import (
    DetectionListResponse,
    DetectionStatusResponse,
    DetectionSummary,
    FileUploadResponse,
)
from app.services.file_service import file_service
from app.utils.db import get_db
from app.utils.dependencies import check_quota, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detections", tags=["detection"])


# ── Helpers ───────────────────────────────────────────────────────────────────


def _assert_owns(detection: Optional[Detection], current_user: User) -> Detection:
    """Raise 404/403 if the detection is missing or belongs to another user."""
    if detection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detection not found")
    if detection.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return detection


async def _upload(
    file: UploadFile,
    file_type: str,
    current_user: User,
    db: Session,
    batch_id: Optional[int] = None,
) -> FileUploadResponse:
    """Shared upload logic for both video and image endpoints."""
    from app.services.cache_service import cache_service

    # Validate
    if file_type == "video":
        valid, err = file_service.validate_video_file(file)
    else:
        valid, err = file_service.validate_image_file(file)

    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    # Hash (also validates size via streaming)
    file_hash = await file_service.compute_file_hash(file)

    # Duplicate check — if the same file was already uploaded by this user
    existing = (
        db.query(Detection)
        .filter(Detection.user_id == current_user.id, Detection.file_hash == file_hash)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"File already uploaded. Use detection ID {existing.id} to check results.",
        )

    # Validate batch ownership if provided
    if batch_id is not None:
        from app.models.database import Batch
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Batch {batch_id} not found")
        if batch.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to batch")

    # Save to disk
    file_path = await file_service.save_file_to_disk(file, current_user.id, file_hash, file_type)

    # Check cache — if hit, mark immediately completed
    cached = cache_service.get_cached_result(db, file_hash)
    if cached:
        detection = Detection(
            user_id=current_user.id,
            batch_id=batch_id,
            file_hash=file_hash,
            file_type=file_type,
            original_filename=file.filename,
            file_size_bytes=file.size,
            uploaded_at=datetime.utcnow(),
            processing_status="completed",
            ai_probability=cached.get("ai_probability"),
            confidence_score=cached.get("confidence_score"),
            detection_methods=(cached.get("detection_methods") or "")[:500],
            result_json=cached,
            processing_time_ms=cached.get("processing_time_ms"),
            completed_at=datetime.utcnow(),
            served_from_cache=True,
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)
        logger.info(
            "Detection served from cache",
            extra={"detection_id": detection.id, "file_hash": file_hash},
        )
        return FileUploadResponse(
            detection_id=detection.id,
            file_hash=file_hash,
            file_type=file_type,
            processing_status="completed",
            message="File matched cache — results available immediately.",
            polling_url=f"/detections/{detection.id}",
        )

    # Persist Detection record
    detection = Detection(
        user_id=current_user.id,
        batch_id=batch_id,
        file_hash=file_hash,
        file_type=file_type,
        original_filename=file.filename,
        file_size_bytes=file.size,
        uploaded_at=datetime.utcnow(),
        processing_status="pending",
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)

    # Submit Celery task (fire-and-forget)
    task = celery_app.send_task(
        "app.tasks.detection_tasks.process_detection",
        args=[detection.id],
    )
    detection.celery_task_id = task.id
    db.commit()

    logger.info(
        "Detection queued",
        extra={"detection_id": detection.id, "file_type": file_type, "task_id": task.id},
    )
    return FileUploadResponse(
        detection_id=detection.id,
        file_hash=file_hash,
        file_type=file_type,
        processing_status="pending",
        message="File uploaded. Detection in progress. Poll the URL below for results.",
        polling_url=f"/detections/{detection.id}",
    )


# ── Upload endpoints ──────────────────────────────────────────────────────────


@router.post("/video", status_code=status.HTTP_202_ACCEPTED, response_model=FileUploadResponse)
async def upload_video(
    file: UploadFile,
    batch_id: Optional[int] = Query(None, description="Optional batch to add this detection to"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _quota: None = Depends(check_quota),
):
    """Upload a video file for deepfake detection. Returns 202 immediately; poll for results."""
    return await _upload(file, "video", current_user, db, batch_id=batch_id)


@router.post("/image", status_code=status.HTTP_202_ACCEPTED, response_model=FileUploadResponse)
async def upload_image(
    file: UploadFile,
    batch_id: Optional[int] = Query(None, description="Optional batch to add this detection to"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _quota: None = Depends(check_quota),
):
    """Upload an image file for deepfake detection. Returns 202 immediately; poll for results."""
    return await _upload(file, "image", current_user, db, batch_id=batch_id)


# ── Status / results ──────────────────────────────────────────────────────────


@router.get("/{detection_id}", response_model=DetectionStatusResponse)
def get_detection(
    detection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Poll a single detection for status and (when ready) results."""
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    _assert_owns(detection, current_user)

    s = detection.processing_status

    if s in ("pending", "processing"):
        progress = 10 if s == "pending" else 50
        if detection.celery_task_id:
            try:
                result = celery_app.AsyncResult(detection.celery_task_id)
                if result.state == "PROGRESS" and isinstance(result.info, dict):
                    progress = result.info.get("progress", progress)
            except Exception:
                pass

        return DetectionStatusResponse(
            detection_id=detection.id,
            processing_status=s,
            progress_percent=progress,
            message="Detection in progress. Check back shortly.",
        )

    if s == "completed":
        return DetectionStatusResponse(
            detection_id=detection.id,
            processing_status="completed",
            file_hash=detection.file_hash,
            file_type=detection.file_type,
            ai_probability=detection.ai_probability,
            confidence_score=detection.confidence_score,
            detection_methods=detection.detection_methods,
            processing_time_ms=detection.processing_time_ms,
            uploaded_at=detection.uploaded_at,
            completed_at=detection.completed_at,
            result_json=detection.result_json,
        )

    # status == "error"
    return DetectionStatusResponse(
        detection_id=detection.id,
        processing_status="error",
        error_message=detection.error_message or "Unknown error",
        retry_available=True,
    )


# ── Retry ──────────────────────────────────────────────────────────────────────


@router.post("/{detection_id}/retry", status_code=status.HTTP_202_ACCEPTED)
def retry_detection(
    detection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-submit a failed detection to the Celery task queue."""
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    _assert_owns(detection, current_user)

    if detection.processing_status not in ("error", "pending"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Detection is '{detection.processing_status}' — only 'error' or 'pending' can be retried.",
        )

    detection.processing_status = "pending"
    detection.error_message = None
    detection.ai_probability = None
    detection.confidence_score = None
    detection.result_json = None
    detection.completed_at = None
    db.commit()

    task = celery_app.send_task(
        "app.tasks.detection_tasks.process_detection",
        args=[detection.id],
    )
    detection.celery_task_id = task.id
    db.commit()

    logger.info(
        "Detection retried",
        extra={"detection_id": detection_id, "task_id": task.id, "user_id": current_user.id},
    )
    return {
        "detection_id": detection_id,
        "status": "pending",
        "task_id": task.id,
        "message": "Detection re-queued for processing.",
        "polling_url": f"/detections/{detection_id}",
    }


# ── List ──────────────────────────────────────────────────────────────────────


@router.get("", response_model=DetectionListResponse)
def list_detections(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a paginated list of the current user's detections."""
    base_q = db.query(Detection).filter(Detection.user_id == current_user.id)
    total = base_q.count()
    rows = base_q.order_by(Detection.uploaded_at.desc()).offset(skip).limit(limit).all()

    return DetectionListResponse(
        detections=[
            DetectionSummary(
                detection_id=d.id,
                file_hash=d.file_hash,
                file_type=d.file_type,
                original_filename=d.original_filename,
                processing_status=d.processing_status,
                ai_probability=d.ai_probability,
                uploaded_at=d.uploaded_at,
            )
            for d in rows
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


# ── Delete ────────────────────────────────────────────────────────────────────


@router.delete("/{detection_id}")
def delete_detection(
    detection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a detection record and its uploaded file."""
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    _assert_owns(detection, current_user)

    file_service.delete_file(current_user.id, detection.file_hash)

    db.delete(detection)
    db.commit()
    logger.info("Detection deleted", extra={"detection_id": detection_id, "user_id": current_user.id})
    return {"message": "Detection deleted"}
