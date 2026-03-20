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

    # Autopilot LangGraph settings
    AUTOPILOT_MODEL: str = "llama-3.3-70b-versatile"
    AUTOPILOT_MAX_RETRIES: int = 2
    AUTOPILOT_CONTEXT_MESSAGES: int = 10

    # CORS — comma-separated origins, defaults to localhost for dev
    CORS_ORIGINS: str = "http://localhost:5173"

    # Cookie secure flag — auto-detected from environment
    COOKIE_SECURE: bool = False

    # Strip trailing whitespace/newlines from all string secrets
    # (HF Spaces and other platforms often inject trailing \n)
    @field_validator("JWT_SECRET_KEY", "DATABASE_URL", "GROQ_API_KEY", "CORS_ORIGINS", "AUTOPILOT_MODEL", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip() if isinstance(v, str) else v

    class Config:
        env_file = ".env"


settings = Settings()

# Reject known-insecure JWT secrets at startup — ALWAYS, regardless of environment
_INSECURE_SECRETS = {
    "change-me-to-a-real-secret-in-production",
    "secret",
    "changeme",
    "your-secret-key",
    "CHANGE_ME_GENERATE_WITH_openssl_rand_hex_32",
}
if settings.JWT_SECRET_KEY in _INSECURE_SECRETS:
    import warnings
    warnings.warn(
        "WARNING: JWT_SECRET_KEY is set to a known insecure default. "
        "Generate a real secret with: openssl rand -hex 32",
        stacklevel=2,
    )
