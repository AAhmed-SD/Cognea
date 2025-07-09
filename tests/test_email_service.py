from datetime import datetime, timedelta, UTC
from types import SimpleNamespace
from typing import List

import jwt
import pytest

from services import email_service as es_mod


class _TokenTableStub:
    """In-memory representation of the auth_tokens table used in tests."""

    def __init__(self):
        self._rows: List[dict] = []
        self._filters = []  # store tuples(column, op, value)

    # Insert operation
    def insert(self, row):  # noqa: D401
        self._rows.append(row)
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=[row]))

    # Delete operation with optional filters
    def delete(self):  # noqa: D401
        # Reset filters; deletion executed via execute()
        self._filters = []
        self._deleting = True
        def _lt(column, value):  # type: ignore[override]
            self._filters.append((column, "lt", value))
            return self
        def _eq(column, value):  # type: ignore[override]
            self._filters.append((column, "eq", value))
            return self
        self.lt = _lt  # type: ignore[attr-defined]
        self.eq = _eq  # type: ignore[attr-defined]
        return self

    def _apply_filters(self, rows):  # noqa: D401
        result = rows
        for column, op, value in self._filters:
            if op == "lt":
                result = [r for r in result if r[column] < value]
            elif op == "eq":
                result = [r for r in result if r[column] == value]
        return result

    def execute(self):  # noqa: D401
        filtered = self._apply_filters(self._rows)
        if getattr(self, "_deleting", False):
            for row in filtered:
                self._rows.remove(row)
            # After deletion reset flag
            self._deleting = False
        return SimpleNamespace(data=filtered)

    # For select chain
    def select(self, *_args):  # noqa: D401
        # Provide eq method for filtering
        self._filters = []
        return self

    def eq(self, column, value):  # noqa: D401
        self._filters.append((column, "eq", value))
        return self

    # Helper for delete chain distinguishing
    def lt(self, column, value):  # placeholder until overridden in delete()
        self._filters.append((column, "lt", value))
        return self


class _SupabaseStub:
    """Supabase client stub with only the auth_tokens table interface."""

    def __init__(self):
        self.auth_tokens = _TokenTableStub()

    def table(self, name: str):  # noqa: D401
        if name == "auth_tokens":
            return self.auth_tokens
        raise KeyError(name)


@pytest.fixture()
def patched_email_service(monkeypatch):  # noqa: D401
    """Return a fresh EmailService instance with patched dependencies."""
    # Patch supabase client
    supabase_stub = _SupabaseStub()
    monkeypatch.setattr(es_mod, "get_supabase_client", lambda: supabase_stub)

    # Patch _send_email to avoid SMTP network call
    monkeypatch.setattr(es_mod.EmailService, "_send_email", lambda self, *a, **k: True)

    # Provide dummy SMTP credentials via env vars so __init__ doesn't warn
    monkeypatch.setenv("SMTP_USERNAME", "dummy")
    monkeypatch.setenv("SMTP_PASSWORD", "dummy")

    return es_mod.EmailService()


class TestTokenCreationAndVerification:
    """Direct tests of private token helpers."""

    def test_create_and_verify_token(self, patched_email_service):  # noqa: D401
        payload = {"user_id": "u1", "type": "password_reset"}
        token = patched_email_service._create_token(payload.copy(), timedelta(minutes=30))
        decoded = patched_email_service._verify_token(token)
        assert decoded is not None and decoded["user_id"] == "u1"

    def test_verify_token_invalid_or_expired(self, patched_email_service):  # noqa: D401
        bad = patched_email_service._verify_token("not.a.jwt")
        assert bad is None
        # expired token
        expired = jwt.encode({"exp": 1, "iat": 1}, patched_email_service.jwt_secret, algorithm="HS256")
        assert patched_email_service._verify_token(expired) is None


class TestPasswordResetFlow:
    """End-to-end password reset email and token verification."""

    def test_password_reset_flow(self, patched_email_service):  # noqa: D401
        user_id = "user-xyz"
        email = "user@example.com"
        # Send reset email; token record should be created
        assert patched_email_service.send_password_reset_email(user_id, email)
        tokens = patched_email_service.supabase.auth_tokens._rows
        assert len(tokens) == 1 and tokens[0]["user_id"] == user_id
        token = tokens[0]["token"]
        # Verify token works
        assert patched_email_service.verify_password_reset_token(token) == user_id
        # Expire token artificially
        tokens[0]["expires_at"] = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        assert patched_email_service.verify_password_reset_token(token) is None


class TestEmailVerificationFlow:
    """Flow for email verification tokens."""

    def test_email_verification_flow(self, patched_email_service):  # noqa: D401
        user_id = "user-abc"
        email = "verify@example.com"
        assert patched_email_service.send_email_verification(user_id, email)
        rec = patched_email_service.supabase.auth_tokens._rows[0]
        token = rec["token"]
        assert patched_email_service.verify_email_token(token) == user_id
        # Set wrong type filter
        patched_email_service.supabase.auth_tokens._rows[0]["type"] = "password_reset"
        assert patched_email_service.verify_email_token(token) is None


class TestInvalidateAndCleanup:
    """invalidate_token and cleanup_expired_tokens logic."""

    def test_invalidate_and_cleanup(self, patched_email_service):  # noqa: D401
        user_id = "u2"
        email = "a@b.com"
        # create two tokens
        patched_email_service.send_password_reset_email(user_id, email)
        patched_email_service.send_email_verification(user_id, email)
        tokens = patched_email_service.supabase.auth_tokens._rows
        assert len(tokens) == 2
        # Invalidate first token
        tok = tokens[0]["token"]
        assert patched_email_service.invalidate_token(tok)
        assert len(tokens) == 1
        # Expire remaining token
        tokens[0]["expires_at"] = (datetime.utcnow() - timedelta(days=8)).isoformat()
        deleted = patched_email_service.cleanup_expired_tokens()
        assert deleted == 1
        assert tokens == []