"""
Configuration management for MindMoney backend.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    google_api_key: str
    anthropic_api_key: str
    openai_api_key: str
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Supabase
    supabase_url: str
    supabase_key: str
    
    # Model configurations
    gemini_model: str = "gemini-1.5-pro"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    openai_model: str = "gpt-4o-mini"
    
    # Temperature settings per agent
    intake_temperature: float = 0.2
    planner_temperature: float = 0.2
    synthesizer_temperature: float = 0.4
    
    # App settings
    debug: bool = False
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # State TTL in seconds
    state_ttl: int = 3600
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()