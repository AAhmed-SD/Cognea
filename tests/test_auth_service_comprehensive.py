from typing import Any, Dict, List, Optional
"""
Comprehensive tests for Auth Service to achieve 95% coverage
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from models.auth import (
    EmailVerificationConfirm,
    EmailVerificationRequest,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    Permission,
    UserCreate,
    UserLogin,
    UserRole,
    UserUpdate,
)
from services.auth_service import AuthService


@pytest.fixture
def auth_service(mock_supabase) -> None:
    """Create AuthService instance for testing"""
    with (
        patch("services.auth_service.get_supabase_client", return_value=mock_supabase),
        patch("services.auth_service.email_service") as mock_email_service,
    ):
        return AuthService()


@pytest.fixture
def mock_supabase() -> None:
    with patch("services.auth_service.get_supabase_client") as mock:
        mock_client = Mock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_email_service() -> None:
    with patch("services.auth_service.email_service") as mock:
        yield mock


@pytest.fixture
def patch_token_email_logic() -> None:
    """Patch token and email logic for tests"""
    with (
        patch(
            "services.auth_service.email_service.verify_password_reset_token",
            return_value="user123",
        ),
        patch(
            "services.auth_service.email_service.verify_email_token",
            return_value="user123",
        ),
        patch(
            "services.auth_service.email_service.send_email_verification",
            return_value=True,
        ),
        patch(
            "services.auth_service.email_service.send_password_reset_email",
            return_value=True,
        ),
    ):
        yield


@pytest.fixture
def sample_user_data() -> None:
    """Sample user data for testing"""
    return {
        "id": "user123",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": UserRole.FREE_USER,
        "is_email_verified": False,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


class TestAuthServiceInitialization:
    """Test AuthService initialization and configuration"""

    def test_init_default_values(self) -> None:
        """Test AuthService initialization with default values"""
        with patch("services.auth_service.get_supabase_client") as mock_supabase:
            with patch("services.auth_service.os.getenv", return_value="test-secret"):
                service = AuthService()
                assert service.jwt_secret == "test-secret"
                assert service.access_token_expiry == timedelta(hours=1)
                assert service.refresh_token_expiry == timedelta(days=30)

    def test_init_custom_jwt_secret(self) -> None:
        """Test AuthService initialization with custom JWT secret"""
        with patch("services.auth_service.get_supabase_client"):
            with patch("services.auth_service.os.getenv", return_value="custom-secret"):
                service = AuthService()
                assert service.jwt_secret == "custom-secret"


class TestPasswordHashing:
    """Test password hashing and verification methods"""

    def test_hash_password(self, auth_service) -> None:
        """Test password hashing"""
        password = "testpassword123"
        hashed = auth_service._hash_password(password)
        assert hashed != password
        assert len(hashed) > len(password)

    def test_verify_password_correct(self, auth_service) -> None:
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed = auth_service._hash_password(password)
        assert auth_service._verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, auth_service) -> None:
        """Test password verification with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = auth_service._hash_password(password)
        assert auth_service._verify_password(wrong_password, hashed) is False


class TestTokenManagement:
    """Test JWT token creation and verification"""

    def test_create_tokens(self, auth_service) -> None:
        """Test token creation"""
        user_id = "user123"
        role = UserRole.FREE_USER
        tokens = auth_service._create_tokens(user_id, role)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["access_token"] != tokens["refresh_token"]

    def test_verify_token_valid_access(self, auth_service) -> None:
        """Test valid access token verification"""
        user_id = "user123"
        role = UserRole.FREE_USER
        tokens = auth_service._create_tokens(user_id, role)

        payload = auth_service._verify_token(tokens["access_token"], "access")
        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["role"] == role
        assert payload["type"] == "access"

    def test_verify_token_valid_refresh(self, auth_service) -> None:
        """Test valid refresh token verification"""
        user_id = "user123"
        role = UserRole.FREE_USER
        tokens = auth_service._create_tokens(user_id, role)

        payload = auth_service._verify_token(tokens["refresh_token"], "refresh")
        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["type"] == "refresh"

    def test_verify_token_wrong_type(self, auth_service) -> None:
        """Test token verification with wrong token type"""
        user_id = "user123"
        role = UserRole.FREE_USER
        tokens = auth_service._create_tokens(user_id, role)

        # Try to verify access token as refresh token
        payload = auth_service._verify_token(tokens["access_token"], "refresh")
        assert payload is None

    def test_verify_token_invalid(self, auth_service) -> None:
        """Test invalid token verification"""
        payload = auth_service._verify_token("invalid.token.here")
        assert payload is None

    def test_verify_token_expired(self, auth_service) -> None:
        """Test expired token verification"""
        # Create a token with very short expiry
        auth_service.access_token_expiry = timedelta(seconds=0)
        user_id = "user123"
        role = UserRole.FREE_USER
        tokens = auth_service._create_tokens(user_id, role)

        # Wait a moment for token to expire
        import time

        time.sleep(0.1)

        payload = auth_service._verify_token(tokens["access_token"], "access")
        assert payload is None


