from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Claims AI Platform"
    env: str = "dev"
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    document_dir: str = "./data/documents"
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_api_url: str | None = None
    llm_api_key: str | None = None
    sla_hours: int = 72

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
