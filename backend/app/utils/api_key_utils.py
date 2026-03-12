"""Secure API key generation and hashing utilities."""
import hashlib
import secrets
import string


_ALPHABET = string.ascii_letters + string.digits
_PREFIX = "sk_live_"


class APIKeyUtils:
    """Handles secure API key generation and SHA256 hashing."""

    def generate_api_key(self, length: int = 40) -> str:
        """Return a cryptographically random API key with a fixed prefix."""
        random_part = "".join(secrets.choice(_ALPHABET) for _ in range(length))
        return f"{_PREFIX}{random_part}"

    def hash_api_key(self, key: str) -> str:
        """Return the SHA256 hex digest of *key* (stored in DB, never the plain key)."""
        return hashlib.sha256(key.encode()).hexdigest()

    def verify_api_key(self, plain_key: str, hashed_key: str) -> bool:
        """Constant-time comparison of plain_key against a stored hash."""
        return secrets.compare_digest(self.hash_api_key(plain_key), hashed_key)

    def mask_key(self, key_hash: str) -> str:
        """Return a display-safe string like 'sk_live_...abcd' using the hash tail."""
        return f"{_PREFIX}...{key_hash[-6:]}"


api_key_utils = APIKeyUtils()
