# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Rchat.ai Backend"

    # SQLite DB in project root
    DATABASE_URL: str = "sqlite:///./rchat.db"

    # JWT settings
    JWT_SECRET_KEY: str = "super-secret-key-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"


settings = Settings()