# app/main.py
from fastapi import FastAPI

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.init_db import init_db

app = FastAPI(title="Rchat.ai")


@app.on_event("startup")
def on_startup():
    # Ensure tables are created at startup
    init_db()


@app.get("/")
def root():
    return {"msg": "Rchat.ai backend running"}


# versioned API routes
app.include_router(api_router, prefix="/api/v1")