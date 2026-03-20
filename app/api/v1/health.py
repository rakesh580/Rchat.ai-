# app/api/v1/health.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check():
    return {"status": "ok"}


@router.get("/debug")
def debug_check(current_user=Depends(get_current_user)):
    """Protected debug endpoint — requires authentication."""
    db_ok = False
    db_error = ""
    try:
        from app.db.postgres import query_one
        result = query_one("SELECT 1 AS ok")
        db_ok = result is not None
    except Exception:
        db_error = "Database connection failed"

    return {
        "status": "ok",
        "db_connected": db_ok,
        "db_error": db_error,
    }
