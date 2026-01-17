from pydantic_settings import BaseSettings
from typing import List, Optional
import json

class Settings(BaseSettings):
    # Application Settings
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-here"
    JWT_SECRET: str = "your-jwt-secret-here"
    API_VERSION: str = "v1"

    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql://platform_user:password@localhost:5432/ai_platform"

    # Redis Cache & Queue
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_URL: str = "redis://localhost:6379/1"

    # n8n Configuration
    N8N_API_KEY: str = ""
    N8N_API_URL: str = "http://localhost:5678/api/v1"
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook"

    # AI API Keys
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Frontend
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Algeria-specific
    DEFAULT_TIMEZONE: str = "Africa/Algiers"
    DEFAULT_CURRENCY: str = "DZD"
    DEFAULT_LANGUAGE: str = "fr"
    DZD_TO_USD: float = 135.0

    # Cost Management
    CLAUDE_INPUT_COST_PER_M: float = 3.0
    CLAUDE_OUTPUT_COST_PER_M: float = 15.0
    COST_MARKUP_PERCENTAGE: float = 50.0

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
