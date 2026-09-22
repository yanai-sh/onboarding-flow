from collections.abc import Iterator

import pytest
from pydantic import ValidationError

from onboarding_flow.config import (
    DEFAULT_UPSTREAM_TIMEOUT_SECONDS,
    DEFAULT_UPSTREAM_URL,
    Settings,
    get_settings,
    reset_settings_cache,
    upstream_timeout_seconds,
    upstream_url,
)


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Iterator[None]:
    reset_settings_cache()
    yield
    reset_settings_cache()


def test_settings_defaults() -> None:
    settings = Settings()
    assert str(settings.upstream_url) == DEFAULT_UPSTREAM_URL
    assert settings.upstream_timeout_seconds == DEFAULT_UPSTREAM_TIMEOUT_SECONDS


def test_settings_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UPSTREAM_URL", "https://example.test/vehicle-info")
    monkeypatch.setenv("UPSTREAM_TIMEOUT_SECONDS", "2.5")
    reset_settings_cache()

    settings = get_settings()
    assert str(settings.upstream_url) == "https://example.test/vehicle-info"
    assert settings.upstream_timeout_seconds == 2.5


def test_settings_rejects_invalid_upstream_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UPSTREAM_URL", "not-a-url")
    with pytest.raises(ValidationError):
        Settings()


def test_legacy_config_helpers_use_cached_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UPSTREAM_TIMEOUT_SECONDS", "3")
    reset_settings_cache()

    assert upstream_url() == DEFAULT_UPSTREAM_URL
    assert upstream_timeout_seconds() == 3.0
