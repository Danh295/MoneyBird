"""
config.py - Google GenAI SDK Setup (Type Safe)
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    gemini_api_key: str = "" 
    tavily_api_key: str = ""
    
    model_name: str = "gemini-2.5-flash-lite"
    
    intake_temperature: float = 0.3
    planner_temperature: float = 0.1
    synthesizer_temperature: float = 0.6
    
    debug: bool = True
    cors_origins: str = "*"
    
    # Redis configuration
    redis_url: str = "redis://localhost:6379"
    state_ttl: int = 86400  # 24 hours in seconds

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()