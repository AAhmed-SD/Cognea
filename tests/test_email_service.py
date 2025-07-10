import pytest
import os
import smtplib
import jwt
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, Mock
from email.mime.multipart import MIMEMultipart

from services.email_service import EmailService, email_service


class TestEmailService:
    """Test EmailService functionality."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_client.table.return_value.delete.return_value.lt.return_value.execute.return_value = MagicMock()
        return mock_client

    @pytest.fixture
    def email_service_instance(self, mock_supabase):
        """Create EmailService instance with mocked Supabase."""
        with patch('services.email_service.get_supabase_client', return_value=mock_supabase):
            service = EmailService()
            return service

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables."""
        env_vars = {
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test@test.com",
            "SMTP_PASSWORD": "test_password",
            "FROM_EMAIL": "noreply@test.com",
            "APP_NAME": "TestApp",
            "APP_URL": "https://test.app",
            "JWT_SECRET": "test-secret-key"
        }
        
        with patch.dict(os.environ, env_vars):
            yield env_vars

    def test_email_service_initialization(self, email_service_instance):
        """Test EmailService initialization."""
        assert email_service_instance.smtp_server == "smtp.gmail.com"
        assert email_service_instance.smtp_port == 587
        assert email_service_instance.from_email == "noreply@cognie.app"
        assert email_service_instance.app_name == "Cognie"
        assert email_service_instance.app_url == "https://cognie.app"
        assert email_service_instance.jwt_secret == "your-secret-key"

    def test_email_service_initialization_with_env_vars(self, mock_env_vars, mock_supabase):
        """Test EmailService initialization with environment variables."""
        with patch('services.email_service.get_supabase_client', return_value=mock_supabase):
            service = EmailService()
            
            assert service.smtp_server == "smtp.test.com"
            assert service.smtp_port == 587
            assert service.smtp_username == "test@test.com"
            assert service.smtp_password == "test_password"
            assert service.from_email == "noreply@test.com"
            assert service.app_name == "TestApp"
            assert service.app_url == "https://test.app"
            assert service.jwt_secret == "test-secret-key"

    def test_create_token(self, email_service_instance):
        """Test JWT token creation."""
        payload = {"user_id": "123", "type": "password_reset"}
        expiry = timedelta(hours=1)
        
        token = email_service_instance._create_token(payload, expiry)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        decoded = jwt.decode(token, email_service_instance.jwt_secret, algorithms=["HS256"])
        assert decoded["user_id"] == "123"
        assert decoded["type"] == "password_reset"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_verify_token_valid(self, email_service_instance):
        """Test JWT token verification with valid token."""
        payload = {"user_id": "123", "type": "password_reset"}
        expiry = timedelta(hours=1)
        
        token = email_service_instance._create_token(payload, expiry)
        verified_payload = email_service_instance._verify_token(token)
        
        assert verified_payload is not None
        assert verified_payload["user_id"] == "123"
        assert verified_payload["type"] == "password_reset"

    def test_verify_token_expired(self, email_service_instance):
        """Test JWT token verification with expired token."""
        payload = {"user_id": "123", "type": "password_reset"}
        expiry = timedelta(seconds=-1)  # Already expired
        
        token = email_service_instance._create_token(payload, expiry)
        verified_payload = email_service_instance._verify_token(token)
        
        assert verified_payload is None

    def test_verify_token_invalid(self, email_service_instance):
        """Test JWT token verification with invalid token."""
        invalid_token = "invalid.token.here"
        
        verified_payload = email_service_instance._verify_token(invalid_token)
        
        assert verified_payload is None

    def test_verify_token_wrong_secret(self, email_service_instance):
        """Test JWT token verification with wrong secret."""
        # Create token with different secret
        payload = {"user_id": "123", "type": "password_reset", "exp": datetime.utcnow() + timedelta(hours=1)}
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        
        verified_payload = email_service_instance._verify_token(token)
        
        assert verified_payload is None

    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, email_service_instance):
        """Test successful email sending."""
        # Set up SMTP credentials
        email_service_instance.smtp_username = "test@test.com"
        email_service_instance.smtp_password = "test_password"
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_service_instance._send_email(
            "recipient@test.com",
            "Test Subject",
            "<h1>Test HTML</h1>",
            "Test Text"
        )
        
        assert result is True
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@test.com", "test_password")
        mock_server.send_message.assert_called_once()

    def test_send_email_no_credentials(self, email_service_instance):
        """Test email sending without SMTP credentials."""
        # Clear SMTP credentials
        email_service_instance.smtp_username = None
        email_service_instance.smtp_password = None
        
        result = email_service_instance._send_email(
            "recipient@test.com",
            "Test Subject",
            "<h1>Test HTML</h1>",
            "Test Text"
        )
        
        assert result is False

    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_smtp_error(self, mock_smtp, email_service_instance):
        """Test email sending with SMTP error."""
        # Set up SMTP credentials
        email_service_instance.smtp_username = "test@test.com"
        email_service_instance.smtp_password = "test_password"
        
        # Mock SMTP server to raise exception
        mock_smtp.side_effect = smtplib.SMTPException("SMTP error")
        
        result = email_service_instance._send_email(
            "recipient@test.com",
            "Test Subject",
            "<h1>Test HTML</h1>",
            "Test Text"
        )
        
        assert result is False

    @patch('services.email_service.smtplib.SMTP')
    def test_send_password_reset_email_success(self, mock_smtp, email_service_instance):
        """Test successful password reset email sending."""
        # Set up SMTP credentials
        email_service_instance.smtp_username = "test@test.com"
        email_service_instance.smtp_password = "test_password"
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_service_instance.send_password_reset_email(
            "user123",
            "user@test.com",
            "Test User"
        )
        
        assert result is True
        
        # Verify token was stored in database
        email_service_instance.supabase.table.assert_called_with("auth_tokens")
        
        # Verify email was sent
        mock_server.send_message.assert_called_once()

    @patch('services.email_service.smtplib.SMTP')
    def test_send_password_reset_email_without_name(self, mock_smtp, email_service_instance):
        """Test password reset email sending without user name."""
        # Set up SMTP credentials
        email_service_instance.smtp_username = "test@test.com"
        email_service_instance.smtp_password = "test_password"
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_service_instance.send_password_reset_email(
            "user123",
            "user@test.com"
        )
        
        assert result is True
        mock_server.send_message.assert_called_once()

    def test_send_password_reset_email_db_error(self, email_service_instance):
        """Test password reset email with database error."""
        # Mock database error
        email_service_instance.supabase.table.return_value.insert.side_effect = Exception("DB error")
        
        result = email_service_instance.send_password_reset_email(
            "user123",
            "user@test.com",
            "Test User"
        )
        
        assert result is False

    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_verification_success(self, mock_smtp, email_service_instance):
        """Test successful email verification sending."""
        # Set up SMTP credentials
        email_service_instance.smtp_username = "test@test.com"
        email_service_instance.smtp_password = "test_password"
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_service_instance.send_email_verification(
            "user123",
            "user@test.com",
            "Test User"
        )
        
        assert result is True
        
        # Verify token was stored in database
        email_service_instance.supabase.table.assert_called_with("auth_tokens")
        
        # Verify email was sent
        mock_server.send_message.assert_called_once()

    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_verification_without_name(self, mock_smtp, email_service_instance):
        """Test email verification sending without user name."""
        # Set up SMTP credentials
        email_service_instance.smtp_username = "test@test.com"
        email_service_instance.smtp_password = "test_password"
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_service_instance.send_email_verification(
            "user123",
            "user@test.com"
        )
        
        assert result is True
        mock_server.send_message.assert_called_once()

    def test_send_email_verification_db_error(self, email_service_instance):
        """Test email verification with database error."""
        # Mock database error
        email_service_instance.supabase.table.return_value.insert.side_effect = Exception("DB error")
        
        result = email_service_instance.send_email_verification(
            "user123",
            "user@test.com",
            "Test User"
        )
        
        assert result is False

    def test_verify_password_reset_token_success(self, email_service_instance):
        """Test successful password reset token verification."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        # Mock database response
        mock_token_data = {
            "user_id": "user123",
            "token": token,
            "type": "password_reset",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        email_service_instance.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_token_data]
        
        result = email_service_instance.verify_password_reset_token(token)
        
        assert result == "user123"

    def test_verify_password_reset_token_invalid_type(self, email_service_instance):
        """Test password reset token verification with wrong type."""
        # Create token with wrong type
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "email_verification"},
            timedelta(hours=1)
        )
        
        result = email_service_instance.verify_password_reset_token(token)
        
        assert result is None

    def test_verify_password_reset_token_not_in_db(self, email_service_instance):
        """Test password reset token verification when token not in database."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        # Mock empty database response
        email_service_instance.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        result = email_service_instance.verify_password_reset_token(token)
        
        assert result is None

    def test_verify_password_reset_token_expired_in_db(self, email_service_instance):
        """Test password reset token verification when token expired in database."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        # Mock database response with expired token
        mock_token_data = {
            "user_id": "user123",
            "token": token,
            "type": "password_reset",
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()  # Expired
        }
        
        email_service_instance.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_token_data]
        
        result = email_service_instance.verify_password_reset_token(token)
        
        assert result is None

    def test_verify_password_reset_token_invalid_token(self, email_service_instance):
        """Test password reset token verification with invalid token."""
        result = email_service_instance.verify_password_reset_token("invalid_token")
        
        assert result is None

    def test_verify_password_reset_token_db_error(self, email_service_instance):
        """Test password reset token verification with database error."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        # Mock database error
        email_service_instance.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        
        result = email_service_instance.verify_password_reset_token(token)
        
        assert result is None

    def test_verify_email_token_success(self, email_service_instance):
        """Test successful email verification token verification."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "email_verification"},
            timedelta(days=1)
        )
        
        # Mock database response
        mock_token_data = {
            "user_id": "user123",
            "token": token,
            "type": "email_verification",
            "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat()
        }
        
        email_service_instance.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_token_data]
        
        result = email_service_instance.verify_email_token(token)
        
        assert result == "user123"

    def test_verify_email_token_invalid_type(self, email_service_instance):
        """Test email verification token verification with wrong type."""
        # Create token with wrong type
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        result = email_service_instance.verify_email_token(token)
        
        assert result is None

    def test_verify_email_token_not_in_db(self, email_service_instance):
        """Test email verification token verification when token not in database."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "email_verification"},
            timedelta(days=1)
        )
        
        # Mock empty database response
        email_service_instance.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        result = email_service_instance.verify_email_token(token)
        
        assert result is None

    def test_verify_email_token_expired_in_db(self, email_service_instance):
        """Test email verification token verification when token expired in database."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "email_verification"},
            timedelta(days=1)
        )
        
        # Mock database response with expired token
        mock_token_data = {
            "user_id": "user123",
            "token": token,
            "type": "email_verification",
            "expires_at": (datetime.utcnow() - timedelta(days=1)).isoformat()  # Expired
        }
        
        email_service_instance.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_token_data]
        
        result = email_service_instance.verify_email_token(token)
        
        assert result is None

    def test_verify_email_token_invalid_token(self, email_service_instance):
        """Test email verification token verification with invalid token."""
        result = email_service_instance.verify_email_token("invalid_token")
        
        assert result is None

    def test_verify_email_token_db_error(self, email_service_instance):
        """Test email verification token verification with database error."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "email_verification"},
            timedelta(days=1)
        )
        
        # Mock database error
        email_service_instance.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        
        result = email_service_instance.verify_email_token(token)
        
        assert result is None

    def test_invalidate_token_success(self, email_service_instance):
        """Test successful token invalidation."""
        token = "test_token"
        
        result = email_service_instance.invalidate_token(token)
        
        assert result is True
        email_service_instance.supabase.table.return_value.delete.return_value.eq.return_value.execute.assert_called_once()

    def test_invalidate_token_db_error(self, email_service_instance):
        """Test token invalidation with database error."""
        token = "test_token"
        
        # Mock database error
        email_service_instance.supabase.table.return_value.delete.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        
        result = email_service_instance.invalidate_token(token)
        
        assert result is False

    def test_cleanup_expired_tokens_success(self, email_service_instance):
        """Test successful cleanup of expired tokens."""
        # Mock database response with deleted tokens
        mock_deleted_tokens = [{"id": 1}, {"id": 2}, {"id": 3}]
        email_service_instance.supabase.table.return_value.delete.return_value.lt.return_value.execute.return_value.data = mock_deleted_tokens
        
        result = email_service_instance.cleanup_expired_tokens()
        
        assert result == 3
        email_service_instance.supabase.table.return_value.delete.return_value.lt.return_value.execute.assert_called_once()

    def test_cleanup_expired_tokens_no_expired(self, email_service_instance):
        """Test cleanup when no expired tokens exist."""
        # Mock database response with no deleted tokens
        email_service_instance.supabase.table.return_value.delete.return_value.lt.return_value.execute.return_value.data = None
        
        result = email_service_instance.cleanup_expired_tokens()
        
        assert result == 0

    def test_cleanup_expired_tokens_db_error(self, email_service_instance):
        """Test cleanup with database error."""
        # Mock database error
        email_service_instance.supabase.table.return_value.delete.return_value.lt.return_value.execute.side_effect = Exception("DB error")
        
        result = email_service_instance.cleanup_expired_tokens()
        
        assert result == 0

    def test_token_expiry_times(self, email_service_instance):
        """Test token expiry time configuration."""
        assert email_service_instance.password_reset_expiry == timedelta(hours=24)
        assert email_service_instance.email_verification_expiry == timedelta(days=7)

    def test_email_content_generation(self, email_service_instance):
        """Test email content generation includes required elements."""
        # Test password reset email content
        with patch.object(email_service_instance, '_send_email', return_value=True) as mock_send:
            email_service_instance.send_password_reset_email(
                "user123",
                "user@test.com",
                "Test User"
            )
            
            # Check that _send_email was called with correct parameters
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            
            # Check email components
            assert call_args[0] == "user@test.com"  # to_email
            assert "Reset Your" in call_args[1]     # subject
            assert "Test User" in call_args[2]      # html_content
            assert "reset-password?token=" in call_args[2]  # reset URL in html
            assert "Test User" in call_args[3]      # text_content
            assert "reset-password?token=" in call_args[3]  # reset URL in text

    def test_email_content_without_name(self, email_service_instance):
        """Test email content generation without user name."""
        with patch.object(email_service_instance, '_send_email', return_value=True) as mock_send:
            email_service_instance.send_password_reset_email(
                "user123",
                "user@test.com"
            )
            
            # Check that _send_email was called
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            
            # Check that content doesn't include user name
            assert "Hello!" in call_args[2]  # html_content should have "Hello!" not "Hello {name}!"
            assert "Hello!" in call_args[3]  # text_content should have "Hello!" not "Hello {name}!"

    def test_email_verification_content_generation(self, email_service_instance):
        """Test email verification content generation."""
        with patch.object(email_service_instance, '_send_email', return_value=True) as mock_send:
            email_service_instance.send_email_verification(
                "user123",
                "user@test.com",
                "Test User"
            )
            
            # Check that _send_email was called with correct parameters
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            
            # Check email components
            assert call_args[0] == "user@test.com"  # to_email
            assert "Verify Your" in call_args[1]    # subject
            assert "Test User" in call_args[2]      # html_content
            assert "verify-email?token=" in call_args[2]  # verify URL in html
            assert "Test User" in call_args[3]      # text_content
            assert "verify-email?token=" in call_args[3]  # verify URL in text

    def test_token_missing_user_id(self, email_service_instance):
        """Test token verification when user_id is missing from payload."""
        # Create token without user_id
        token = email_service_instance._create_token(
            {"type": "password_reset"},
            timedelta(hours=1)
        )
        
        result = email_service_instance.verify_password_reset_token(token)
        
        assert result is None

    def test_datetime_parsing_with_z_suffix(self, email_service_instance):
        """Test datetime parsing with Z suffix from database."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        # Mock database response with Z suffix (use timezone-aware datetime)
        from datetime import timezone
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_token_data = {
            "user_id": "user123",
            "token": token,
            "type": "password_reset",
            "expires_at": future_time.isoformat().replace('+00:00', 'Z')
        }
        
        email_service_instance.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_token_data]
        
        result = email_service_instance.verify_password_reset_token(token)
        
        assert result == "user123"


class TestGlobalEmailService:
    """Test global email service instance."""

    def test_global_email_service_exists(self):
        """Test that global email_service exists."""
        assert email_service is not None
        assert isinstance(email_service, EmailService)

    def test_global_email_service_configuration(self):
        """Test global email service configuration."""
        assert email_service.smtp_server == "smtp.gmail.com"
        assert email_service.smtp_port == 587
        assert email_service.from_email == "noreply@cognie.app"
        assert email_service.app_name == "Cognie"


class TestEmailServiceIntegration:
    """Integration tests for EmailService."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client for integration tests."""
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_client.table.return_value.delete.return_value.lt.return_value.execute.return_value = MagicMock()
        return mock_client

    @pytest.fixture
    def email_service_with_real_config(self, mock_supabase):
        """Create EmailService with real configuration for integration tests."""
        with patch('services.email_service.get_supabase_client', return_value=mock_supabase):
            service = EmailService()
            service.smtp_username = "test@test.com"
            service.smtp_password = "test_password"
            service.jwt_secret = "integration-test-secret"
            return service

    def test_full_password_reset_workflow(self, email_service_with_real_config):
        """Test complete password reset workflow."""
        service = email_service_with_real_config
        
        # Mock successful email sending
        with patch.object(service, '_send_email', return_value=True):
            # Send password reset email
            result = service.send_password_reset_email(
                "user123",
                "user@test.com",
                "Test User"
            )
            
            assert result is True
            
            # Verify token was created and stored
            service.supabase.table.assert_called_with("auth_tokens")
            insert_call = service.supabase.table.return_value.insert.call_args[0][0]
            
            assert insert_call["user_id"] == "user123"
            assert insert_call["type"] == "password_reset"
            assert "token" in insert_call
            assert "expires_at" in insert_call
            
            # Extract token and verify it
            token = insert_call["token"]
            
            # Mock database response for token verification
            service.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [insert_call]
            
            # Verify token
            user_id = service.verify_password_reset_token(token)
            assert user_id == "user123"

    def test_full_email_verification_workflow(self, email_service_with_real_config):
        """Test complete email verification workflow."""
        service = email_service_with_real_config
        
        # Mock successful email sending
        with patch.object(service, '_send_email', return_value=True):
            # Send email verification
            result = service.send_email_verification(
                "user123",
                "user@test.com",
                "Test User"
            )
            
            assert result is True
            
            # Verify token was created and stored
            service.supabase.table.assert_called_with("auth_tokens")
            insert_call = service.supabase.table.return_value.insert.call_args[0][0]
            
            assert insert_call["user_id"] == "user123"
            assert insert_call["type"] == "email_verification"
            assert "token" in insert_call
            assert "expires_at" in insert_call
            
            # Extract token and verify it
            token = insert_call["token"]
            
            # Mock database response for token verification
            service.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [insert_call]
            
            # Verify token
            user_id = service.verify_email_token(token)
            assert user_id == "user123"

    def test_token_lifecycle_management(self, email_service_with_real_config):
        """Test complete token lifecycle management."""
        service = email_service_with_real_config
        
        # Create token
        token = service._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        # Mock database responses
        mock_token_data = {
            "user_id": "user123",
            "token": token,
            "type": "password_reset",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        service.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_token_data]
        
        # Verify token
        user_id = service.verify_password_reset_token(token)
        assert user_id == "user123"
        
        # Invalidate token
        result = service.invalidate_token(token)
        assert result is True
        
        # Cleanup expired tokens
        service.supabase.table.return_value.delete.return_value.lt.return_value.execute.return_value.data = [{"id": 1}]
        cleanup_count = service.cleanup_expired_tokens()
        assert cleanup_count == 1

    def test_error_handling_throughout_workflow(self, email_service_with_real_config):
        """Test error handling throughout the workflow."""
        service = email_service_with_real_config
        
        # Test database error during token creation
        service.supabase.table.return_value.insert.side_effect = Exception("DB error")
        
        result = service.send_password_reset_email(
            "user123",
            "user@test.com",
            "Test User"
        )
        
        assert result is False
        
        # Reset mock
        service.supabase.table.return_value.insert.side_effect = None
        
        # Test email sending error
        with patch.object(service, '_send_email', return_value=False):
            result = service.send_password_reset_email(
                "user123",
                "user@test.com",
                "Test User"
            )
            
            assert result is False

    def test_concurrent_token_operations(self, email_service_with_real_config):
        """Test concurrent token operations."""
        service = email_service_with_real_config
        
        # Create multiple tokens
        tokens = []
        for i in range(5):
            token = service._create_token(
                {"user_id": f"user{i}", "type": "password_reset"},
                timedelta(hours=1)
            )
            tokens.append(token)
        
        # Verify all tokens
        for i, token in enumerate(tokens):
            # Mock database response
            mock_token_data = {
                "user_id": f"user{i}",
                "token": token,
                "type": "password_reset",
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
            
            service.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_token_data]
            
            user_id = service.verify_password_reset_token(token)
            assert user_id == f"user{i}"