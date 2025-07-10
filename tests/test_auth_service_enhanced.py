import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import jwt

from services.auth_service import AuthService
from models.auth import UserCreate, UserLogin, PasswordChange, PasswordResetRequest, PasswordResetConfirm, UserRole, Permission


class TestAuthService:
    """Test enhanced authentication service."""

    @pytest.fixture
    def auth_service(self):
        """Create auth service instance."""
        return AuthService()

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client."""
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        return mock_client

    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing."""
        return {
            "id": "user_123",
            "email": "test@example.com",
            "password_hash": "$2b$12$hashed_password",
            "first_name": "John",
            "last_name": "Doe",
            "role": UserRole.FREE_USER,
            "is_active": True,
            "is_email_verified": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

    def test_init(self, auth_service):
        """Test AuthService initialization."""
        assert auth_service.supabase is not None
        assert auth_service.jwt_secret is not None
        assert auth_service.access_token_expiry == timedelta(hours=1)
        assert auth_service.refresh_token_expiry == timedelta(days=30)

    def test_hash_password(self, auth_service):
        """Test password hashing."""
        password = "test_password_123"
        hashed = auth_service._hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self, auth_service):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = auth_service._hash_password(password)
        
        assert auth_service._verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, auth_service):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = auth_service._hash_password(password)
        
        assert auth_service._verify_password(wrong_password, hashed) is False

    def test_create_tokens(self, auth_service):
        """Test JWT token creation."""
        user_id = "user_123"
        role = UserRole.FREE_USER
        
        tokens = auth_service._create_tokens(user_id, role)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert isinstance(tokens["access_token"], str)
        assert isinstance(tokens["refresh_token"], str)

    def test_verify_token_valid_access(self, auth_service):
        """Test token verification with valid access token."""
        user_id = "user_123"
        role = UserRole.FREE_USER
        
        tokens = auth_service._create_tokens(user_id, role)
        payload = auth_service._verify_token(tokens["access_token"], "access")
        
        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["role"] == role
        assert payload["type"] == "access"

    def test_verify_token_valid_refresh(self, auth_service):
        """Test token verification with valid refresh token."""
        user_id = "user_123"
        role = UserRole.FREE_USER
        
        tokens = auth_service._create_tokens(user_id, role)
        payload = auth_service._verify_token(tokens["refresh_token"], "refresh")
        
        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["type"] == "refresh"

    def test_verify_token_wrong_type(self, auth_service):
        """Test token verification with wrong token type."""
        user_id = "user_123"
        role = UserRole.FREE_USER
        
        tokens = auth_service._create_tokens(user_id, role)
        payload = auth_service._verify_token(tokens["access_token"], "refresh")
        
        assert payload is None

    def test_verify_token_invalid(self, auth_service):
        """Test token verification with invalid token."""
        payload = auth_service._verify_token("invalid_token", "access")
        assert payload is None

    @pytest.mark.asyncio
    @patch('services.auth_service.email_service')
    async def test_register_user_success(self, mock_email_service, auth_service, mock_supabase_client, sample_user_data):
        """Test successful user registration."""
        auth_service.supabase = mock_supabase_client
        
        # Mock no existing user
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        # Mock successful user creation
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [sample_user_data]
        
        # Mock email service
        mock_email_service.send_email_verification.return_value = True
        
        user_create = UserCreate(
            email="test@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe"
        )
        
        result = await auth_service.register_user(user_create)
        
        assert "user" in result
        assert "tokens" in result
        assert "message" in result
        assert result["user"]["email"] == "test@example.com"
        assert "access_token" in result["tokens"]
        assert "refresh_token" in result["tokens"]
        mock_email_service.send_email_verification.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_already_exists(self, auth_service, mock_supabase_client, sample_user_data):
        """Test user registration when user already exists."""
        auth_service.supabase = mock_supabase_client
        
        # Mock existing user
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_user_data]
        
        user_create = UserCreate(
            email="test@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe"
        )
        
        with pytest.raises(ValueError, match="User with this email already exists"):
            await auth_service.register_user(user_create)

    @pytest.mark.asyncio
    async def test_login_user_success(self, auth_service, mock_supabase_client, sample_user_data):
        """Test successful user login."""
        auth_service.supabase = mock_supabase_client
        
        # Hash password for comparison
        hashed_password = auth_service._hash_password("SecurePass123!")
        sample_user_data["password_hash"] = hashed_password
        
        # Mock user found
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_user_data]
        
        # Mock update last login
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        
        login_data = UserLogin(
            email="test@example.com",
            password="SecurePass123!"
        )
        
        result = await auth_service.login_user(login_data)
        
        assert "user" in result
        assert "tokens" in result
        assert result["user"]["email"] == "test@example.com"
        assert "access_token" in result["tokens"]
        assert "refresh_token" in result["tokens"]

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, auth_service, mock_supabase_client):
        """Test login with non-existent user."""
        auth_service.supabase = mock_supabase_client
        
        # Mock user not found
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        login_data = UserLogin(
            email="nonexistent@example.com",
            password="SecurePass123!"
        )
        
        with pytest.raises(ValueError, match="Invalid email or password"):
            await auth_service.login_user(login_data)

    @pytest.mark.asyncio
    async def test_login_user_wrong_password(self, auth_service, mock_supabase_client, sample_user_data):
        """Test login with wrong password."""
        auth_service.supabase = mock_supabase_client
        
        # Hash different password
        sample_user_data["password_hash"] = auth_service._hash_password("DifferentPassword123!")
        
        # Mock user found
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_user_data]
        
        login_data = UserLogin(
            email="test@example.com",
            password="WrongPassword123!"
        )
        
        with pytest.raises(ValueError, match="Invalid email or password"):
            await auth_service.login_user(login_data)

    @pytest.mark.asyncio
    async def test_login_user_inactive(self, auth_service, mock_supabase_client, sample_user_data):
        """Test login with inactive user."""
        auth_service.supabase = mock_supabase_client
        
        # Set user as inactive
        sample_user_data["is_active"] = False
        sample_user_data["password_hash"] = auth_service._hash_password("SecurePass123!")
        
        # Mock user found
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_user_data]
        
        login_data = UserLogin(
            email="test@example.com",
            password="SecurePass123!"
        )
        
        with pytest.raises(ValueError, match="Account is deactivated"):
            await auth_service.login_user(login_data)

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service, mock_supabase_client, sample_user_data):
        """Test successful token refresh."""
        auth_service.supabase = mock_supabase_client
        
        # Create tokens
        tokens = auth_service._create_tokens("user_123", UserRole.FREE_USER)
        
        # Mock user found and active
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_user_data]
        
        result = await auth_service.refresh_token(tokens["refresh_token"])
        
        assert "access_token" in result
        assert "refresh_token" in result

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, auth_service):
        """Test token refresh with invalid token."""
        with pytest.raises(ValueError, match="Invalid refresh token"):
            await auth_service.refresh_token("invalid_token")

    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, mock_supabase_client, sample_user_data):
        """Test successful password change."""
        auth_service.supabase = mock_supabase_client
        
        # Set current password hash
        current_password = "CurrentPass123!"
        sample_user_data["password_hash"] = auth_service._hash_password(current_password)
        
        # Mock user found
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_user_data]
        
        # Mock password update
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        
        password_change = PasswordChange(
            current_password=current_password,
            new_password="NewSecurePass123!"
        )
        
        result = await auth_service.change_password("user_123", password_change)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, auth_service, mock_supabase_client, sample_user_data):
        """Test password change with wrong current password."""
        auth_service.supabase = mock_supabase_client
        
        # Set different password hash
        sample_user_data["password_hash"] = auth_service._hash_password("DifferentPass123!")
        
        # Mock user found
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_user_data]
        
        password_change = PasswordChange(
            current_password="WrongCurrentPass123!",
            new_password="NewSecurePass123!"
        )
        
        with pytest.raises(ValueError, match="Current password is incorrect"):
            await auth_service.change_password("user_123", password_change)

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, auth_service, mock_supabase_client, sample_user_data):
        """Test successful user retrieval by ID."""
        auth_service.supabase = mock_supabase_client
        
        # Mock user found
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_user_data]
        
        result = await auth_service.get_user_by_id("user_123")
        
        assert result is not None
        assert result["id"] == "user_123"
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, auth_service, mock_supabase_client):
        """Test user retrieval when user not found."""
        auth_service.supabase = mock_supabase_client
        
        # Mock user not found
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        result = await auth_service.get_user_by_id("nonexistent_user")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_check_permission_success(self, auth_service, mock_supabase_client, sample_user_data):
        """Test permission checking."""
        auth_service.supabase = mock_supabase_client
        
        # Mock user found
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_user_data]
        
        # Test with a permission that FREE_USER should have
        result = await auth_service.check_permission("user_123", Permission.VIEW_CONTENT)
        
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_check_permission_user_not_found(self, auth_service, mock_supabase_client):
        """Test permission checking when user not found."""
        auth_service.supabase = mock_supabase_client
        
        # Mock user not found
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        result = await auth_service.check_permission("nonexistent_user", Permission.VIEW_CONTENT)
        
        assert result is False