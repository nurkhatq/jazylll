from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://Imang:0000@localhost:5432/jazyl"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # WhatsApp
    WHATSAPP_API_URL: str = "https://api.whatsapp.com"
    WHATSAPP_API_KEY: Optional[str] = None

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 5242880  # 5MB

    # Application
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Jazyl Platform"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
