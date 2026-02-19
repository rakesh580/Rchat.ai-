# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Rchat.ai Backend"

    # JWT settings
    JWT_SECRET_KEY: str = "CHANGE_ME_SET_IN_ENV"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    MONGO_URI: str = "SET_IN_ENV_FILE"
    MONGO_DB_NAME: str = "rchat"

    # Groq AI
    GROQ_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()