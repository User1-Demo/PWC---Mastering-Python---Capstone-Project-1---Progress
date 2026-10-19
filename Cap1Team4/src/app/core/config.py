import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
env_path = os.path.join(root_dir, ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_path, env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "ClaimIQ"
    ENV: str = "dev"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./claims.db"
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: list[str] = []

    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCK_MINUTES: int = 15
    AI_RATE_LIMIT_PER_MINUTE: int = 30

    SLA_DEFAULT_DAYS: int = 7
    HIGH_VALUE_THRESHOLD: float = 500_000

    DOCUMENT_STORAGE_DIR: str = "data/documents"
    MAX_UPLOAD_BYTES: int = 10_485_760
    RAG_TOP_K: int = 4
    RAG_CHUNK_SIZE: int = 800
    RAG_CHUNK_OVERLAP: int = 100


@lru_cache
def get_settings() -> Settings:
  return Settings()  # type: ignore[call-arg]


settings = get_settings()