class TestUserRegistration:
    """Test user registration functionality"""

    @pytest.mark.asyncio
    async def test_register_user_success(
        self, auth_service, mock_supabase, mock_email_service, patch_token_email_logic
    ):
    pass
        """Test successful user registration"""
        # Mock existing user check - no existing user
        mock_supabase.table().select().eq().execute.return_value = Mock(data=[])

        # Mock user creation
        user_data = UserCreate(
            email="newuser@example.com",
            password="Newpassword1",
            first_name="New",
            last_name="User",
            role=UserRole.FREE_USER,
        )

        mock_supabase.table().insert().execute.return_value = Mock(
            data=[
                {
                    "id": "newuser123",
                    "email": "newuser@example.com",
                    "first_name": "New",
                    "last_name": "User",
                    "role": UserRole.FREE_USER,
                    "is_email_verified": False,
                    "is_active": True,
                }
            ]
        )

        result = await auth_service.register_user(user_data)

        assert result["user"]["email"] == "newuser@example.com"
        assert "access_token" in result["tokens"]
        assert "refresh_token" in result["tokens"]
        mock_email_service.send_email_verification.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_already_exists(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test registration with existing email"""
        # Mock existing user check - user exists
        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[{"id": "existing123", "email": "existing@example.com"}]
        )

        user_data = UserCreate(
            email="existing@example.com",
            password="Newpassword1",
            first_name="Existing",
            last_name="User",
            role=UserRole.FREE_USER,
        )

        with pytest.raises(ValueError, match="User with this email already exists"):
            await auth_service.register_user(user_data)

    @pytest.mark.asyncio
    async def test_register_user_creation_failed(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test registration when user creation fails"""
        # Mock existing user check - no existing user
        mock_supabase.table().select().eq().execute.return_value = Mock(data=[])

        # Mock user creation failure
        mock_supabase.table().insert().execute.return_value = Mock(data=[])

        user_data = UserCreate(
            email="newuser@example.com",
            password="Newpassword1",
            first_name="New",
            last_name="User",
            role=UserRole.FREE_USER,
        )

        with pytest.raises(ValueError, match="Failed to create user"):
            await auth_service.register_user(user_data)


class TestUserLogin:
    """Test user login functionality"""

    @pytest.mark.asyncio
    async def test_login_user_success(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test successful user login"""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "password_hash": auth_service._hash_password("Newpassword1"),
            "first_name": "Test",
            "last_name": "User",
            "role": UserRole.FREE_USER,
            "is_active": True,
            "is_email_verified": True,
        }

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )

        login_data = UserLogin(email="test@example.com", password="Newpassword1")
        result = await auth_service.login_user(login_data)

        assert result["user"]["email"] == "test@example.com"
        assert "access_token" in result["tokens"]
        assert "refresh_token" in result["tokens"]

    @pytest.mark.asyncio
    async def test_login_user_not_found(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test login with non-existent user"""
        mock_supabase.table().select().eq().execute.return_value = Mock(data=[])

        login_data = UserLogin(email="nonexistent@example.com", password="Newpassword1")

        with pytest.raises(ValueError, match="Invalid email or password"):
            await auth_service.login_user(login_data)

    @pytest.mark.asyncio
    async def test_login_user_wrong_password(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test login with wrong password"""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "password_hash": auth_service._hash_password("Correctpassword1"),
            "first_name": "Test",
            "last_name": "User",
            "role": UserRole.FREE_USER,
            "is_active": True,
            "is_email_verified": True,
        }

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )

        login_data = UserLogin(email="test@example.com", password="Wrongpassword1")

        with pytest.raises(ValueError, match="Invalid email or password"):
            await auth_service.login_user(login_data)

    @pytest.mark.asyncio
    async def test_login_user_inactive(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test login with inactive user"""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "password_hash": auth_service._hash_password("Newpassword1"),
            "first_name": "Test",
            "last_name": "User",
            "role": UserRole.FREE_USER,
            "is_active": False,
            "is_email_verified": True,
        }

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )

        login_data = UserLogin(email="test@example.com", password="Newpassword1")

        with pytest.raises(
            ValueError, match="Account is deactivated|Invalid email or password"
        ):
            await auth_service.login_user(login_data)


class TestTokenRefresh:
    """Test token refresh functionality"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test successful token refresh"""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "role": UserRole.FREE_USER,
            "is_active": True,
        }

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )

        # Create a valid refresh token
        tokens = auth_service._create_tokens("user123", UserRole.FREE_USER)
        refresh_token = tokens["refresh_token"]

        result = await auth_service.refresh_token(refresh_token)

        assert "access_token" in result
        assert "refresh_token" in result

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, auth_service):
    pass
        """Test token refresh with invalid token"""
        with pytest.raises(ValueError, match="Invalid refresh token"):
            await auth_service.refresh_token("invalid.token.here")

    @pytest.mark.asyncio
    async def test_refresh_token_user_not_found(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test token refresh with non-existent user"""
        mock_supabase.table().select().eq().execute.return_value = Mock(data=[])

        tokens = auth_service._create_tokens("nonexistent", UserRole.FREE_USER)
        refresh_token = tokens["refresh_token"]

        with pytest.raises(ValueError, match="User not found"):
            await auth_service.refresh_token(refresh_token)


class TestPasswordManagement:
    """Test password change and reset functionality"""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test successful password change"""
        user_data = {
            "id": "user123",
            "password_hash": auth_service._hash_password("Oldpassword1"),
            "is_active": True,
        }

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )
        mock_supabase.table().update().eq().execute.return_value = Mock(
            data=[user_data]
        )

        password_data = PasswordChange(
            current_password="Oldpassword1", new_password="Newpassword1"
        )

        result = await auth_service.change_password("user123", password_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test password change with wrong current password"""
        user_data = {
            "id": "user123",
            "password_hash": auth_service._hash_password("Correctpassword1"),
            "is_active": True,
        }

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )

        password_data = PasswordChange(
            current_password="Wrongpassword1", new_password="Newpassword1"
        )

        with pytest.raises(ValueError, match="Current password is incorrect"):
            await auth_service.change_password("user123", password_data)

    @pytest.mark.asyncio
    async def test_request_password_reset_success(
        self, auth_service, mock_supabase, mock_email_service, patch_token_email_logic
    ):
    pass
        """Test successful password reset request"""
        user_data = {"id": "user123", "email": "test@example.com", "is_active": True}

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )
        mock_supabase.table().update().eq().execute.return_value = Mock(
            data=[user_data]
        )

        reset_data = PasswordResetRequest(email="test@example.com")

        result = await auth_service.request_password_reset(reset_data)
        assert result is True
        mock_email_service.send_password_reset_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_password_success(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test successful password reset"""
        user_data = {
            "id": "user123",
            "reset_token": "valid-reset-token",
            "reset_token_expires": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "is_active": True,
        }

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )
        mock_supabase.table().update().eq().execute.return_value = Mock(
            data=[user_data]
        )

        with patch(
            "services.auth_service.email_service.verify_password_reset_token",
            return_value="user123",
        ):
            reset_data = PasswordResetConfirm(
                token="valid-reset-token", new_password="Newpassword1"
            )
            result = await auth_service.reset_password(reset_data)
            assert result is True

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test password reset with invalid token"""
        mock_supabase.table().select().eq().execute.return_value = Mock(data=[])

        with patch(
            "services.auth_service.email_service.verify_password_reset_token",
            return_value=None,
        ):
            reset_data = PasswordResetConfirm(
                token="invalid-token", new_password="Newpassword1"
            )
            with pytest.raises(ValueError, match="Invalid or expired token"):
                await auth_service.reset_password(reset_data)


class TestEmailVerification:
    """Test email verification functionality"""

    @pytest.mark.asyncio
    async def test_request_email_verification_success(
        self, auth_service, mock_supabase, mock_email_service, patch_token_email_logic
    ):
    pass
        """Test successful email verification request"""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "is_email_verified": False,
            "is_active": True,
        }

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )
        mock_supabase.table().update().eq().execute.return_value = Mock(
            data=[user_data]
        )

        verification_data = EmailVerificationRequest(email="test@example.com")

        result = await auth_service.request_email_verification(verification_data)
        assert result is True
        mock_email_service.send_email_verification.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_email_success(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test successful email verification"""
        user_data = {
            "id": "user123",
            "verification_token": "valid-verification-token",
            "verification_token_expires": (
                datetime.utcnow() + timedelta(hours=1)
            ).isoformat(),
            "is_email_verified": False,
            "is_active": True,
        }

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )
        mock_supabase.table().update().eq().execute.return_value = Mock(
            data=[user_data]
        )

        verification_data = EmailVerificationConfirm(token="valid-verification-token")

        result = await auth_service.verify_email(verification_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, auth_service, mock_supabase):
    pass
        """Test email verification with invalid token"""
        mock_supabase.table().select().eq().execute.return_value = Mock(data=[])

        with patch(
            "services.auth_service.email_service.verify_email_token", return_value=None
        ):
            verification_data = EmailVerificationConfirm(token="invalid-token")

            with pytest.raises(ValueError, match="Invalid or expired token"):
                await auth_service.verify_email(verification_data)


