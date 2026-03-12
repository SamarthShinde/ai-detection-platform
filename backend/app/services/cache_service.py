"""Cache service — avoids re-running ML inference on identical files (same hash)."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.database import DetectionCache

logger = logging.getLogger(__name__)


class CacheService:
    """DB-backed result cache keyed by file hash."""

    def get_cached_result(self, db: Session, file_hash: str) -> Optional[dict]:
        """
        Return cached result_json for *file_hash*, or None if not found.
        Increments the hit counter and updates last_hit_at on a cache hit.
        """
        entry = db.query(DetectionCache).filter(DetectionCache.file_hash == file_hash).first()
        if entry is None:
            return None

        entry.hits += 1
        entry.last_hit_at = datetime.utcnow()
        db.commit()

        logger.info(
            "Cache hit",
            extra={"file_hash": file_hash, "hits": entry.hits},
        )
        return entry.result_json

    def cache_result(self, db: Session, file_hash: str, file_type: str, result: dict) -> None:
        """
        Store *result* in the cache under *file_hash*.
        If an entry already exists for this hash it is overwritten.
        """
        existing = db.query(DetectionCache).filter(DetectionCache.file_hash == file_hash).first()
        if existing:
            existing.result_json = result
            existing.file_type = file_type
            existing.last_hit_at = None
        else:
            entry = DetectionCache(
                file_hash=file_hash,
                file_type=file_type,
                result_json=result,
                hits=0,
                created_at=datetime.utcnow(),
            )
            db.add(entry)
        db.commit()
        logger.debug("Result cached", extra={"file_hash": file_hash, "file_type": file_type})

    def clear_old_cache(self, db: Session, days: int = 30) -> int:
        """
        Delete cache entries older than *days* days.
        Returns the number of rows deleted.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = (
            db.query(DetectionCache)
            .filter(DetectionCache.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        logger.info("Cache cleared", extra={"deleted": deleted, "older_than_days": days})
        return deleted

    def get_cache_stats(self, db: Session) -> dict:
        """Return total entries and total hits for the cache."""
        total = db.query(DetectionCache).count()
        total_hits = db.query(DetectionCache).with_entities(
            DetectionCache.hits
        ).all()
        hits_sum = sum(h[0] for h in total_hits) if total_hits else 0
        return {"total_entries": total, "total_hits": hits_sum}


cache_service = CacheService()
