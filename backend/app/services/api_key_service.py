"""API key creation, validation, listing, and revocation."""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.database import APIKey, User
from app.utils.api_key_utils import api_key_utils

logger = logging.getLogger(__name__)


class APIKeyService:
    """Manages the full lifecycle of API keys."""

    def create_api_key(self, db: Session, user_id: int, name: str) -> tuple[str, APIKey]:
        """
        Generate a new API key for *user_id*.

        Returns (plain_key, APIKey) — the plain key is shown to the user once only.
        """
        plain_key = api_key_utils.generate_api_key()
        key_hash = api_key_utils.hash_api_key(plain_key)

        api_key = APIKey(
            user_id=user_id,
            key_hash=key_hash,
            name=name,
            created_at=datetime.utcnow(),
            active=True,
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        logger.info("API key created", extra={"user_id": user_id, "key_id": api_key.id, "key_name": name})
        return plain_key, api_key

    def validate_api_key(self, db: Session, plain_key: str) -> Optional[User]:
        """
        Verify *plain_key* against stored hashes.

        Returns the owning User and updates last_used, or None if invalid/inactive.
        """
        key_hash = api_key_utils.hash_api_key(plain_key)
        api_key = db.query(APIKey).filter(APIKey.key_hash == key_hash, APIKey.active == True).first()
        if not api_key:
            return None

        api_key.last_used = datetime.utcnow()
        db.commit()

        user = db.query(User).filter(User.id == api_key.user_id).first()
        return user

    def list_api_keys(self, db: Session, user_id: int) -> list[dict]:
        """Return active keys for *user_id* with masked key previews."""
        keys = db.query(APIKey).filter(APIKey.user_id == user_id, APIKey.active == True).all()
        return [
            {
                "id": k.id,
                "name": k.name,
                "created_at": k.created_at,
                "last_used": k.last_used,
                "key_preview": api_key_utils.mask_key(k.key_hash),
            }
            for k in keys
        ]

    def revoke_api_key(self, db: Session, key_id: int, user_id: int) -> bool:
        """
        Deactivate the key with *key_id* owned by *user_id*.

        Returns True if revoked, False if not found.
        """
        api_key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user_id, APIKey.active == True).first()
        if not api_key:
            return False
        api_key.active = False
        db.commit()
        logger.info("API key revoked", extra={"key_id": key_id, "user_id": user_id})
        return True

    def revoke_all_api_keys(self, db: Session, user_id: int) -> None:
        """Deactivate all keys for *user_id*."""
        db.query(APIKey).filter(APIKey.user_id == user_id).update({"active": False})
        db.commit()


api_key_service = APIKeyService()
