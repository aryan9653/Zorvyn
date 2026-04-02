"""
Configuration settings for the Finance System Backend.
Uses pydantic-settings for environment variable management.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Finance System Backend"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Database
    database_url: str = "sqlite:///./finance.db"
    
    # Security
    secret_key: str = "your-super-secret-key-change-in-production-please"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # Initial Admin User
    admin_username: str = "admin"
    admin_email: str = "admin@finance.com"
    admin_password: str = "admin123"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
