from datetime import timedelta

import pytest
from jose import jwt
from src.app_config import app_config
from src.auth.jwt_handler import (
    _now,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_create_access_token():
    subject = "test_user_id"
    token = create_access_token(subject)

    assert isinstance(token, str)

    # Decode and verify the content
    decoded = jwt.decode(
        token, app_config.SECRET_KEY, algorithms=[app_config.JWT_ALGORITHM]
    )
    assert decoded["sub"] == subject
    assert decoded["type"] == "access"
    assert "exp" in decoded
    assert "iat" in decoded


def test_create_refresh_token():
    subject = "test_user_id"
    token = create_refresh_token(subject)

    assert isinstance(token, str)

    # Decode and verify the content
    decoded = jwt.decode(
        token, app_config.SECRET_KEY, algorithms=[app_config.JWT_ALGORITHM]
    )
    assert decoded["sub"] == subject
    assert decoded["type"] == "refresh"
    assert "exp" in decoded
    assert "iat" in decoded


def test_decode_token_valid():
    subject = "test_user_id"
    token = create_access_token(subject)

    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["sub"] == subject
    assert decoded["type"] == "access"


def test_decode_token_invalid():
    bad_jwt_str = "invalid_jwt_string_data"
    decoded = decode_token(bad_jwt_str)
    assert decoded is None


def test_decode_token_expired():
    # Construct an expired token manually
    payload = {
        "sub": "test_user_id",
        "type": "access",
        "iat": _now(),
        "exp": _now() - timedelta(minutes=10),  # Expired 10 mins ago
    }
    expired_jwt_str = jwt.encode(
        payload, app_config.SECRET_KEY, algorithm=app_config.JWT_ALGORITHM
    )

    # decode_token catches JWTError which includes ExpiredSignatureError
    decoded = decode_token(expired_jwt_str)
    assert decoded is None
