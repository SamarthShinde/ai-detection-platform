"""Authentication service: password hashing, JWT creation/validation, user management."""
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.database import User
from app.utils.config import settings

logger = logging.getLogger(__name__)

_PASSWORD_RE = re.compile(r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$")


class AuthService:
    """Handles password hashing, JWT tokens, and user CRUD."""

    # ── Passwords ─────────────────────────────────────────────────────────────

    def hash_password(self, password: str) -> str:
        """Hash a plain-text password with bcrypt (cost=12)."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()

    def verify_password(self, plain: str, hashed: str) -> bool:
        """Return True if *plain* matches the stored bcrypt hash."""
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    # ── JWT ───────────────────────────────────────────────────────────────────

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a signed JWT access token."""
        payload = data.copy()
        now = datetime.utcnow()
        expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        payload.update({"iat": now, "exp": expire})
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def decode_token(self, token: str) -> dict:
        """Decode and validate a JWT. Raises HTTPException on failure."""
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError as exc:
            logger.warning("JWT decode failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # ── Users ─────────────────────────────────────────────────────────────────

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Return User by email or None."""
        return db.query(User).filter(User.email == email.lower()).first()

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Return User by primary key or None."""
        return db.query(User).filter(User.id == user_id).first()

    def create_user(self, db: Session, email: str, password: str, full_name: str) -> User:
        """
        Register a new user.

        Raises:
            HTTPException 400 – weak password
            HTTPException 409 – email already registered
        """
        if not _PASSWORD_RE.match(password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Password must be at least 8 characters and contain "
                    "one uppercase letter, one digit, and one special character."
                ),
            )

        if self.get_user_by_email(db, email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=email.lower(),
            password_hash=self.hash_password(password),
            full_name=full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("New user registered", extra={"user_id": user.id, "email": user.email})
        return user

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Return authenticated User or None (never reveals which field failed)."""
        user = self.get_user_by_email(db, email)
        if not user or not self.verify_password(password, user.password_hash):
            return None
        return user


auth_service = AuthService()
