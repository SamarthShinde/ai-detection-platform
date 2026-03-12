"""Pydantic schemas for detection endpoints."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    detection_id: int
    file_hash: str
    file_type: str
    processing_status: str
    message: str
    polling_url: str


class DetectionSummary(BaseModel):
    detection_id: int
    file_hash: str
    file_type: str
    original_filename: Optional[str]
    processing_status: str
    ai_probability: Optional[float]
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DetectionStatusResponse(BaseModel):
    detection_id: int
    processing_status: str
    progress_percent: Optional[int] = None
    message: Optional[str] = None
    # completed fields (populated when status == "completed")
    file_hash: Optional[str] = None
    file_type: Optional[str] = None
    ai_probability: Optional[float] = None
    confidence_score: Optional[float] = None
    detection_methods: Optional[str] = None
    processing_time_ms: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_json: Optional[Any] = None
    # error field
    error_message: Optional[str] = None
    retry_available: Optional[bool] = None

    model_config = {"from_attributes": True}


class DetectionListResponse(BaseModel):
    detections: list[DetectionSummary]
    total: int
    skip: int
    limit: int
