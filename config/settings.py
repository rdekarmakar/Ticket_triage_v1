"""
Centralized configuration management using Pydantic Settings.
All configuration is loaded from environment variables or .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "Ticket Triage System"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite:///data/tickets.db"

    # Groq API
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.3
    groq_max_tokens: int = 1024

    # Webex
    webex_access_token: Optional[str] = None
    webex_bot_token: Optional[str] = None
    webex_webhook_secret: Optional[str] = None
    webhook_base_url: Optional[str] = None

    # Dashboard Auth
    dashboard_username: str = "admin"
    dashboard_password: str = "changeme"

    # Knowledge Base
    runbooks_path: str = "knowledge_base/runbooks"
    chroma_persist_dir: str = "data/chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Search
    search_results_limit: int = 5
    min_similarity_score: float = 0.5
    chunk_size: int = 512
    chunk_overlap: int = 50


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
