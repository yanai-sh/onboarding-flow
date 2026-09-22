import pytest
from pydantic import ValidationError

from onboarding_flow.config import DEFAULT_UPSTREAM_URL, Settings, get_settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert str(settings.upstream_url) == DEFAULT_UPSTREAM_URL
    assert settings.upstream_timeout_seconds == 5.0
    assert settings.log_level == "INFO"


def test_settings_read_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UPSTREAM_URL", "https://example.test/vehicle-info")
    monkeypatch.setenv("UPSTREAM_TIMEOUT_SECONDS", "3")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = get_settings()

    assert str(settings.upstream_url) == "https://example.test/vehicle-info"
    assert settings.upstream_timeout_seconds == 3.0
    assert settings.log_level == "DEBUG"


@pytest.mark.parametrize(
    ("name", "value"),
    [("UPSTREAM_URL", "not-a-url"), ("UPSTREAM_TIMEOUT_SECONDS", "0"), ("LOG_LEVEL", "loud")],
)
def test_settings_reject_invalid_values(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError):
        Settings()
