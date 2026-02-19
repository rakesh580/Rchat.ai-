import os
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.db.init_db import init_db
from app.sockets.server import sio
import app.sockets.events  # noqa: F401 — registers event handlers

fastapi_app = FastAPI(title="Rchat.ai")

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
