"""Usage statistics and history endpoints."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.database import UsageLog, User
from app.services.usage_service import usage_service
from app.utils.db import get_db
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/usage", tags=["usage"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class UsageStatsResponse(BaseModel):
    scans_used: int
    scans_limit: int
    scans_percentage: float
    renewal_date: datetime
    subscription_tier: str
    message: str


class UsageLogResponse(BaseModel):
    endpoint: str
    timestamp: datetime
    file_size_bytes: Optional[int]
    processing_time_ms: Optional[int]
    status_code: int

    model_config = {"from_attributes": True}


class UsageHistoryResponse(BaseModel):
    usage_logs: list[UsageLogResponse]
    total: int
    skip: int
    limit: int


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/stats", response_model=UsageStatsResponse)
def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return current month scan usage and quota for the authenticated user."""
    data = usage_service.get_monthly_usage(db, current_user.id)
    return UsageStatsResponse(**data)


@router.get("/history", response_model=UsageHistoryResponse)
def get_usage_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return paginated usage log entries for the last *days* days."""
    since = datetime.utcnow() - timedelta(days=days)
    base_q = (
        db.query(UsageLog)
        .filter(UsageLog.user_id == current_user.id, UsageLog.timestamp >= since)
    )
    total = base_q.count()
    logs = base_q.order_by(UsageLog.timestamp.desc()).offset(skip).limit(limit).all()

    return UsageHistoryResponse(
        usage_logs=[UsageLogResponse.model_validate(log) for log in logs],
        total=total,
        skip=skip,
        limit=limit,
    )
