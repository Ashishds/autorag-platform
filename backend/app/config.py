"""Application settings, loaded from environment / .env."""

from functools import lru_cache

from dotenv import load_dotenv

load_dotenv(override=True)

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    ENV: str = "local"
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    # Postgres (asyncpg)
    POSTGRES_URL: str = "postgresql://autorag:autorag@localhost:5432/autorag"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "documents"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Providers
    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""  # Custom base URL for OpenAI-compatible APIs (e.g. Euron)
    COHERE_API_KEY: str = ""

    # Models
    LLM_PRIMARY: str = "gemini-2.5-pro"
    LLM_FAST: str = "gemini-2.5-flash"
    LLM_FALLBACK: str = "gpt-4o"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIM: int = 768
    RERANKER_MODEL: str = "rerank-v3.5"

    # Observer
    OBSERVER_CRON_MINUTES: int = 60

    # Langfuse
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # OAuth / Connectors
    APP_BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    NOTION_CLIENT_ID: str = ""
    NOTION_CLIENT_SECRET: str = ""
    DROPBOX_CLIENT_ID: str = ""
    DROPBOX_CLIENT_SECRET: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