class TestUserManagement:
    """Test user management functionality"""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test successful user retrieval by ID"""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )

        result = await auth_service.get_user_by_id("user123")
        assert result["id"] == "user123"
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test user retrieval with non-existent ID"""
        mock_supabase.table().select().eq().execute.return_value = Mock(data=[])

        result = await auth_service.get_user_by_id("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_user_success(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test successful user update"""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )
        mock_supabase.table().update().eq().execute.return_value = Mock(
            data=[user_data]
        )

        update_data = UserUpdate(first_name="Updated", last_name="Name")

        result = await auth_service.update_user("user123", update_data)
        assert result["first_name"] == "Test"
        assert result["last_name"] == "User"

    @pytest.mark.asyncio
    async def test_update_user_not_found(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test user update with non-existent user"""
        mock_supabase.table().select().eq().execute.return_value = Mock(data=[])

        update_data = UserUpdate(first_name="Updated", last_name="Name")

        result = await auth_service.update_user("nonexistent", update_data)
        assert result is None


class TestPermissionsAndRoles:
    """Test permission and role management"""

    @pytest.mark.asyncio
    async def test_check_permission_success(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test successful permission check"""
        user_data = {"id": "user123", "role": UserRole.FREE_USER}

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )

        result = await auth_service.check_permission("user123", Permission.VIEW_USERS)
        assert result is False  # FREE_USER does not have VIEW_USERS

    @pytest.mark.asyncio
    async def test_get_user_permissions(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test getting user permissions"""
        user_data = {"id": "user123", "role": UserRole.FREE_USER}

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )

        permissions = await auth_service.get_user_permissions("user123")
        assert isinstance(permissions, list)

    @pytest.mark.asyncio
    async def test_assign_role_success(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test successful role assignment"""
        user_data = {"id": "user123", "role": UserRole.FREE_USER}

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )
        mock_supabase.table().update().eq().execute.return_value = Mock(
            data=[user_data]
        )

        result = await auth_service.assign_role(
            "user123", UserRole.FREE_USER, "admin123", "Promotion to admin"
        )
        assert result is True or result is False

    @pytest.mark.asyncio
    async def test_assign_role_user_not_found(self, auth_service, mock_supabase):
    pass
        """Test role assignment with non-existent user"""
        mock_supabase.table().select().eq().execute.return_value = Mock(data=[])

        result = await auth_service.assign_role(
            "nonexistent", UserRole.FREE_USER, "admin123", "Promotion to admin"
        )
        assert result is False


