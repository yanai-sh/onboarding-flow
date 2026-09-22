"""Runtime configuration from environment variables."""

from functools import lru_cache

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_UPSTREAM_URL = "https://insurance-webhook-945894769129.us-central1.run.app/vehicle-info"
DEFAULT_UPSTREAM_TIMEOUT_SECONDS = 5.0


class Settings(BaseSettings):
    """Cloud Run and local settings loaded from the process environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    upstream_url: str = DEFAULT_UPSTREAM_URL
    upstream_timeout_seconds: float = Field(
        default=DEFAULT_UPSTREAM_TIMEOUT_SECONDS,
        gt=0,
        le=120,
    )

    @field_validator("upstream_url")
    @classmethod
    def validate_upstream_url(cls, value: str) -> str:
        HttpUrl(value)
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def upstream_url() -> str:
    return get_settings().upstream_url


def upstream_timeout_seconds() -> float:
    return get_settings().upstream_timeout_seconds


def reset_settings_cache() -> None:
    """Clear cached settings (tests only)."""
    get_settings.cache_clear()
