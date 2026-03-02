from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Image Social Platform"
    DEBUG: bool = False
    SECRET_KEY: str = "change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database (Neon.tech PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/aiimage"

    # Redis (Upstash)
    REDIS_URL: str = "redis://localhost:6379"

    # Hugging Face
    HUGGINGFACE_API_KEY: str = ""
    HUGGINGFACE_IMAGE_MODEL: str = "black-forest-labs/FLUX.1-schnell"

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
