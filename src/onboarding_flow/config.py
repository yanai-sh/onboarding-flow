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

    # BaseSettings forbids unknown keys; a local .env also carries deploy-only values.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    upstream_url: HttpUrl = Field(default=HttpUrl(DEFAULT_UPSTREAM_URL))
    # Total budget for one upstream exchange, enforced by the adapter.
    upstream_timeout_seconds: float = Field(
        default=DEFAULT_UPSTREAM_TIMEOUT_SECONDS,
        gt=0,
        le=120,
    )
    log_level: LogLevel = "INFO"


@cache
def get_settings() -> Settings:
    return Settings()
