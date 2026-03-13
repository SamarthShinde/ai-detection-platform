from pydantic import BaseModel, EmailStr, Field, computed_field
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    subscription_tier: str
    is_verified: bool = False
    email_2fa_enabled: bool = False
    created_at: datetime

    # Alias so frontend can use user.tier
    @computed_field  # type: ignore[misc]
    @property
    def tier(self) -> str:
        return self.subscription_tier

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class DetectionResponse(BaseModel):
    id: int
    user_id: int
    file_hash: str
    file_type: str
    processing_status: str
    ai_probability: Optional[float] = None
    confidence_score: Optional[float] = None
    detection_methods: Optional[str] = None
    result_json: Optional[dict] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DetectionListResponse(BaseModel):
    items: List[DetectionResponse]
    total: int
    page: int
    per_page: int


class UsageStatsResponse(BaseModel):
    scans_used: int
    scans_limit: int
    api_calls: int
    renewal_date: datetime
