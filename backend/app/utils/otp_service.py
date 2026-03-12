"""OTP generation, storage (Redis), and verification."""
import logging
import random
import string

import redis

from app.utils.config import settings

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
_RESEND_COOLDOWN_S = 60  # seconds between resend requests


class OTPService:
    """Manages OTP lifecycle using Redis."""

    def __init__(self) -> None:
        self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    # ── Keys ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _otp_key(otp_type: str, identifier: str) -> str:
        return f"otp:{otp_type}:{identifier}"

    @staticmethod
    def _attempts_key(otp_type: str, identifier: str) -> str:
        return f"otp_attempts:{otp_type}:{identifier}"

    @staticmethod
    def _resend_key(identifier: str) -> str:
        return f"otp_resend:{identifier}"

    # ── Core ──────────────────────────────────────────────────────────────────

    def generate_otp(self) -> str:
        """Return a random numeric OTP of the configured length."""
        return "".join(random.choices(string.digits, k=settings.OTP_LENGTH))

    def store_otp(self, identifier: str, otp: str, otp_type: str = "email_verification") -> None:
        """Persist OTP in Redis with expiry; reset attempt counter."""
        expiry_s = settings.OTP_EXPIRY_MINUTES * 60
        pipe = self._redis.pipeline()
        pipe.set(self._otp_key(otp_type, identifier), otp, ex=expiry_s)
        pipe.set(self._attempts_key(otp_type, identifier), 0, ex=expiry_s)
        pipe.execute()
        logger.debug("OTP stored", extra={"type": otp_type, "identifier": identifier})

    def verify_otp(self, identifier: str, otp: str, otp_type: str = "email_verification") -> bool:
        """
        Validate OTP.

        Returns True and cleans up Redis on success.
        Returns False on mismatch, expiry, or too many attempts.
        """
        otp_key = self._otp_key(otp_type, identifier)
        attempts_key = self._attempts_key(otp_type, identifier)

        stored = self._redis.get(otp_key)
        if stored is None:
            logger.debug("OTP not found or expired", extra={"type": otp_type})
            return False

        attempts = int(self._redis.get(attempts_key) or 0)
        if attempts >= _MAX_ATTEMPTS:
            logger.warning("OTP max attempts exceeded", extra={"identifier": identifier})
            return False

        if stored != otp:
            self._redis.incr(attempts_key)
            logger.debug("OTP mismatch", extra={"type": otp_type, "attempts": attempts + 1})
            return False

        # Valid — clean up
        pipe = self._redis.pipeline()
        pipe.delete(otp_key)
        pipe.delete(attempts_key)
        pipe.execute()
        return True

    def remaining_attempts(self, identifier: str, otp_type: str = "email_verification") -> int:
        """Return how many verification attempts are left."""
        attempts = int(self._redis.get(self._attempts_key(otp_type, identifier)) or 0)
        return max(0, _MAX_ATTEMPTS - attempts)

    def resend_allowed(self, identifier: str) -> bool:
        """True if the user may request a new OTP (cooldown has passed)."""
        return self._redis.get(self._resend_key(identifier)) is None

    def set_resend_cooldown(self, identifier: str) -> None:
        """Start the resend cooldown timer."""
        self._redis.set(self._resend_key(identifier), "1", ex=_RESEND_COOLDOWN_S)


otp_service = OTPService()
