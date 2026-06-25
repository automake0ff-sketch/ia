"""
Configuración centralizada de la aplicación.
Lee variables de entorno (y .env) usando pydantic-settings.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "YouTube Video Summarizer API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # --- CORS ---
    ALLOWED_ORIGINS: str = "*"

    # --- Proveedores LLM ---
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"
    DEFAULT_LLM_PROVIDER: str = "openai"  # openai | anthropic

    # --- Base de datos ---
    DATABASE_URL: str = "sqlite:///./data/summarizer.db"

    # --- Caché ---
    REDIS_URL: Optional[str] = None
    CACHE_TTL_DAYS: int = 7

    # --- Resúmenes ---
    SUPPORTED_LANGUAGES: List[str] = ["es", "en", "fr", "de", "it", "pt"]
    DEFAULT_LANGUAGE: str = "es"
    MAX_TRANSCRIPT_CHARS: int = 60000

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
