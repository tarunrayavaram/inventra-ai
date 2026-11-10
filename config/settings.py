"""Application configuration."""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Google Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-3.8-flash"

    # OpenWeather API
    openweather_api_key: str
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"

    # Database
    database_path: str = "./database/inventra.db"

    # App Settings
    log_level: str = "INFO"
    weather_cache_ttl: int = 1800
    max_conversation_history: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def db_path_resolved(self) -> Path:
        """Get absolute database path."""
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        return Path(self.database_path).resolve()


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
