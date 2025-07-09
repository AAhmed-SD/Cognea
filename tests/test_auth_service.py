import types
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException

from services import auth as auth_service


class _StubSupabase:
    """Minimal Supabase stub tailored for auth tests."""

    def __init__(self, user_exists: bool = True):
        self._user_exists = user_exists
        self._email_queried: str | None = None

    # Chainable interface mimicking the Supabase Python client
    def table(self, _name: str):  # noqa: D401
        return self

    def select(self, *_args, **_kwargs):  # noqa: D401
        return self

    def eq(self, _column: str, value):  # noqa: D401
        self._email_queried = value
        return self

    def execute(self):  # noqa: D401
        if not self._user_exists:
            return types.SimpleNamespace(data=[])
        return types.SimpleNamespace(
            data=[{"id": "user-123", "email": self._email_queried, "role": "user"}]
        )


@pytest.fixture()
def monkeypatched_supabase(monkeypatch):  # noqa: D401
    """Automatically patch get_supabase_client; returns factory for custom stubs."""

    def _factory(user_exists: bool = True):
        return _StubSupabase(user_exists=user_exists)

    monkeypatch.setattr(auth_service, "get_supabase_client", lambda: _factory(True))
    return _factory


class TestPasswordHashing:
    """hash_password / verify_password round-trip."""

    def test_hash_and_verify_success(self):
        password = "S3cureP@ssword!"
        hashed = auth_service.hash_password(password)
        assert password != hashed
        assert auth_service.verify_password(password, hashed) is True

    def test_verify_failure(self):
        hashed = auth_service.hash_password("RealP@ss1!")
        assert auth_service.verify_password("WrongP@ss2!", hashed) is False


class TestCreateAccessToken:
    """JWT payload and expiry checks."""

    def test_token_contains_exp_and_sub(self):
        data = {"sub": "tester@example.com", "role": "user"}
        token = auth_service.create_access_token(data)
        decoded = jwt.decode(
            token,
            auth_service.security_config.SECRET_KEY,
            algorithms=[auth_service.security_config.JWT_ALGORITHM],
        )
        assert decoded["sub"] == data["sub"]
        assert decoded["role"] == data["role"]
        exp = datetime.fromtimestamp(decoded["exp"], tz=UTC)
        assert exp > datetime.now(UTC)
        margin = timedelta(minutes=auth_service.security_config.ACCESS_TOKEN_EXPIRE_MINUTES + 1)
        assert exp - datetime.now(UTC) <= margin


class TestGetCurrentUser:
    """Happy-path and error scenarios for get_current_user."""

    def test_get_current_user_success(self):
        email = "user@example.com"
        token = auth_service.create_access_token({"sub": email, "role": "user"})
        # Patch Supabase to return a user
        auth_service.get_supabase_client = lambda: _StubSupabase(user_exists=True)  # type: ignore
        user = auth_service.get_current_user(token=token)
        assert user["email"] == email
        assert user["role"] == "user"

    def test_get_current_user_invalid_token(self):
        with pytest.raises(HTTPException):
            auth_service.get_current_user(token="invalid.token")

    def test_get_current_user_user_not_found(self):
        email = "missing@example.com"
        token = auth_service.create_access_token({"sub": email, "role": "user"})
        auth_service.get_supabase_client = lambda: _StubSupabase(user_exists=False)  # type: ignore
        with pytest.raises(HTTPException):
            auth_service.get_current_user(token=token)
