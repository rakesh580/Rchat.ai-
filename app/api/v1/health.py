# app/api/v1/health.py
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check():
    return {"status": "ok"}


@router.get("/debug")
def debug_check():
    """Temporary debug endpoint — shows config status (no secret values)."""
    db_ok = False
    db_error = ""
    try:
        from app.db.postgres import query_one
        result = query_one("SELECT 1 AS ok")
        db_ok = result is not None
    except Exception as e:
        db_error = f"{type(e).__name__}: {str(e)}"

    return {
        "status": "ok",
        "jwt_key_set": bool(settings.JWT_SECRET_KEY),
        "jwt_key_length": len(settings.JWT_SECRET_KEY),
        "jwt_algorithm": settings.JWT_ALGORITHM,
        "db_url_set": bool(settings.DATABASE_URL),
        "db_url_prefix": settings.DATABASE_URL[:30] + "..." if settings.DATABASE_URL else "",
        "db_connected": db_ok,
        "db_error": db_error,
        "groq_key_set": bool(settings.GROQ_API_KEY) and settings.GROQ_API_KEY != "your-groq-api-key-here",
        "cors_origins": settings.CORS_ORIGINS,
        "cookie_secure": settings.COOKIE_SECURE,
    }