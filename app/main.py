"""
main.py
───────
FastAPI application factory for Seeroo Travels Attock API.

Phase 7 additions:
  - Structured JSON logging (production) / coloured dev logging.
  - Production fail-fast startup checks (missing keys → immediate exit).
  - Strict CORS policy in production (CORS_ORIGINS env var).
  - Request size limit middleware (MAX_REQUEST_SIZE_BYTES).
  - Request timeout middleware (REQUEST_TIMEOUT_SECONDS).
  - Enhanced /api/v1/health endpoint with dependency probes.
  - API version prefix /api/v1/ on all routes.
"""

import asyncio
import logging
import os
import time

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

# ── 1. Structured logging must be first ──────────────────────────────────────
from app.core.logging_config import setup_logging
from app.core.config import settings, run_startup_checks

setup_logging(json_output=settings.LOG_JSON, level=settings.LOG_LEVEL)
logger = logging.getLogger("seeroo_backend")

# ── 2. Production fail-fast ───────────────────────────────────────────────────
run_startup_checks()

# ── 3. Import models so Base.metadata is populated ───────────────────────────
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.models.user import User        # noqa: F401
from app.models.tour import Tour        # noqa: F401
from app.models.booking import Booking  # noqa: F401
from app.models.email_log import EmailLog  # noqa: F401

from app.routes import tours, bookings, chat
from app.services.tour_service import seed_default_tours

# ── 4. Initialise DB tables ───────────────────────────────────────────────────
try:
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing database: {e}")

# ── 5. Seed default tours ─────────────────────────────────────────────────────
db = SessionLocal()
try:
    logger.info("Seeding default tours...")
    seed_default_tours(db)
    logger.info("Seeding completed.")
except Exception as e:
    logger.error(f"Error seeding database: {e}")
finally:
    db.close()

# ── 6. Create FastAPI app ─────────────────────────────────────────────────────
app = FastAPI(
    title="Seeroo Travels Attock API",
    description=(
        "Production-grade FastAPI backend for AI-powered domestic tour booking. "
        "All API routes versioned under /api/v1/."
    ),
    version="2.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

# ── 7. CORS ───────────────────────────────────────────────────────────────────
_cors_origins = settings.CORS_ORIGINS if settings.IS_PRODUCTION else ["*"]
logger.info(f"CORS origins: {_cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)

# ── 8. Request Size Limit Middleware ──────────────────────────────────────────
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
            if size > settings.MAX_REQUEST_SIZE_BYTES:
                logger.warning(
                    f"Request body too large: {size} bytes "
                    f"(limit: {settings.MAX_REQUEST_SIZE_BYTES})",
                    extra={"route": str(request.url.path)},
                )
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": f"Request body exceeds maximum allowed size of "
                                       f"{settings.MAX_REQUEST_SIZE_BYTES // 1024} KB."},
                )
        except ValueError:
            pass
    return await call_next(request)

# ── 9. Request Timeout Middleware ─────────────────────────────────────────────
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        return await asyncio.wait_for(
            call_next(request),
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.error(
            f"Request timed out after {settings.REQUEST_TIMEOUT_SECONDS}s",
            extra={"route": str(request.url.path)},
        )
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"detail": f"Request timed out after {settings.REQUEST_TIMEOUT_SECONDS} seconds."},
        )

# ── 10. Structured access logging middleware ──────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = int((time.monotonic() - start) * 1000)
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)",
        extra={"route": str(request.url.path)},
    )
    return response

# ── 11. Validation error handler ──────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        f"Validation error on {request.url.path}",
        extra={"route": str(request.url.path), "error": str(exc.errors())},
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "message": "Input validation failed. Check field structures."},
    )

# ── 12. Register API routers ──────────────────────────────────────────────────
app.include_router(tours.router)
app.include_router(bookings.router)
app.include_router(chat.router)

# ── 13. Health Check ──────────────────────────────────────────────────────────
@app.get(f"{settings.API_PREFIX}/health", tags=["System"])
def health_check():
    """
    Probes all critical dependencies and returns degraded status if any fail.
    Safe to call frequently — each probe has a short timeout.
    """
    health: dict = {
        "status":       "ok",
        "environment":  settings.ENVIRONMENT,
        "database":     "unknown",
        "vector_store": "unknown",
        "llm":          "unknown",
        "redis":        "unknown",
    }
    degraded = False

    # ── Database probe ────────────────────────────────────────────────────────
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health["database"] = "connected"
    except Exception as e:
        health["database"] = f"error: {str(e)[:80]}"
        degraded = True

    # ── Vector store probe ────────────────────────────────────────────────────
    try:
        from app.services.vector_store import get_vector_store
        vs = get_vector_store()
        # Attempt a minimal query
        vs.search("health check ping", k=1)
        health["vector_store"] = "connected"
    except Exception as e:
        health["vector_store"] = f"error: {str(e)[:80]}"
        degraded = True

    # ── LLM probe ─────────────────────────────────────────────────────────────
    try:
        from app.ai.llm_provider import get_llm
        llm = get_llm()
        health["llm"] = f"available ({llm.__class__.__name__})"
    except Exception as e:
        health["llm"] = f"error: {str(e)[:80]}"
        degraded = True

    # ── Redis probe ───────────────────────────────────────────────────────────
    if settings.REDIS_URL:
        try:
            import redis as redis_lib
            client = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
            client.ping()
            health["redis"] = "connected"
        except Exception as e:
            health["redis"] = f"error: {str(e)[:80]}"
            degraded = True
    else:
        health["redis"] = "not_configured (SQLite fallback active)"

    if degraded:
        health["status"] = "degraded"

    return JSONResponse(
        status_code=status.HTTP_200_OK if not degraded else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=health,
    )

# ── 14. Static files (MUST be last — catches all unmatched paths) ─────────────
workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app.mount("/", StaticFiles(directory=workspace_dir, html=True), name="static")

logger.info(
    f"Seeroo Travels API v2.0 started — "
    f"env={settings.ENVIRONMENT} prefix={settings.API_PREFIX}"
)
