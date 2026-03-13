"""API key management endpoints."""
import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.database import User
from app.services.api_key_service import api_key_service
from app.utils.db import get_db
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class CreateAPIKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class APIKeyCreatedResponse(BaseModel):
    key: str
    name: str
    created_at: datetime
    message: str


class APIKeyListItemResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    key_preview: str
    is_active: bool = True


class APIKeyListResponse(BaseModel):
    keys: list[APIKeyListItemResponse]


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("", status_code=status.HTTP_201_CREATED, response_model=APIKeyCreatedResponse)
def create_api_key(
    payload: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a new API key. The full key is shown **once only** — save it now."""
    plain_key, api_key = api_key_service.create_api_key(db, current_user.id, payload.name)
    return APIKeyCreatedResponse(
        key=plain_key,
        name=api_key.name,
        created_at=api_key.created_at,
        message="API key created. Save it somewhere safe — you won't be able to see it again.",
    )


@router.get("", response_model=APIKeyListResponse)
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all active API keys for the current user (masked)."""
    keys = api_key_service.list_api_keys(db, current_user.id)
    return APIKeyListResponse(
        keys=[APIKeyListItemResponse(**k) for k in keys]
    )


@router.delete("/{key_id}")
def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke (deactivate) an API key. This cannot be undone."""
    revoked = api_key_service.revoke_api_key(db, key_id, current_user.id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return {"message": "API key revoked successfully"}
