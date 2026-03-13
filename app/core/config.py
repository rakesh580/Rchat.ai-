# app/core/config.py
import os
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Rchat.ai Backend"

    # JWT settings — MUST be set via .env
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # PostgreSQL (Neon) — MUST be set via .env
    DATABASE_URL: str

    # Groq AI
    GROQ_API_KEY: str = ""

    # CORS — comma-separated origins, defaults to localhost for dev
    CORS_ORIGINS: str = "http://localhost:5173"

    # Cookie secure flag — auto-detected from environment
    COOKIE_SECURE: bool = False

    # Strip trailing whitespace/newlines from all string secrets
    # (HF Spaces and other platforms often inject trailing \n)
    @field_validator("JWT_SECRET_KEY", "DATABASE_URL", "GROQ_API_KEY", "CORS_ORIGINS", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip() if isinstance(v, str) else v

    class Config:
        env_file = ".env"


settings = Settings()

# Reject known-insecure JWT secrets at startup
_INSECURE_SECRETS = {
    "change-me-to-a-real-secret-in-production",
    "secret",
    "changeme",
    "your-secret-key",
}
if os.getenv("ENV", "development") != "development" and settings.JWT_SECRET_KEY in _INSECURE_SECRETS:
    raise RuntimeError(
        "FATAL: JWT_SECRET_KEY is set to a known insecure default. "
        "Set a cryptographically random secret (256+ bits) in .env before deploying."
    )
