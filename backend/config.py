"""
config.py - Google GenAI SDK Setup (Type Safe)
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    gemini_api_key: str = "AIzaSyCOqnGKuVgL1uv7CXOQy5tK1jbskPXVQ34" 
    tavily_api_key: str = "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"
    
    # Supabase configuration
    supabase_url: str = "https://czdisykcmzsycudwtstf.supabase.co/"
    supabase_key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN6ZGlzeWtjbXpzeWN1ZHd0c3RmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg2MTk5NzIsImV4cCI6MjA4NDE5NTk3Mn0.4j25szbtQ2hEKY5b69rIjucSAesRxiq7o9U4pSjbEaU"
    
    model_name: str = "gemini-2.5-flash"
    
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