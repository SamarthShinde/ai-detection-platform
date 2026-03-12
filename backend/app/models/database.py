from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Index
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """Platform user with subscription tier."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    subscription_tier = Column(String(20), default="free", nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    email_2fa_enabled = Column(Boolean, default=False, nullable=False)
    last_2fa_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    detections = relationship("Detection", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")


class Detection(Base):
    """File detection record tracking AI analysis results."""
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    file_type = Column(String(10), nullable=False)  # "video" or "image"
    original_filename = Column(String(255), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_status = Column(String(20), default="pending", nullable=False)
    ai_probability = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    detection_methods = Column(String(500), nullable=True)
    result_json = Column(JSON, nullable=True)
    error_message = Column(String(500), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    celery_task_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="detections")

    __table_args__ = (
        Index("ix_detections_user_status", "user_id", "processing_status"),
        Index("ix_detections_created_at", "created_at"),
    )


class APIKey(Base):
    """Hashed API keys for programmatic access."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(64), nullable=False, index=True)
    name = Column(String(100), nullable=False, default="Default")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index("ix_api_keys_user_active", "user_id", "active"),
    )


class UsageLog(Base):
    """Per-request usage tracking for quota enforcement."""
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    endpoint = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=False, default=200)
    error_message = Column(String(500), nullable=True)

    user = relationship("User", back_populates="usage_logs")

    __table_args__ = (
        Index("ix_usage_logs_user_timestamp", "user_id", "timestamp"),
    )
