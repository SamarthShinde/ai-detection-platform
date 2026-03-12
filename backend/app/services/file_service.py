"""File validation, hashing, and storage service."""
import hashlib
import logging
import os
from pathlib import Path

from fastapi import UploadFile

logger = logging.getLogger(__name__)

_UPLOADS_ROOT = Path(__file__).resolve().parents[3] / "uploads"

_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

_VIDEO_MAX_BYTES = 100 * 1024 * 1024   # 100 MB
_IMAGE_MAX_BYTES = 10 * 1024 * 1024    # 10 MB

_CHUNK = 8192  # read in 8 KB chunks


class FileService:
    """Handles file validation, SHA256 hashing, and local storage."""

    # ── Validation ────────────────────────────────────────────────────────────

    def validate_video_file(self, file: UploadFile) -> tuple[bool, str]:
        """Return (True, '') if valid video, else (False, error_message)."""
        ext = Path(file.filename or "").suffix.lower()
        if ext not in _VIDEO_EXTENSIONS:
            return False, f"Invalid file type. Allowed: {', '.join(_VIDEO_EXTENSIONS)}"
        if file.size and file.size > _VIDEO_MAX_BYTES:
            return False, "File size exceeds maximum of 100 MB"
        return True, ""

    def validate_image_file(self, file: UploadFile) -> tuple[bool, str]:
        """Return (True, '') if valid image, else (False, error_message)."""
        ext = Path(file.filename or "").suffix.lower()
        if ext not in _IMAGE_EXTENSIONS:
            return False, f"Invalid file type. Allowed: {', '.join(_IMAGE_EXTENSIONS)}"
        if file.size and file.size > _IMAGE_MAX_BYTES:
            return False, "File size exceeds maximum of 10 MB"
        return True, ""

    # ── Hashing ───────────────────────────────────────────────────────────────

    async def compute_file_hash(self, file: UploadFile) -> str:
        """Read the entire upload and return its SHA256 hex digest."""
        sha256 = hashlib.sha256()
        await file.seek(0)
        while chunk := await file.read(_CHUNK):
            sha256.update(chunk)
        await file.seek(0)  # rewind so callers can still read the file
        return sha256.hexdigest()

    # ── Storage ───────────────────────────────────────────────────────────────

    def _file_dir(self, user_id: int, file_hash: str) -> Path:
        return _UPLOADS_ROOT / f"user_{user_id}" / file_hash

    def file_exists_locally(self, user_id: int, file_hash: str) -> bool:
        """True if the file directory already exists (already uploaded)."""
        return self._file_dir(user_id, file_hash).exists()

    async def save_file_to_disk(
        self,
        file: UploadFile,
        user_id: int,
        file_hash: str,
        file_type: str,
    ) -> str:
        """
        Save *file* to uploads/user_{user_id}/{file_hash}/{file_hash}.{ext}.

        Returns the absolute path as a string.
        Skips writing if the exact file path already exists.
        """
        ext = Path(file.filename or f"file.{file_type}").suffix.lower()
        dest_dir = self._file_dir(user_id, file_hash)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / f"{file_hash}{ext}"

        if dest_path.exists():
            logger.debug("File already on disk, skipping write", extra={"path": str(dest_path)})
            return str(dest_path)

        await file.seek(0)
        with dest_path.open("wb") as fh:
            while chunk := await file.read(_CHUNK):
                fh.write(chunk)

        logger.info("File saved", extra={"path": str(dest_path), "user_id": user_id})
        return str(dest_path)

    def get_file_path(self, user_id: int, file_hash: str, original_filename: str) -> str:
        """Reconstruct the stored file path from metadata."""
        ext = Path(original_filename).suffix.lower()
        return str(self._file_dir(user_id, file_hash) / f"{file_hash}{ext}")

    def delete_file(self, user_id: int, file_hash: str) -> None:
        """Remove the file directory for a given user + hash (best-effort)."""
        dest_dir = self._file_dir(user_id, file_hash)
        if not dest_dir.exists():
            return
        for child in dest_dir.iterdir():
            child.unlink(missing_ok=True)
        try:
            dest_dir.rmdir()
        except OSError:
            pass
        logger.info("File deleted", extra={"user_id": user_id, "file_hash": file_hash})


file_service = FileService()
