from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.init_db import init_db

app = FastAPI(title=settings.PROJECT_NAME)


# Run DB initialization when the backend starts
@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def root():
    return {"msg": "Rchat.ai backend running"}


# include versioned API routes
app.include_router(api_router, prefix="/api/v1")