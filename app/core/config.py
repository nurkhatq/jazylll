from pydantic_settings import BaseSettings
from typing import Optional
import secrets
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT - SECURITY CRITICAL: Must be set via environment variable
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Redis for token blacklist and session management
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_TOKEN_BLACKLIST_PREFIX: str = "blacklist:"
    REDIS_SESSION_PREFIX: str = "session:"

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # WhatsApp Integration
    WHATSAPP_API_URL: str = "https://api.whatsapp.com"
    WHATSAPP_API_KEY: Optional[str] = None
    WHATSAPP_VERIFICATION_CODE_EXPIRE_MINUTES: int = 5
    WHATSAPP_VERIFICATION_CODE_LENGTH: int = 6

    # Security Settings
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    REQUIRE_EMAIL_VERIFICATION: bool = False

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_AUTH_PER_MINUTE: int = 5

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.jazyl.tech",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 5242880  # 5MB
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/jpg", "image/webp"]

    # Application
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Jazyl Platform"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False

    # Audit Logging
    ENABLE_AUDIT_LOGGING: bool = True
    AUDIT_LOG_SENSITIVE_OPERATIONS: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_critical_settings()

    def _validate_critical_settings(self):
        """Validate critical security settings on startup"""

        # Validate SECRET_KEY
        if not self.SECRET_KEY:
            if self.ENVIRONMENT == "development":
                # Auto-generate for development only
                self.SECRET_KEY = secrets.token_urlsafe(32)
                print("⚠️  WARNING: Auto-generated SECRET_KEY for development. Set SECRET_KEY in .env for production!")
            else:
                raise ValueError(
                    "SECRET_KEY must be set in environment variables for production. "
                    "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )

        # Validate SECRET_KEY strength
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long for security")

        # Validate DATABASE_URL
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set in environment variables")

        # Warn about missing critical configs in production
        if self.ENVIRONMENT == "production":
            if not self.GOOGLE_CLIENT_ID:
                print("⚠️  WARNING: GOOGLE_CLIENT_ID not set - OAuth authentication will not work")
            if not self.WHATSAPP_API_KEY:
                print("⚠️  WARNING: WHATSAPP_API_KEY not set - Phone verification will not work")
            if self.DEBUG:
                print("⚠️  WARNING: DEBUG is enabled in production - this is a security risk!")


settings = Settings()
