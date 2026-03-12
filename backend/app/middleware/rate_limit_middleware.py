"""Rate limiting middleware — enforces per-user per-minute/hour limits via Redis."""
import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt

from app.services.rate_limit_service import rate_limit_service
from app.utils.config import settings

logger = logging.getLogger(__name__)

# Paths that bypass rate limiting entirely
_PUBLIC_PATHS = {"/health", "/health/detailed", "/docs", "/redoc", "/openapi.json", "/"}
_PUBLIC_PREFIXES = ("/auth/",)


async def rate_limit_middleware_fn(request: Request, call_next):
    """
    HTTP middleware that enforces per-user rate limits for protected endpoints.

    Public endpoints (auth, health, docs) are skipped.
    Requests without a valid Bearer token are passed through — the endpoint
    itself will return 401.
    """
    path = request.url.path

    # Skip public paths
    if path in _PUBLIC_PATHS or any(path.startswith(p) for p in _PUBLIC_PREFIXES):
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return await call_next(request)

    token = auth_header[7:]

    # Decode token — on failure just let the endpoint handle the 401
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return await call_next(request)
    except JWTError:
        return await call_next(request)

    # Load subscription tier from DB
    tier = _get_user_tier(user_id)

    # Check rate limit
    is_allowed, limit_info = rate_limit_service.check_rate_limit(str(user_id), tier)

    if not is_allowed:
        headers = rate_limit_service.get_rate_limit_headers(str(user_id), tier)
        logger.warning(
            "Rate limit exceeded",
            extra={"user_id": user_id, "tier": tier, "path": path},
        )
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Upgrade your plan for higher limits."},
            headers=headers,
        )

    response = await call_next(request)

    # Attach rate limit headers to every response
    headers = rate_limit_service.get_rate_limit_headers(str(user_id), tier)
    for name, value in headers.items():
        response.headers[name] = value

    return response


def _get_user_tier(user_id: str) -> str:
    """Return subscription_tier for *user_id*, defaulting to 'free' on any error."""
    try:
        from app.models.database import User
        from app.utils.db import SessionLocal

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            return (user.subscription_tier if user and user.subscription_tier else "free")
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Could not fetch user tier", extra={"user_id": user_id, "error": str(exc)})
        return "free"
