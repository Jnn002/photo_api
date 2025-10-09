"""
Application configuration using Pydantic Settings.

This module loads configuration from environment variables and provides
centralized settings for the entire application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    # Application
    APP_NAME: str = 'Photography Studio API'
    APP_VERSION: str = '1.0.0'
    DEBUG: bool = False
    ENVIRONMENT: str = 'development'
    DOMAIN: str = ''

    # Database
    DATABASE_URL: str = ''

    # Redis
    REDIS_HOST: str = ''
    REDIS_PORT: int = 0
    REDIS_URL: str = ''

    # Security & JWT
    JWT_SECRET: str = ''
    JWT_ALGORITHM: str = ''
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRY: float = 30.0

    # Email Configuration (all from .env)
    MAIL_USERNAME: str = ''
    MAIL_PASSWORD: str = ''
    MAIL_SERVER: str = ''
    MAIL_PORT: int = 587
    MAIL_FROM: str = ''
    MAIL_FROM_NAME: str = ''

    # Business Rules Configuration
    PAYMENT_DEADLINE_DAYS: int = 5
    CHANGES_DEADLINE_DAYS: int = 7
    DEFAULT_EDITING_DAYS: int = 5
    DEFAULT_DEPOSIT_PERCENTAGE: int = 50

    # CORS
    CORS_ORIGINS: list[str] = ['http://localhost:4200', 'http://localhost:3000']

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


# Global settings instance
settings = Settings()
