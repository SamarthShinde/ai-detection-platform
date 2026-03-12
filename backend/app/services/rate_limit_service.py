"""Redis-based rate limiting per user and subscription tier."""
import logging
import time
from typing import Optional

import redis as redis_sync

from app.utils.config import settings

logger = logging.getLogger(__name__)

# Rate limit config per tier (-1 = unlimited)
RATE_LIMIT_CONFIG: dict[str, dict] = {
    "free":       {"requests_per_minute": 2,  "requests_per_hour": 50},
    "pro":        {"requests_per_minute": 30, "requests_per_hour": 1000},
    "enterprise": {"requests_per_minute": -1, "requests_per_hour": -1},
}

_DEFAULT_TIER = "free"


class RateLimitService:
    """Distributed rate limiting backed by Redis atomic counters."""

    def __init__(self) -> None:
        self._redis: Optional[redis_sync.Redis] = None

    def _get_redis(self) -> redis_sync.Redis:
        if self._redis is None:
            self._redis = redis_sync.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=2,
                decode_responses=True,
            )
        return self._redis

    # ── Config helpers ────────────────────────────────────────────────────────

    def get_rate_limit_config(self, subscription_tier: str) -> dict:
        """Return rate limit config for *subscription_tier*."""
        return RATE_LIMIT_CONFIG.get(subscription_tier, RATE_LIMIT_CONFIG[_DEFAULT_TIER])

    # ── Core check ────────────────────────────────────────────────────────────

    def check_rate_limit(self, identifier: str, tier: str) -> tuple[bool, dict]:
        """
        Atomically check and increment rate limit counters for *identifier*.

        Returns (True, info_dict) when the request is allowed,
        (False, info_dict) when it should be rejected with 429.
        """
        config = self.get_rate_limit_config(tier)
        rpm_limit = config["requests_per_minute"]
        rph_limit = config["requests_per_hour"]

        # Unlimited tier — skip Redis entirely
        if rpm_limit == -1 and rph_limit == -1:
            return True, {"remaining": -1, "reset_at": None}

        r = self._get_redis()

        minute_key = f"ratelimit:minute:{identifier}"
        hour_key = f"ratelimit:hour:{identifier}"

        now = int(time.time())
        minute_reset = now + 60 - (now % 60)
        hour_reset = now + 3600 - (now % 3600)

        try:
            pipe = r.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)
            results = pipe.execute()

            minute_count = results[0]
            hour_count = results[2]

            # Check minute limit
            if rpm_limit != -1 and minute_count > rpm_limit:
                return False, {
                    "remaining": 0,
                    "reset_at": minute_reset,
                    "limit": rpm_limit,
                    "window": "minute",
                }

            # Check hour limit
            if rph_limit != -1 and hour_count > rph_limit:
                return False, {
                    "remaining": 0,
                    "reset_at": hour_reset,
                    "limit": rph_limit,
                    "window": "hour",
                }

            minute_remaining = max(0, rpm_limit - minute_count) if rpm_limit != -1 else -1
            return True, {
                "remaining": minute_remaining,
                "reset_at": minute_reset,
                "limit": rpm_limit,
            }

        except Exception as exc:
            # If Redis is unavailable, fail open (allow the request)
            logger.warning("Rate limit Redis error — failing open", extra={"error": str(exc)})
            return True, {"remaining": -1, "reset_at": None}

    # ── Header helpers ────────────────────────────────────────────────────────

    def get_rate_limit_headers(self, identifier: str, tier: str) -> dict[str, str]:
        """Return X-RateLimit-* headers for the current state of *identifier*."""
        config = self.get_rate_limit_config(tier)
        rpm_limit = config["requests_per_minute"]

        if rpm_limit == -1:
            return {
                "X-RateLimit-Limit": "unlimited",
                "X-RateLimit-Remaining": "unlimited",
                "X-RateLimit-Reset": "0",
            }

        r = self._get_redis()
        minute_key = f"ratelimit:minute:{identifier}"
        now = int(time.time())
        reset_at = now + 60 - (now % 60)

        try:
            current = int(r.get(minute_key) or 0)
            remaining = max(0, rpm_limit - current)
        except Exception:
            remaining = rpm_limit

        return {
            "X-RateLimit-Limit": str(rpm_limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_at),
        }

    # ── Admin ─────────────────────────────────────────────────────────────────

    def reset_user_limits(self, identifier: str) -> None:
        """Delete rate limit keys for *identifier* (use on logout or tier change)."""
        r = self._get_redis()
        r.delete(f"ratelimit:minute:{identifier}", f"ratelimit:hour:{identifier}")
        logger.info("Rate limit keys reset", extra={"identifier": identifier})


rate_limit_service = RateLimitService()
