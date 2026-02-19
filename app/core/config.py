# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Rchat.ai Backend"

    # JWT settings — MUST be set via .env
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # MongoDB — MUST be set via .env
    MONGO_URI: str
    MONGO_DB_NAME: str = "rchat"

    # Groq AI
    GROQ_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()