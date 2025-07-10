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
            "password": "securepassword123",
            "first_name": "Jane",
            "last_name": "Smith"
        }

    @pytest.fixture
    def login_data(self):
        """Sample login data."""
        return {
            "email": "test@example.com",
            "password": "password123"
        }

    def test_router_tags(self):
        """Test router has correct tags."""
        assert "Authentication" in router.tags

    def test_router_endpoints_exist(self):
        """Test that all expected endpoints exist in router."""
        # Get all route paths
        routes = []
        for route in router.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        # Check main auth endpoints exist
        expected_endpoints = ["/register", "/login", "/logout", "/refresh", "/me"]
        for endpoint in expected_endpoints:
            # Check if any route contains the endpoint
            assert any(endpoint in route for route in routes), f"Endpoint {endpoint} not found"

    @pytest.mark.asyncio
    async def test_register_success(self, mock_supabase, sample_user_data, registration_data):
        """Test successful user registration."""
        # Import the function we want to test
        from routes.auth import register
        
        # Mock Supabase response for user creation
        mock_result = MagicMock()
        mock_result.data = [sample_user_data]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result

        # Mock email service
        with patch('routes.auth.get_supabase_client', return_value=mock_supabase), \
             patch('routes.auth.email_service') as mock_email_service, \
             patch('routes.auth.bcrypt.hashpw') as mock_hash:
            
            mock_hash.return_value = b"hashed_password"
            mock_email_service.send_email_verification.return_value = True

            # Mock the registration request
            from pydantic import BaseModel
            class RegisterRequest(BaseModel):
                email: str
                password: str
                first_name: str
                last_name: str

            request = RegisterRequest(**registration_data)
            
            result = await register(request)

            assert "user" in result
            assert "access_token" in result
            assert result["user"]["email"] == sample_user_data["email"]
            mock_supabase.table.assert_called_with("users")

    @pytest.mark.asyncio
    async def test_register_email_exists(self, mock_supabase, registration_data):
        """Test registration with existing email."""
        from routes.auth import register
        
        # Mock Supabase to return existing user
        mock_result = MagicMock()
        mock_result.data = [{"email": "newuser@example.com"}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        with patch('routes.auth.get_supabase_client', return_value=mock_supabase), \
             pytest.raises(HTTPException) as exc_info:
            
            from pydantic import BaseModel
            class RegisterRequest(BaseModel):
                email: str
                password: str
                first_name: str
                last_name: str

            request = RegisterRequest(**registration_data)
            await register(request)

        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_success(self, mock_supabase, sample_user_data, login_data):
        """Test successful login."""
        from routes.auth import login
        
        # Mock Supabase response for user lookup
        user_with_password = sample_user_data.copy()
        user_with_password["password"] = "hashed_password"
        
        mock_result = MagicMock()
        mock_result.data = [user_with_password]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        with patch('routes.auth.get_supabase_client', return_value=mock_supabase), \
             patch('routes.auth.bcrypt.checkpw') as mock_check, \
             patch('routes.auth.create_access_token') as mock_token:
            
            mock_check.return_value = True
            mock_token.return_value = "access_token_123"

            from pydantic import BaseModel
            class LoginRequest(BaseModel):
                email: str
                password: str

            request = LoginRequest(**login_data)
            result = await login(request)

            assert "user" in result
            assert "access_token" in result
            assert result["access_token"] == "access_token_123"
            mock_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_supabase, login_data):
        """Test login with invalid credentials."""
        from routes.auth import login
        
        # Mock Supabase to return no user
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        with patch('routes.auth.get_supabase_client', return_value=mock_supabase), \
             pytest.raises(HTTPException) as exc_info:
            
            from pydantic import BaseModel
            class LoginRequest(BaseModel):
                email: str
                password: str

            request = LoginRequest(**login_data)
            await login(request)

        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, mock_supabase, sample_user_data, login_data):
        """Test login with wrong password."""
        from routes.auth import login
        
        # Mock Supabase response with user
        user_with_password = sample_user_data.copy()
        user_with_password["password"] = "hashed_password"
        
        mock_result = MagicMock()
        mock_result.data = [user_with_password]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        with patch('routes.auth.get_supabase_client', return_value=mock_supabase), \
             patch('routes.auth.bcrypt.checkpw') as mock_check, \
             pytest.raises(HTTPException) as exc_info:
            
            mock_check.return_value = False  # Wrong password

            from pydantic import BaseModel
            class LoginRequest(BaseModel):
                email: str
                password: str

            request = LoginRequest(**login_data)
            await login(request)

        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_supabase, sample_user_data):
        """Test getting current user profile."""
        from routes.auth import get_current_user_profile
        
        # Mock current user from dependency
        current_user = sample_user_data

        result = await get_current_user_profile(current_user)

        assert result == current_user
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_logout_success(self):
        """Test successful logout."""
        from routes.auth import logout
        
        # Mock current user
        current_user = {"id": "user123"}

        with patch('routes.auth.invalidate_token') as mock_invalidate:
            mock_invalidate.return_value = True
            
            result = await logout(current_user)

            assert result == {"message": "Successfully logged out"}

    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test successful token refresh."""
        from routes.auth import refresh_token
        
        refresh_data = {"refresh_token": "valid_refresh_token"}

        with patch('routes.auth.verify_refresh_token') as mock_verify, \
             patch('routes.auth.create_access_token') as mock_create:
            
            mock_verify.return_value = {"user_id": "user123"}
            mock_create.return_value = "new_access_token"

            from pydantic import BaseModel
            class RefreshRequest(BaseModel):
                refresh_token: str

            request = RefreshRequest(**refresh_data)
            result = await refresh_token(request)

            assert "access_token" in result
            assert result["access_token"] == "new_access_token"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self):
        """Test token refresh with invalid token."""
        from routes.auth import refresh_token
        
        refresh_data = {"refresh_token": "invalid_token"}

        with patch('routes.auth.verify_refresh_token') as mock_verify, \
             pytest.raises(HTTPException) as exc_info:
            
            mock_verify.return_value = None  # Invalid token

            from pydantic import BaseModel
            class RefreshRequest(BaseModel):
                refresh_token: str

            request = RefreshRequest(**refresh_data)
            await refresh_token(request)

        assert exc_info.value.status_code == 401
        assert "Invalid refresh token" in str(exc_info.value.detail)


class TestAuthHelperFunctions:
    """Test authentication helper functions."""

    def test_password_hashing(self):
        """Test password hashing functionality."""
        import bcrypt
        
        password = "test_password"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Verify password can be checked
        assert bcrypt.checkpw(password.encode('utf-8'), hashed)
        assert not bcrypt.checkpw("wrong_password".encode('utf-8'), hashed)

    def test_token_creation(self):
        """Test JWT token creation."""
        from routes.auth import create_access_token
        
        user_data = {"user_id": "123", "email": "test@example.com"}
        
        with patch('routes.auth.jwt.encode') as mock_encode:
            mock_encode.return_value = "jwt_token"
            
            token = create_access_token(user_data)
            
            assert token == "jwt_token"
            mock_encode.assert_called_once()


class TestAuthIntegration:
    """Integration tests for authentication flow."""

    @pytest.mark.asyncio
    async def test_full_registration_login_flow(self, mock_supabase):
        """Test complete registration and login flow."""
        from routes.auth import register, login
        
        # Registration data
        reg_data = {
            "email": "integration@test.com",
            "password": "password123",
            "first_name": "Integration",
            "last_name": "Test"
        }

        # Mock user creation
        user_data = {
            "id": "user123",
            "email": "integration@test.com",
            "first_name": "Integration",
            "last_name": "Test"
        }

        with patch('routes.auth.get_supabase_client', return_value=mock_supabase), \
             patch('routes.auth.email_service') as mock_email, \
             patch('routes.auth.bcrypt.hashpw') as mock_hash, \
             patch('routes.auth.bcrypt.checkpw') as mock_check, \
             patch('routes.auth.create_access_token') as mock_token:

            # Setup mocks
            mock_hash.return_value = b"hashed_password"
            mock_check.return_value = True
            mock_token.return_value = "access_token"
            mock_email.send_email_verification.return_value = True

            # Mock registration responses
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []  # No existing user
            mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [user_data]

            # Register user
            from pydantic import BaseModel
            class RegisterRequest(BaseModel):
                email: str
                password: str
                first_name: str
                last_name: str

            reg_request = RegisterRequest(**reg_data)
            reg_result = await register(reg_request)

            assert "user" in reg_result
            assert "access_token" in reg_result

            # Now test login
            user_with_password = user_data.copy()
            user_with_password["password"] = "hashed_password"
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [user_with_password]

            class LoginRequest(BaseModel):
                email: str
                password: str

            login_request = LoginRequest(email=reg_data["email"], password=reg_data["password"])
            login_result = await login(login_request)

            assert "user" in login_result
            assert "access_token" in login_result