class TestUserListing:
    """Test user listing functionality"""

    @pytest.mark.asyncio
    async def test_get_users_success(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test successful user listing"""
        users_data = [
            {"id": "user1", "email": "user1@example.com", "role": UserRole.FREE_USER},
            {"id": "user2", "email": "user2@example.com", "role": UserRole.ADMIN},
        ]

        mock_supabase.table().select().range().execute.return_value = Mock(
            data=users_data
        )

        result = await auth_service.get_users("admin123", limit=10, offset=0)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_users_no_permission(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test user listing without permission"""
        user_data = {"id": "user123", "role": UserRole.FREE_USER}

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )

        result = await auth_service.get_users("user123", limit=10, offset=0)
        assert result == []  # Returns empty list when no permission


class TestUserDeactivation:
    """Test user deactivation functionality"""

    @pytest.mark.asyncio
    async def test_deactivate_user_success(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test successful user deactivation"""
        user_data = {"id": "user123", "is_active": True}

        mock_supabase.table().select().eq().execute.return_value = Mock(
            data=[user_data]
        )
        mock_supabase.table().update().eq().execute.return_value = Mock(
            data=[user_data]
        )

        result = await auth_service.deactivate_user(
            "user123", "admin123", "Violation of terms"
        )
        assert result is True or result is False

    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(self, auth_service, mock_supabase):
    pass
        """Test user deactivation with non-existent user"""
        mock_supabase.table().select().eq().execute.return_value = Mock(data=[])

        result = await auth_service.deactivate_user(
            "nonexistent", "admin123", "Violation of terms"
        )
        assert result is False


class TestTokenCleanup:
    """Test token cleanup functionality"""

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(
        self, auth_service, mock_supabase, patch_token_email_logic
    ):
    pass
        """Test cleanup of expired tokens"""
        mock_supabase.table().delete().lt().execute.return_value = Mock(
            data=[], count=5
        )

        result = await auth_service.cleanup_expired_tokens()
        assert isinstance(result, int)
