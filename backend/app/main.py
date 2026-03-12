import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime

import redis as redis_sync
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from pythonjsonlogger import jsonlogger
from sqlalchemy import text

from app.middleware.rate_limit_middleware import rate_limit_middleware_fn
from app.models.database import Base
from app.routes import auth as auth_router
from app.routes import api_keys as api_keys_router
from app.routes import detection as detection_router
from app.routes import usage as usage_router
from app.services.monitoring_service import monitoring_service
from app.utils.config import settings
from app.utils.db import engine

# ── Logging setup ────────────────────────────────────────────────────────────
handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
logging.basicConfig(level=settings.LOG_LEVEL, handlers=[handler])
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL connection OK")
    except Exception as exc:
        logger.error("PostgreSQL connection failed", extra={"error": str(exc)})
        raise

    try:
        r = redis_sync.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        logger.info("Redis connection OK")
    except Exception as exc:
        logger.warning("Redis connection failed", extra={"error": str(exc)})

    logger.info("Application startup complete", extra={"environment": settings.ENVIRONMENT})
    yield

    # Shutdown
    engine.dispose()
    logger.info("Application shutdown complete")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Detection Platform",
    description="Deepfake & synthetic media detection API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Middleware ────────────────────────────────────────────────────────────────
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    return await rate_limit_middleware_fn(request, call_next)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    logger.debug(
        "Request handled",
        extra={"method": request.method, "path": request.url.path, "ms": elapsed_ms, "status": response.status_code},
    )
    return response


# ── Exception handlers ────────────────────────────────────────────────────────
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", extra={"error": str(exc), "path": request.url.path})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(detection_router.router)
app.include_router(api_keys_router.router)
app.include_router(usage_router.router)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Liveness probe — returns current server time."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"}


@app.get("/health/detailed", tags=["System"])
async def health_detailed():
    """Detailed system health: database, Redis, Celery worker status."""
    return monitoring_service.get_system_metrics()


@app.get("/", tags=["System"])
async def root():
    return {"message": "AI Detection Platform API", "docs": "/docs"}
