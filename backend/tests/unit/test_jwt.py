from datetime import timedelta
from unittest.mock import patch

import pytest

with patch.dict("os.environ", {"SECRET_KEY": "test-secret-key-for-unit-testing-only"}):
    from src.auth.jwt_handler import (
        create_access_token,
        create_refresh_token,
        decode_token,
    )

TEST_SECRET = "test-secret-key-for-unit-testing-only"
TEST_EMAIL = "test@example.com"


@pytest.fixture(autouse=True)
def patch_secret_key():
    with patch("src.auth.jwt_handler.app_config") as mock_config:
        mock_config.SECRET_KEY = TEST_SECRET
        yield mock_config


class TestCreateAccessToken:
    def test_returns_string(self):
        assert isinstance(create_access_token(TEST_EMAIL), str)

    def test_correct_subject(self):
        payload = decode_token(create_access_token(TEST_EMAIL))
        assert payload["sub"] == TEST_EMAIL

    def test_type_is_access(self):
        payload = decode_token(create_access_token(TEST_EMAIL))
        assert payload["type"] == "access"

    def test_not_expired_by_default(self):
        assert decode_token(create_access_token(TEST_EMAIL)) is not None

    def test_expired_immediately(self):
        token = create_access_token(TEST_EMAIL, expires_delta=timedelta(seconds=-1))
        assert decode_token(token) is None

    def test_raises_without_secret(self):
        with patch("src.auth.jwt_handler.app_config") as mock_cfg:
            mock_cfg.SECRET_KEY = None
            with pytest.raises(ValueError, match="SECRET_KEY"):
                create_access_token(TEST_EMAIL)


class TestCreateRefreshToken:
    def test_returns_string(self):
        assert isinstance(create_refresh_token(TEST_EMAIL), str)

    def test_correct_subject(self):
        payload = decode_token(create_refresh_token(TEST_EMAIL))
        assert payload["sub"] == TEST_EMAIL

    def test_type_is_refresh(self):
        payload = decode_token(create_refresh_token(TEST_EMAIL))
        assert payload["type"] == "refresh"


class TestDecodeToken:
    def test_valid_token_returns_dict(self):
        payload = decode_token(create_access_token(TEST_EMAIL))
        assert isinstance(payload, dict)

    def test_expired_returns_none(self):
        token = create_access_token(TEST_EMAIL, expires_delta=timedelta(seconds=-1))
        assert decode_token(token) is None

    def test_invalid_returns_none(self):
        assert decode_token("invalid.token.string") is None
