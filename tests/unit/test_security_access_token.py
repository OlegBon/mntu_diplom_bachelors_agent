from datetime import timedelta

import pytest
from jose import ExpiredSignatureError, jwt

from backend import security
from backend.config import get_bounded_int_env


def test_local_access_token_ttl_is_bounded() -> None:
    assert 15 <= security.ACCESS_TOKEN_EXPIRE_MINUTES <= 720


def test_expired_access_token_is_rejected() -> None:
    token = security.create_access_token({"sub": "expired-user"}, expires_delta=timedelta(seconds=-1))

    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])


def test_bounded_integer_environment_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_ACCESS_TTL", "480")
    assert get_bounded_int_env("TEST_ACCESS_TTL", default=30, minimum=15, maximum=720) == 480

    monkeypatch.setenv("TEST_ACCESS_TTL", "721")
    with pytest.raises(RuntimeError, match="15–720"):
        get_bounded_int_env("TEST_ACCESS_TTL", default=30, minimum=15, maximum=720)
