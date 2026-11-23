import pytest

from app.config import Settings


def test_production_rejects_placeholder_secret():
    with pytest.raises(ValueError):
        Settings(ENVIRONMENT="production", SECRET_KEY="change-me", _env_file=None)


def test_production_rejects_wildcard_cors():
    with pytest.raises(ValueError):
        Settings(ENVIRONMENT="production", SECRET_KEY="x" * 64, CORS_ORIGINS="*", _env_file=None)


def test_production_defaults_are_hardened():
    s = Settings(ENVIRONMENT="production", SECRET_KEY="x" * 64, CORS_ORIGINS="https://soc.example.com", _env_file=None)
    assert s.cookie_secure is True
    assert s.docs_enabled is False


def test_dev_falls_back_to_flagged_secret():
    s = Settings(ENVIRONMENT="development", SECRET_KEY="", _env_file=None)
    assert s.using_dev_secret
