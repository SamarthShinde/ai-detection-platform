"""Batch processing endpoints — create, list, status, export."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.models.database import Batch, Detection, User
from app.schemas.batch import (
    BatchListResponse,
    BatchResponse,
    BatchStatusResponse,
    BatchSummaryResponse,
    CreateBatchRequest,
)
from app.services.batch_service import batch_service
from app.utils.db import get_db
from app.utils.dependencies import get_current_user
from app.utils.export_service import export_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/batches", tags=["batch"])


def _get_batch_or_404(batch_id: int, user_id: int, db: Session) -> Batch:
    """Return the batch if it exists and belongs to *user_id*, else raise 404/403."""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    if batch.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return batch


# ── Create ────────────────────────────────────────────────────────────────────


@router.post("", status_code=status.HTTP_201_CREATED)
def create_batch(
    body: CreateBatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a named batch and attach existing detection records to it.

    All *detection_ids* must already exist and belong to the requesting user.
    """
    # Verify ownership of every detection up-front
    for did in body.detection_ids:
        det = db.query(Detection).filter(Detection.id == did).first()
        if det is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Detection {did} not found",
            )
        if det.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Detection {did} does not belong to you",
            )

    # Create batch record
    batch = batch_service.create_batch(db, user_id=current_user.id, batch_name=body.batch_name)

    # Link detections
    for did in body.detection_ids:
        batch_service.add_detection_to_batch(db, batch_id=batch.id, detection_id=did)

    db.refresh(batch)
    logger.info(
        "Batch created via API",
        extra={"batch_id": batch.id, "user_id": current_user.id, "files": len(body.detection_ids)},
    )
    return {
        "batch_id": batch.id,
        "batch_name": batch.batch_name,
        "files_count": len(body.detection_ids),
        "status": batch.status,
        "message": f"Batch created with {len(body.detection_ids)} detection(s).",
    }


# ── List ──────────────────────────────────────────────────────────────────────


@router.get("", response_model=BatchListResponse)
def list_batches(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a paginated list of all batches owned by the current user."""
    batches, total = batch_service.list_user_batches(db, current_user.id, skip=skip, limit=limit)
    return BatchListResponse(
        batches=[
            BatchResponse(
                batch_id=b.id,
                batch_name=b.batch_name,
                status=b.status,
                files_total=b.files_total,
                files_completed=b.files_completed,
                files_failed=b.files_failed,
                progress_percent=round((b.files_completed / b.files_total * 100) if b.files_total > 0 else 0),
                created_at=b.created_at,
                completed_at=b.completed_at,
            )
            for b in batches
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


# ── Status ────────────────────────────────────────────────────────────────────


@router.get("/{batch_id}", response_model=BatchStatusResponse)
def get_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return live progress information for a single batch."""
    _get_batch_or_404(batch_id, current_user.id, db)
    result = batch_service.get_batch_status(db, batch_id=batch_id, user_id=current_user.id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return BatchStatusResponse(**result)


# ── Summary ───────────────────────────────────────────────────────────────────


@router.get("/{batch_id}/summary", response_model=BatchSummaryResponse)
def get_batch_summary(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return aggregate statistics for a (completed) batch."""
    _get_batch_or_404(batch_id, current_user.id, db)
    summary = batch_service.get_batch_summary(db, batch_id=batch_id)
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return BatchSummaryResponse(**summary)


# ── Export ────────────────────────────────────────────────────────────────────


@router.get("/{batch_id}/export")
def export_batch(
    batch_id: int,
    fmt: str = Query("json", pattern="^(json|csv|pdf)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export all detection results in the batch.

    * **fmt=json** — returns JSON (default)
    * **fmt=csv**  — returns a CSV file download
    * **fmt=pdf**  — returns a PDF file download (requires `reportlab`)
    """
    batch = _get_batch_or_404(batch_id, current_user.id, db)
    detections = db.query(Detection).filter(Detection.batch_id == batch_id).all()

    if fmt == "csv":
        csv_content = export_service.export_batch_as_csv(batch, detections)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="batch_{batch_id}.csv"'},
        )

    if fmt == "pdf":
        pdf_bytes = export_service.generate_pdf_report(batch, detections)
        if pdf_bytes is None:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="PDF export requires the 'reportlab' package. Install it with: pip install reportlab",
            )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="batch_{batch_id}.pdf"'},
        )

    # Default: JSON
    return export_service.export_batch_as_json(batch, detections)
