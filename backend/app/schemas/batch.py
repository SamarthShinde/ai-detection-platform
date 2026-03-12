"""Pydantic schemas for batch processing endpoints."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateBatchRequest(BaseModel):
    batch_name: str = Field(..., min_length=1, max_length=255)
    detection_ids: list[int] = Field(..., min_length=1, description="IDs of existing detections to include")


class BatchResponse(BaseModel):
    batch_id: int
    batch_name: str
    status: str
    files_total: int
    files_completed: int
    files_failed: int
    progress_percent: int
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BatchStatusResponse(BaseModel):
    batch_id: int
    batch_name: str
    status: str
    files_total: int
    files_completed: int
    files_processing: int
    files_failed: int
    progress_percent: int
    eta_seconds: int
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class BatchListResponse(BaseModel):
    batches: list[BatchResponse]
    total: int
    skip: int
    limit: int


class BatchSummaryResponse(BaseModel):
    batch_id: int
    batch_name: str
    summary: dict
