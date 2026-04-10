"""
Application configuration

Loads configuration from environment variables using Pydantic Settings.
Provides type-safe access to application settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses pydantic-settings for type-safe configuration management.
    Values are loaded from .env file or environment variables.
    """

    # Application Configuration
    app_name: str = "Makyol Compliance API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    # API Security
    api_keys: str = "your-secure-api-key-here"

    # Rate Limiting
    rate_limit_per_minute: int = 100

    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    cors_allow_credentials: bool = True

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    def get_api_keys_list(self) -> List[str]:
        """Parse comma-separated API keys into a list."""
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]

    def get_cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


# Global settings instance
settings = Settings()
