"""
config.py
─────────
Centralised application settings loaded from environment variables.

Supports two modes controlled by the ENVIRONMENT variable:
  development (default) — relaxed, allows mock LLM, empty SMTP, SQLite, verbose logs
  production            — strict, fails fast on missing credentials, Redis mandatory

Fail-fast rules for production startup:
  - OPENAI_API_KEY must be set
  - SMTP_USER + SMTP_PASS must be set
  - DATABASE_URL should point to PostgreSQL (warned if sqlite is used)
"""

import os
import sys
import logging
from dotenv import load_dotenv

# ── Load .env from workspace root ─────────────────────────────────────────────
_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(dotenv_path=_env_path)

# ── Determine environment mode first ─────────────────────────────────────────
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower().strip()
IS_PRODUCTION: bool = ENVIRONMENT == "production"

# ── Collect all settings from environment ─────────────────────────────────────
class Settings:
    # Core
    ENVIRONMENT: str        = ENVIRONMENT
    IS_PRODUCTION: bool     = IS_PRODUCTION

    # Database
    DATABASE_URL: str       = os.getenv("DATABASE_URL", "sqlite:///./seeroo_travels.db")

    # Server
    HOST: str               = os.getenv("HOST", "127.0.0.1")
    PORT: int               = int(os.getenv("PORT", "8000"))

    # CORS — strict in production
    CORS_ORIGINS: list      = (
        [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
        if IS_PRODUCTION
        else ["*"]
    )

    # OpenAI
    OPENAI_API_KEY: str     = os.getenv("OPENAI_API_KEY", "")

    # SMTP
    SMTP_HOST: str          = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int          = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str          = os.getenv("SMTP_USER", "")
    SMTP_PASS: str          = os.getenv("SMTP_PASS", "")

    # Redis
    REDIS_URL: str          = os.getenv("REDIS_URL", "")  # e.g. redis://localhost:6379/0

    # Request limits
    MAX_REQUEST_SIZE_BYTES: int = int(os.getenv("MAX_REQUEST_SIZE_BYTES", str(1 * 1024 * 1024)))  # 1 MB
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

    # API versioning prefix
    API_PREFIX: str         = "/api/v1"

    # Log level
    LOG_LEVEL: str          = os.getenv("LOG_LEVEL", "WARNING" if IS_PRODUCTION else "INFO")
    LOG_JSON: bool          = os.getenv("LOG_JSON", "true" if IS_PRODUCTION else "false").lower() == "true"


settings = Settings()


# ── Production Fail-Fast Startup Checks ───────────────────────────────────────
def run_startup_checks() -> None:
    """
    Validates required environment variables in production mode.
    Exits the process with a descriptive error if any check fails.
    Called once at application startup from main.py.
    """
    if not IS_PRODUCTION:
        return  # No strict checks in development

    errors = []

    if not settings.OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is required in production (MockChatModel is disabled).")

    if not settings.SMTP_USER or not settings.SMTP_PASS:
        errors.append("SMTP_USER and SMTP_PASS are required in production for transactional email delivery.")

    if settings.DATABASE_URL.startswith("sqlite"):
        # Warn but don't fail — some production setups might intentionally use SQLite
        print(
            "[WARNING] ENVIRONMENT=production but DATABASE_URL points to SQLite. "
            "Consider switching to PostgreSQL for production workloads.",
            file=sys.stderr,
        )

    if not settings.REDIS_URL:
        errors.append(
            "REDIS_URL is required in production for persistent rate limiting and agent memory checkpoints."
        )

    if not settings.CORS_ORIGINS:
        errors.append(
            "CORS_ORIGINS must be explicitly set in production (e.g. CORS_ORIGINS=https://yourdomain.com). "
            "Wildcard '*' is disabled in production mode."
        )

    if errors:
        print("\n[FATAL] Production startup checks failed:", file=sys.stderr)
        for err in errors:
            print(f"  ✗ {err}", file=sys.stderr)
        print("\nSet ENVIRONMENT=development to bypass these checks during local development.\n", file=sys.stderr)
        sys.exit(1)
