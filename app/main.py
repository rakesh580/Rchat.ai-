import os
import socketio
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
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

fastapi_app = FastAPI(title="Rchat.ai")
fastapi_app.state.limiter = limiter
fastapi_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' ws: wss:"
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


@fastapi_app.get("/")
def root():
    return {"msg": "Rchat.ai backend running"}


fastapi_app.include_router(api_router, prefix="/api/v1")

# Serve uploaded files (avatars, status media)
uploads_path = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(uploads_path, exist_ok=True)
fastapi_app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

# Combine: Socket.IO handles /socket.io/*, FastAPI handles everything else
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
