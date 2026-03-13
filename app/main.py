import os
import logging
import traceback
import socketio
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.db.init_db import init_db
from app.sockets.server import sio
from app.core.rate_limit import limiter
from app.core.config import settings
import app.sockets.events  # noqa: F401 — registers event handlers

logger = logging.getLogger("rchat")
logging.basicConfig(level=logging.INFO)

fastapi_app = FastAPI(title="Rchat.ai")
fastapi_app.state.limiter = limiter
fastapi_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@fastapi_app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return JSON for ALL unhandled exceptions — never a plain text 500."""
    tb = traceback.format_exc()
    logger.error("Unhandled %s on %s %s: %s\n%s", type(exc).__name__, request.method, request.url.path, exc, tb)
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {str(exc)}"},
    )

cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: blob:; connect-src 'self' ws: wss:; frame-ancestors 'self' https://huggingface.co https://*.hf.space"
        if settings.COOKIE_SECURE:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


fastapi_app.add_middleware(SecurityHeadersMiddleware)


@fastapi_app.on_event("startup")
def on_startup():
    init_db()
    # Ensure uploads directories exist
    base = os.path.join(os.path.dirname(__file__), "..", "uploads")
    os.makedirs(os.path.join(base, "avatars"), exist_ok=True)
    os.makedirs(os.path.join(base, "status"), exist_ok=True)


fastapi_app.include_router(api_router, prefix="/api/v1")

# Serve uploaded files (avatars, status media)
uploads_path = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(uploads_path, exist_ok=True)
fastapi_app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

# Serve frontend build if it exists (production / HF Spaces deployment)
_frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_frontend_dist):
    from starlette.responses import FileResponse

    # Serve static assets (JS, CSS, images)
    fastapi_app.mount("/assets", StaticFiles(directory=os.path.join(_frontend_dist, "assets")), name="frontend-assets")

    # Catch-all: serve index.html for SPA client-side routing
    @fastapi_app.get("/{path:path}")
    async def serve_spa(path: str):
        file_path = os.path.join(_frontend_dist, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(_frontend_dist, "index.html"))
else:
    @fastapi_app.get("/")
    def root():
        return {"msg": "Rchat.ai backend running (no frontend build found)"}

# Combine: Socket.IO handles /socket.io/*, FastAPI handles everything else
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
