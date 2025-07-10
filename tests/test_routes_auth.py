import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
from fastapi import HTTPException
from fastapi.testclient import TestClient

from routes.auth import router


class TestAuthRouter:
    """Test authentication router endpoints."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        mock_client = MagicMock()
        return mock_client

    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing."""
        return {
            "id": "user123",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }

    @pytest.fixture
    def registration_data(self):
        """Sample registration data."""
        return {
            "email": "newuser@example.com",
            "password": "SecurePassword123!"
        }

    @pytest.fixture
    def login_data(self):
        """Sample login data."""
        return {
            "email": "test@example.com",
            "password": "Password123!"
        }

    def test_router_tags(self):
        """Test router has correct tags."""
        assert "authentication" in router.tags

    def test_router_endpoints_exist(self):
        """Test that all expected endpoints exist in router."""
        # Get all route paths
        routes = []
        for route in router.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)

        # Check main auth endpoints exist (based on actual routes)
        expected_endpoints = ["/signup", "/login", "/token", "/me", "/forgot-password", "/reset-password"]
        for endpoint in expected_endpoints:
            # Check if any route contains the endpoint
            assert any(endpoint in route for route in routes), f"Endpoint {endpoint} not found"

    def test_signup_success(self, mock_supabase, sample_user_data, registration_data):
        """Test successful user signup."""
        # Import the function we want to test
        from routes.auth import signup
        
        # Mock Supabase auth response
        mock_auth_response = MagicMock()
        mock_auth_response.user = MagicMock()
        mock_auth_response.user.id = "user123"
        mock_auth_response.user.email = "test@example.com"
        
        mock_supabase.auth.sign_up.return_value = mock_auth_response
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [sample_user_data]

        with patch('routes.auth.get_supabase_client', return_value=mock_supabase), \
             patch('routes.auth.create_access_token') as mock_token:
            
            mock_token.return_value = "access_token_123"

            # Mock the registration request
            from routes.auth import UserCreate
            request = UserCreate(**registration_data)
            
            result = signup(request)

            assert "user" in result
            assert "access_token" in result
            assert result["user"]["email"] == "newuser@example.com"
            mock_supabase.auth.sign_up.assert_called_once()

    def test_signup_email_exists(self, mock_supabase, registration_data):
        """Test signup with existing email."""
        from routes.auth import signup
        
        # Mock Supabase auth to raise exception for existing user
        mock_supabase.auth.sign_up.side_effect = Exception("User already registered")

        with patch('routes.auth.get_supabase_client', return_value=mock_supabase), \
             patch('routes.auth.validate_password_strength', return_value=(True, None)), \
             pytest.raises(HTTPException) as exc_info:
            
            from routes.auth import UserCreate
            request = UserCreate(**registration_data)
            signup(request)

        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)

    def test_login_success(self, mock_supabase, sample_user_data, login_data):
        """Test successful login."""
        from routes.auth import login
        
        # Mock Supabase auth response
        mock_auth_response = MagicMock()
        mock_auth_response.user = MagicMock()
        mock_auth_response.user.id = "user123"
        mock_auth_response.user.email = "test@example.com"
        
        mock_supabase.auth.sign_in_with_password.return_value = mock_auth_response

        with patch('routes.auth.get_supabase_client', return_value=mock_supabase), \
             patch('routes.auth.create_access_token') as mock_token:
            
            mock_token.return_value = "access_token_123"

            from routes.auth import UserLogin
            request = UserLogin(**login_data)
            result = login(request)

            assert "user" in result
            assert "access_token" in result
            assert result["access_token"] == "access_token_123"
            mock_supabase.auth.sign_in_with_password.assert_called_once()

    def test_login_invalid_credentials(self, mock_supabase, login_data):
        """Test login with invalid credentials."""
        from routes.auth import login
        
        # Mock Supabase auth to raise exception
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")

        with patch('routes.auth.get_supabase_client', return_value=mock_supabase), \
             pytest.raises(HTTPException) as exc_info:
            
            from routes.auth import UserLogin
            request = UserLogin(**login_data)
            login(request)

        assert exc_info.value.status_code == 401
        assert "Incorrect email or password" in str(exc_info.value.detail)

    def test_login_wrong_password(self, mock_supabase, sample_user_data, login_data):
        """Test login with wrong password."""
        from routes.auth import login
        
        # Mock Supabase auth to return no user
        mock_auth_response = MagicMock()
        mock_auth_response.user = None
        mock_supabase.auth.sign_in_with_password.return_value = mock_auth_response

        with patch('routes.auth.get_supabase_client', return_value=mock_supabase), \
             pytest.raises(HTTPException) as exc_info:
            
            from routes.auth import UserLogin
            request = UserLogin(**login_data)
            login(request)

        assert exc_info.value.status_code == 401
        assert "Incorrect email or password" in str(exc_info.value.detail)

    def test_get_current_user_success(self, sample_user_data):
        """Test getting current user profile."""
        from routes.auth import get_current_user_info
        
        # Mock current user object with attributes
        class MockUser:
            def __init__(self, data):
                self.id = data["id"]
                self.email = data["email"]
        
        current_user = MockUser(sample_user_data)

        result = get_current_user_info(current_user)

        assert "id" in result
        assert "email" in result
        assert result["email"] == "test@example.com"

    def test_forgot_password_success(self, mock_supabase):
        """Test successful password reset request."""
        from routes.auth import forgot_password
        
        with patch('routes.auth.get_supabase_client', return_value=mock_supabase):
            from routes.auth import ForgotPasswordRequest
            request = ForgotPasswordRequest(email="test@example.com")
            
            result = forgot_password(request)

            assert "message" in result
            mock_supabase.auth.reset_password_email.assert_called_once_with("test@example.com")

    def test_reset_password_success(self, mock_supabase):
        """Test successful password reset."""
        from routes.auth import reset_password
        
        with patch('routes.auth.get_supabase_client', return_value=mock_supabase):
            from routes.auth import ResetPasswordRequest
            request = ResetPasswordRequest(token="reset_token", new_password="NewPassword123!")
            
            result = reset_password(request)

            assert "message" in result


