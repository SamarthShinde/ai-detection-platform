"""Authentication routes: register, login, refresh, me, logout."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.database import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas import UserResponse
from app.services.auth_service import auth_service
from app.utils.db import get_db
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    user = auth_service.create_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and return a JWT access token."""
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_service.create_access_token({"sub": str(user.id)})
    logger.info("User logged in", extra={"user_id": user.id})
    return TokenResponse(access_token=token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(current_user: User = Depends(get_current_user)):
    """Issue a new access token for the currently authenticated user."""
    token = auth_service.create_access_token({"sub": str(current_user.id)})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Invalidate the current session (client should discard the token)."""
    logger.info("User logged out", extra={"user_id": current_user.id})
    return {"message": "Logged out successfully"}
