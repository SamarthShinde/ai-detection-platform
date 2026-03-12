"""Usage tracking and quota enforcement per subscription tier."""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.database import Detection, UsageLog, User

logger = logging.getLogger(__name__)

# ── Quota config ──────────────────────────────────────────────────────────────
# -1 = unlimited
QUOTA_CONFIG: dict[str, dict] = {
    "free":       {"scans_per_month": 5,   "requests_per_minute": 2},
    "pro":        {"scans_per_month": 100,  "requests_per_minute": 30},
    "enterprise": {"scans_per_month": -1,   "requests_per_minute": -1},
}

_DEFAULT_TIER = "free"


class UsageService:
    """Handles usage logging, quota calculation, and tier-based limits."""

    # ── Logging ───────────────────────────────────────────────────────────────

    def track_usage(
        self,
        db: Session,
        user_id: int,
        endpoint: str,
        file_size_bytes: Optional[int],
        processing_time_ms: Optional[int],
        status_code: int,
    ) -> None:
        """Append a UsageLog entry for one request."""
        log = UsageLog(
            user_id=user_id,
            endpoint=endpoint,
            timestamp=datetime.utcnow(),
            file_size_bytes=file_size_bytes,
            processing_time_ms=processing_time_ms,
            status_code=status_code,
        )
        db.add(log)
        db.commit()

    # ── Quota ─────────────────────────────────────────────────────────────────

    def _month_start(self) -> datetime:
        now = datetime.utcnow()
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def _next_month_start(self) -> datetime:
        ms = self._month_start()
        # Jump to month+1 (handle December → January)
        if ms.month == 12:
            return ms.replace(year=ms.year + 1, month=1)
        return ms.replace(month=ms.month + 1)

    def get_monthly_usage(self, db: Session, user_id: int) -> dict:
        """Return scan counts, limits, and renewal date for *user_id*."""
        user = db.query(User).filter(User.id == user_id).first()
        tier = (user.subscription_tier if user else None) or _DEFAULT_TIER
        quota = QUOTA_CONFIG.get(tier, QUOTA_CONFIG[_DEFAULT_TIER])
        limit = quota["scans_per_month"]

        month_start = self._month_start()
        scans_used = (
            db.query(Detection)
            .filter(
                Detection.user_id == user_id,
                Detection.processing_status == "completed",
                Detection.created_at >= month_start,
            )
            .count()
        )

        renewal_date = self._next_month_start()
        remaining = (limit - scans_used) if limit != -1 else None
        percentage = round((scans_used / limit) * 100, 1) if limit > 0 else 0.0

        if limit == -1:
            message = "Unlimited scans (Enterprise)"
        elif remaining == 0:
            message = "Monthly quota reached. Upgrade to continue."
        else:
            message = f"You have {remaining} scan(s) remaining this month."

        return {
            "scans_used": scans_used,
            "scans_limit": limit,
            "scans_percentage": percentage,
            "renewal_date": renewal_date,
            "subscription_tier": tier,
            "message": message,
        }

    def check_quota(self, db: Session, user_id: int) -> tuple[bool, str]:
        """
        Return (True, '') when the user has quota remaining,
        (False, reason) when exhausted.
        """
        data = self.get_monthly_usage(db, user_id)
        limit = data["scans_limit"]
        if limit == -1:
            return True, ""
        if data["scans_used"] >= limit:
            return False, f"Monthly quota of {limit} scan(s) exceeded. Upgrade your plan to continue."
        return True, ""

    def get_request_limit(self, subscription_tier: str) -> int:
        """Return requests-per-minute limit for *subscription_tier*."""
        return QUOTA_CONFIG.get(subscription_tier, QUOTA_CONFIG[_DEFAULT_TIER])["requests_per_minute"]


usage_service = UsageService()
