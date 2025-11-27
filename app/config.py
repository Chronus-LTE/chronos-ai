"""
Application configuration using Pydantic Settings
"""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool
    ENVIRONMENT: str

    # Server
    HOST: str
    PORT: int
    FRONTEND_URL: str

    # Database - PostgreSQL
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int
    DATABASE_MAX_OVERFLOW: int

    # Redis
    REDIS_URL: str
    REDIS_CACHE_DB: int

    # Qdrant Vector Database
    QDRANT_HOST: str
    QDRANT_PORT: int
    QDRANT_API_KEY: str
    QDRANT_COLLECTION_NAME: str

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # Google Gemini API
    GEMINI_API_KEY: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Embeddings Model
    EMBEDDING_MODEL: str

    # Timezone
    TIMEZONE: str

    # Logging
    LOG_LEVEL: str

    @property
    def qdrant_url(self) -> str:
        """Get Qdrant URL."""
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"


# Global settings instance
settings = Settings()
