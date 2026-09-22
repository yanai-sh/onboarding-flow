"""Runtime configuration from environment variables."""

from functools import cache
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_UPSTREAM_URL = "https://insurance-webhook-945894769129.us-central1.run.app/vehicle-info"
DEFAULT_UPSTREAM_TIMEOUT_SECONDS = 5.0


def _upper_if_str(value: object) -> object:
    return value.upper() if isinstance(value, str) else value


LogLevel = Annotated[
    Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    BeforeValidator(_upper_if_str),
]


class Settings(BaseSettings):
    """Cloud Run and local settings loaded from the process environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    upstream_url: HttpUrl = Field(default=HttpUrl(DEFAULT_UPSTREAM_URL))
    upstream_timeout_seconds: float = Field(
        default=DEFAULT_UPSTREAM_TIMEOUT_SECONDS,
        gt=0,
        le=120,
    )
    log_level: LogLevel = "INFO"


@cache
def get_settings() -> Settings:
    return Settings()


def upstream_url() -> str:
    return str(get_settings().upstream_url)


def upstream_timeout_seconds() -> float:
    return get_settings().upstream_timeout_seconds


def reset_settings_cache() -> None:
    """Clear cached settings (tests only)."""
    get_settings.cache_clear()
