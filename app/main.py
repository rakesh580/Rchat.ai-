# app/main.py
from fastapi import FastAPI

from app.api.v1.router import api_router
from app.db.init_db import init_db

app = FastAPI(title="Rchat.ai")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def root():
    return {"msg": "Rchat.ai backend running"}

# Apply prefix ONE time only
app.include_router(api_router, prefix="/api/v1")