class TestAuthHelperFunctions:
    """Test authentication helper functions."""

    def test_password_validation(self):
        """Test password validation functionality."""
        from config.security import validate_password_strength
        
        # Test valid password
        is_valid, message = validate_password_strength("ValidPassword123!")
        assert is_valid
        
        # Test invalid password (too short)
        is_valid, message = validate_password_strength("short")
        assert not is_valid

    def test_token_creation(self):
        """Test JWT token creation."""
        from services.auth import create_access_token
        
        user_data = {"sub": "test@example.com"}
        
        with patch('jwt.encode') as mock_encode:
            mock_encode.return_value = "jwt_token"
            
            token = create_access_token(user_data)
            
            assert token == "jwt_token"
            mock_encode.assert_called_once()


class TestAuthIntegration:
    """Integration tests for authentication flow."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        mock_client = MagicMock()
        return mock_client

    def test_full_signup_login_flow(self, mock_supabase):
        """Test complete signup and login flow."""
        from routes.auth import signup, login
        
        # Registration data
        reg_data = {
            "email": "integration@test.com",
            "password": "Password123!"
        }

        # Mock user creation
        user_data = {
            "id": "user123",
            "email": "integration@test.com"
        }

        with patch('routes.auth.get_supabase_client', return_value=mock_supabase), \
             patch('routes.auth.create_access_token') as mock_token, \
             patch('routes.auth.validate_password_strength', return_value=(True, None)):

            # Setup mocks
            mock_token.return_value = "access_token"

            # Mock signup response
            mock_auth_response = MagicMock()
            mock_auth_response.user = MagicMock()
            mock_auth_response.user.id = "user123"
            mock_auth_response.user.email = "integration@test.com"
            
            mock_supabase.auth.sign_up.return_value = mock_auth_response
            mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [user_data]

            # Register user
            from routes.auth import UserCreate
            reg_request = UserCreate(**reg_data)
            reg_result = signup(reg_request)

            assert "user" in reg_result
            assert "access_token" in reg_result

            # Now test login
            mock_supabase.auth.sign_in_with_password.return_value = mock_auth_response

            from routes.auth import UserLogin
            login_request = UserLogin(email=reg_data["email"], password=reg_data["password"])
            login_result = login(login_request)

            assert "user" in login_result
            assert "access_token" in login_result