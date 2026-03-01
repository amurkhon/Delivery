"""Centralized configuration from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret")
UNSAFE_JWT_DEFAULT = "change-this-secret"

# CORS - comma-separated origins, e.g. "https://app.example.com,https://www.example.com"
_CORS_ORIGINS_RAW = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://72.61.116.31:3000,http://localhost:5173,http://72.61.116.31:5173",
)
CORS_ORIGINS = [o.strip() for o in _CORS_ORIGINS_RAW.split(",") if o.strip()]

# Uploads
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "5"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if not IS_PRODUCTION else "INFO")


def validate_production_config() -> None:
    """Validate required config for production. Raises if invalid."""
    if not IS_PRODUCTION:
        return

    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL is required in production. Set it in your environment."
        )

    if not JWT_SECRET_KEY or JWT_SECRET_KEY == UNSAFE_JWT_DEFAULT:
        raise ValueError(
            "JWT_SECRET_KEY must be set to a strong, unique value in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    if len(JWT_SECRET_KEY) < 32:
        raise ValueError(
            "JWT_SECRET_KEY should be at least 32 characters for production security."
        )
