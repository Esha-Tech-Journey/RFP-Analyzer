"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All environment-sensitive configuration for the application."""

    DATABASE_URL: str
    SYNC_DATABASE_URL: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # EPAM DIAL / Azure OpenAI — optional; LLM analysis is skipped if key is empty
    DIAL_API_KEY: str = ""
    DIAL_ENDPOINT: str = "https://ai-proxy.lab.epam.com"
    DIAL_MODEL: str = "gpt-4o"

    class Config:
        env_file = ".env"


settings = Settings()
