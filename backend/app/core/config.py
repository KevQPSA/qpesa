"""
Application configuration settings.
Uses Pydantic's BaseSettings to load environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Literal, Optional
import os

class Settings(BaseSettings):
    """
    Base settings for the application.
    Loads environment variables from .env file and environment.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Project Metadata
    PROJECT_NAME: str = "Kenya Crypto-Fiat Payment Processor"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "BTC/USDT payments with M-Pesa integration for Kenya market"

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False

    # Database Settings
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    TEST_DATABASE_URL: str = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_crypto_fiat_db"

    # Security Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 # 1 hour

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = ["*"] # Be specific in production, e.g., ["http://localhost:3000", "https://yourdomain.com"]
    ALLOWED_HOSTS: List[str] = ["*"] # Be specific in production

    # Blockchain RPC URLs (for direct node interaction or specific APIs)
    BTC_RPC_URL: Optional[str] = None
    ETH_RPC_URL: Optional[str] = None
    TRON_RPC_URL: Optional[str] = None

    # M-Pesa Daraja API Credentials (placeholders)
    MPESA_CONSUMER_KEY: Optional[str] = None
    MPESA_CONSUMER_SECRET: Optional[str] = None
    MPESA_SHORTCODE: Optional[str] = None
    MPESA_PASSKEY: Optional[str] = None
    MPESA_BUSINESS_SHORTCODE: Optional[str] = None # For C2B/B2C
    MPESA_LIPA_NA_MPESA_ONLINE_SHORTCODE: Optional[str] = None # For STK Push
    MPESA_CALLBACK_URL: Optional[str] = None

    # Other potential settings
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None # For error monitoring

settings = Settings()

# Override settings for specific environments if needed (e.g., for testing)
if os.getenv("TESTING") == "true":
    settings.ENVIRONMENT = "test"
    settings.DEBUG = True
    settings.DATABASE_URL = settings.TEST_DATABASE_URL
    settings.ALLOWED_ORIGINS = ["http://test"] # Restrict for test client
    settings.ALLOWED_HOSTS = ["test"]
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = 1 # Shorten for tests
