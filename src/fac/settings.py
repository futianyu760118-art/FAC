"""Environment-backed service settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from FAC-prefixed environment variables."""

    database_url: str = "sqlite:///./fac.db"
    functional_currency: str = "CNY"
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_prefix="FAC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> Settings:
    """Create settings when the application is constructed."""
    return Settings()
