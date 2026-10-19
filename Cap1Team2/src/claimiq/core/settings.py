from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ClaimIQ API"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str = (
        "postgresql+psycopg://postgres:password@localhost:5432/claimiq"
    )

    secret_key: str = "development-secret-key-change-later"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    upload_directory: str = "storage/documents"
    max_upload_size_mb: int = 10

    embedding_model_name: str = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store_directory: str = "storage/vector_store"

    vector_collection_name: str = "claimiq_document_chunks"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()