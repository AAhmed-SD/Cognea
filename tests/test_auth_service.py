from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest

from models.auth import UserCreate, UserRole
from services.auth_service import AuthService


@pytest.fixture
def auth_service() -> None:
    return AuthService()


@patch("services.auth_service.get_supabase_client")
@patch("services.auth_service.email_service")
def test_register_user_success(mock_email_service, mock_supabase_client, auth_service) -> None:
    user_data = UserCreate(
        email="test@example.com",
        password="Abcdefg1",
        first_name="Test",
        last_name="User",
    )
    # Setup full supabase mock chain
    mock_supabase = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_insert = MagicMock()
    # Chain: table().select().eq().execute().data = []
    mock_eq.execute.return_value.data = []
    mock_select.eq.return_value = mock_eq
    mock_table.select.return_value = mock_select
    # Chain: table().insert().execute().data = [{...}]
    mock_insert.execute.return_value.data = [
        {"id": "u1", "email": user_data.email, "first_name": "Test"}
    ]
    mock_table.insert.return_value = mock_insert
    mock_supabase.table.return_value = mock_table
    mock_supabase_client.return_value = mock_supabase
    # Patch _hash_password
    with patch.object(AuthService, "_hash_password", return_value="hashedpw"):
        # Patch _create_tokens
        with patch.object(
            AuthService,
            "_create_tokens",
            return_value={"access_token": "a", "refresh_token": "r"},
        ):
            import asyncio

            result = asyncio.run(auth_service.register_user(user_data))
            assert result["user"]["email"] == user_data.email
            assert result["tokens"]["access_token"] == "a"
            mock_email_service.send_email_verification.assert_called_once()


@patch("services.auth_service.get_supabase_client")
@patch("services.auth_service.email_service")
def test_register_user_existing_email(
    mock_email_service, mock_supabase_client, auth_service
) -> None:
    user_data = UserCreate(
        email="test@example.com",
        password="Abcdefg1",
        first_name="Test",
        last_name="User",
    )
    # Setup full supabase mock chain
    mock_supabase = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    # Chain: table().select().eq().execute().data = [{...}]
    mock_eq.execute.return_value.data = [{"id": "u1"}]
    mock_select.eq.return_value = mock_eq
    mock_table.select.return_value = mock_select
    mock_supabase.table.return_value = mock_table
    mock_supabase_client.return_value = mock_supabase
    with pytest.raises(ValueError, match="User with this email already exists"):
        import asyncio

        asyncio.run(auth_service.register_user(user_data))


@patch("services.auth_service.get_supabase_client")
def test_hash_and_verify_password(mock_supabase_client, auth_service) -> None:
    pw = "Abcdefg1"
    hashed = auth_service._hash_password(pw)
    assert auth_service._verify_password(pw, hashed)
    assert not auth_service._verify_password("wrongpw", hashed)


@patch("services.auth_service.get_supabase_client")
def test_create_and_verify_tokens(mock_supabase_client, auth_service) -> None:
    tokens = auth_service._create_tokens("u1", UserRole.ADMIN)
    assert "access_token" in tokens and "refresh_token" in tokens
    payload = auth_service._verify_token(tokens["access_token"], token_type="access")
    assert payload["user_id"] == "u1"
    assert payload["role"] == UserRole.ADMIN
    # Wrong type
    assert (
        auth_service._verify_token(tokens["access_token"], token_type="refresh") is None
    )
    # Expired token
    expired_token = jwt.encode(
        {"user_id": "u1", "type": "access", "exp": 1},
        auth_service.jwt_secret,
        algorithm="HS256",
    )
    assert auth_service._verify_token(expired_token, token_type="access") is None
    # Invalid token
    assert auth_service._verify_token("invalid.token", token_type="access") is None
