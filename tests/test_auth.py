from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException, status

from services.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)


class TestHashPassword:
    """Test password hashing functionality"""

    def test_hash_password(self) -> None:
        """Test password hashing"""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > len(password)

    def test_hash_password_empty(self) -> None:
        """Test hashing empty password"""
        password = ""
        hashed = hash_password(password)

        assert hashed != password
        assert isinstance(hashed, str)


class TestVerifyPassword:
    """Test password verification functionality"""

    def test_verify_password_correct(self) -> None:
        """Test correct password verification"""
        password = "testpassword123"
        hashed = hash_password(password)

        result = verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self) -> None:
        """Test incorrect password verification"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        result = verify_password(wrong_password, hashed)
        assert result is False


class TestCreateAccessToken:
    """Test JWT token creation"""

    @patch("services.auth.security_config")
    def test_create_access_token(self, mock_security_config) -> None:
        """Test creating access token"""
        mock_security_config.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_security_config.SECRET_KEY = "test_secret_key"
        mock_security_config.JWT_ALGORITHM = "HS256"

        data = {"sub": "test@example.com", "role": "user"}

        with patch("services.auth.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            token = create_access_token(data)

            assert isinstance(token, str)
            assert len(token) > 0


class TestGetCurrentUser:
    """Test current user retrieval from JWT token"""

    @patch("services.auth.get_supabase_client")
    @patch("services.auth.security_config")
    def test_get_current_user_valid_token(
        self, mock_security_config, mock_get_supabase
    ) -> None:
        """Test getting current user with valid token"""
        mock_security_config.SECRET_KEY = "test_secret_key"
        mock_security_config.JWT_ALGORITHM = "HS256"

        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        user_data = {"id": "user123", "email": "test@example.com", "role": "user"}
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            user_data
        ]

        token_data = {"sub": "test@example.com"}
        token = jwt.encode(
            token_data,
            mock_security_config.SECRET_KEY,
            algorithm=mock_security_config.JWT_ALGORITHM,
        )

        result = get_current_user(token)

        assert result["id"] == "user123"
        assert result["email"] == "test@example.com"
        assert result["role"] == "user"

    @patch("services.auth.security_config")
    def test_get_current_user_invalid_token(self, mock_security_config) -> None:
        """Test getting current user with invalid token"""
        mock_security_config.SECRET_KEY = "test_secret_key"
        mock_security_config.JWT_ALGORITHM = "HS256"

        invalid_token = "invalid_token"

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(invalid_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

    @patch("services.auth.get_supabase_client")
    @patch("services.auth.security_config")
    def test_get_current_user_user_not_found(
        self, mock_security_config, mock_get_supabase
    ) -> None:
        """Test getting current user when user not found in database"""
        mock_security_config.SECRET_KEY = "test_secret_key"
        mock_security_config.JWT_ALGORITHM = "HS256"

        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
            []
        )

        token_data = {"sub": "test@example.com"}
        token = jwt.encode(
            token_data,
            mock_security_config.SECRET_KEY,
            algorithm=mock_security_config.JWT_ALGORITHM,
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

    @patch("services.auth.security_config")
    def test_get_current_user_token_without_sub(self, mock_security_config) -> None:
        """Test getting current user with token missing sub claim"""
        mock_security_config.SECRET_KEY = "test_secret_key"
        mock_security_config.JWT_ALGORITHM = "HS256"

        # Create token without sub claim
        token_data = {"role": "user"}
        token = jwt.encode(
            token_data,
            mock_security_config.SECRET_KEY,
            algorithm=mock_security_config.JWT_ALGORITHM,
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"
