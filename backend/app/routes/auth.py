"""Authentication routes: register, verify-email, login, 2FA, refresh, me, logout."""
import asyncio
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.database import User
from app.schemas import UserResponse
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    ResendOTPRequest,
    TokenResponse,
    UpdateProfileRequest,
    Verify2FARequest,
    VerifyEmailRequest,
)
from app.services.auth_service import auth_service
from app.utils.config import settings
from app.utils.db import get_db
from app.utils.dependencies import get_current_user
from app.utils.email_service import email_service
from app.utils.otp_service import otp_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Short-lived token used during the 2FA challenge (5 minutes)
_TEMP_TOKEN_EXPIRY = timedelta(minutes=5)


# ── Register ──────────────────────────────────────────────────────────────────


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Create account and send email-verification OTP.

    The user cannot log in until they verify their email.
    """
    user = auth_service.create_user(db, payload.email, payload.password, payload.full_name)

    otp = otp_service.generate_otp()
    otp_service.store_otp(user.email, otp, "email_verification")
    otp_service.set_resend_cooldown(user.email)
    background_tasks.add_task(email_service.send_verification_email, user.email, otp)

    return {
        "message": "Account created. Check your email for the verification code.",
        "email": user.email,
    }


# ── Verify email ──────────────────────────────────────────────────────────────


@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Submit the email-verification OTP."""
    user = auth_service.get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_verified:
        return {"message": "Email already verified.", "status": "verified"}

    if not otp_service.verify_otp(user.email, payload.otp, "email_verification"):
        remaining = otp_service.remaining_attempts(user.email, "email_verification")
        if remaining == 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Request a new code.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP. {remaining} attempt(s) remaining.",
        )

    auth_service.mark_verified(db, user.id)
    logger.info("Email verified", extra={"user_id": user.id})
    return {"message": "Email verified. You can now log in.", "status": "verified"}


# ── Login ─────────────────────────────────────────────────────────────────────


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Authenticate. Returns JWT directly, or a temp_token if 2FA is enabled."""
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Check your inbox for a verification code.",
        )

    if user.email_2fa_enabled and settings.ENABLE_EMAIL_2FA:
        otp = otp_service.generate_otp()
        otp_service.store_otp(user.email, otp, "2fa")
        background_tasks.add_task(email_service.send_2fa_email, user.email, otp)

        temp_token = auth_service.create_access_token(
            {"sub": str(user.id), "scope": "2fa"},
            expires_delta=_TEMP_TOKEN_EXPIRY,
        )
        logger.info("2FA challenge issued", extra={"user_id": user.id})
        return LoginResponse(requires_2fa=True, temp_token=temp_token, message="2FA code sent to your email.")

    token = auth_service.create_access_token({"sub": str(user.id)})
    logger.info("User logged in", extra={"user_id": user.id})
    return LoginResponse(access_token=token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


# ── Verify 2FA ────────────────────────────────────────────────────────────────


@router.post("/verify-2fa", response_model=TokenResponse)
def verify_2fa(
    payload: Verify2FARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exchange a valid 2FA OTP + temp_token for a permanent access token."""
    if not otp_service.verify_otp(current_user.email, payload.otp, "2fa"):
        remaining = otp_service.remaining_attempts(current_user.email, "2fa")
        if remaining == 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Log in again to get a new code.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid 2FA code. {remaining} attempt(s) remaining.",
        )

    token = auth_service.create_access_token({"sub": str(current_user.id)})
    logger.info("2FA verified, token issued", extra={"user_id": current_user.id})
    return TokenResponse(access_token=token)


# ── Resend OTP ────────────────────────────────────────────────────────────────


@router.post("/resend-otp")
async def resend_otp(payload: ResendOTPRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Re-send a verification OTP (subject to 60-second cooldown)."""
    user = auth_service.get_user_by_email(db, payload.email)
    # Never reveal whether the email exists
    if not user or user.is_verified:
        return {"message": "If that address is registered and unverified, a new code has been sent."}

    if not otp_service.resend_allowed(user.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait 60 seconds before requesting another code.",
        )

    otp = otp_service.generate_otp()
    otp_service.store_otp(user.email, otp, "email_verification")
    otp_service.set_resend_cooldown(user.email)
    background_tasks.add_task(email_service.send_verification_email, user.email, otp)

    return {"message": "Verification code sent. Check your email."}


# ── Toggle 2FA ────────────────────────────────────────────────────────────────


@router.post("/toggle-2fa")
def toggle_2fa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Enable or disable email 2FA for the current user."""
    new_state = auth_service.toggle_2fa(db, current_user.id)
    return {"email_2fa_enabled": new_state}


# ── Refresh ───────────────────────────────────────────────────────────────────


@router.post("/refresh", response_model=TokenResponse)
def refresh(current_user: User = Depends(get_current_user)):
    """Issue a new access token for the currently authenticated user."""
    token = auth_service.create_access_token({"sub": str(current_user.id)})
    return TokenResponse(access_token=token)


# ── Me ────────────────────────────────────────────────────────────────────────


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


# ── Update profile ────────────────────────────────────────────────────────────


@router.put("/me", response_model=UserResponse)
def update_me(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the authenticated user's profile (full name)."""
    current_user.full_name = payload.full_name.strip()
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    logger.info("Profile updated", extra={"user_id": current_user.id})
    return current_user


# ── Change password ───────────────────────────────────────────────────────────


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the authenticated user's password after verifying the current one."""
    if not auth_service.verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.password_hash = auth_service.hash_password(payload.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    logger.info("Password changed", extra={"user_id": current_user.id})
    return {"message": "Password changed successfully"}


# ── Delete account ────────────────────────────────────────────────────────────


@router.delete("/me")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently delete the authenticated user's account and all associated data."""
    user_id = current_user.id
    db.delete(current_user)
    db.commit()
    logger.info("Account deleted", extra={"user_id": user_id})
    return {"message": "Account deleted successfully"}


# ── Logout ────────────────────────────────────────────────────────────────────


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Invalidate the current session (client should discard the token)."""
    logger.info("User logged out", extra={"user_id": current_user.id})
    return {"message": "Logged out successfully"}
