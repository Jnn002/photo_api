"""
Application configuration using Pydantic Settings.

This module loads configuration from environment variables and provides
centralized settings for the entire application.
"""

from pydantic import field_validator
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
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ISSUER: str = 'photography-studio-api'
    JWT_AUDIENCE: str = 'photography-studio-client'

    # Email Configuration (all from .env)
    MAIL_USERNAME: str = ''
    MAIL_PASSWORD: str = ''
    MAIL_SERVER: str = ''
    MAIL_PORT: int = 587
    MAIL_FROM: str = ''
    MAIL_FROM_NAME: str = ''

    # Admin Configuration (for system initialization)
    ADMIN_EMAIL: str = ''
    ADMIN_PASSWORD: str = ''

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

    # Validators
    @field_validator('JWT_SECRET')
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT_SECRET is strong enough."""
        if not v or len(v) < 32:
            raise ValueError(
                'JWT_SECRET must be at least 32 characters. '
                'Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )
        return v

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate DATABASE_URL is properly formatted."""
        if not v:
            raise ValueError('DATABASE_URL is required')
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError('DATABASE_URL must be a PostgreSQL connection string')
        return v

    @field_validator('JWT_ALGORITHM')
    @classmethod
    def validate_jwt_algorithm(cls, v: str) -> str:
        """Validate JWT algorithm is secure."""
        allowed_algorithms = ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
        if v not in allowed_algorithms:
            raise ValueError(
                f'JWT_ALGORITHM must be one of {allowed_algorithms}. Got: {v}'
            )
        return v


# Global settings instance
settings = Settings()
