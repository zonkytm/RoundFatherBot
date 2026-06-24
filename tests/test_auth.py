from unittest.mock import patch

from bot.config import settings
from web.routes.auth import verify_static_token, verify_telegram_init_data


def test_verify_valid_token():
    with patch.object(settings, "DASHBOARD_TOKEN", "test-token-123"):
        assert verify_static_token("test-token-123") is True


def test_verify_invalid_token():
    with patch.object(settings, "DASHBOARD_TOKEN", "test-token-123"):
        assert verify_static_token("wrong-token") is False


def test_verify_empty_token():
    with patch.object(settings, "DASHBOARD_TOKEN", ""):
        assert verify_static_token("anything") is False


def test_verify_telegram_init_data_invalid():
    result = verify_telegram_init_data("invalid_data")
    assert result is None


def test_verify_telegram_init_data_missing_hash():
    result = verify_telegram_init_data("user=test&auth_date=123")
    assert result is None
