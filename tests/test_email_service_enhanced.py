import pytest
import jwt
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
import smtplib

from services.email_service import EmailService, email_service


class TestEmailService:
    """Comprehensive tests for EmailService."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        return mock_supabase

    @pytest.fixture
    def email_svc(self, mock_supabase):
        """Create EmailService with mocked dependencies."""
        with patch('services.email_service.get_supabase_client', return_value=mock_supabase):
            service = EmailService()
            service.smtp_username = "test@example.com"
            service.smtp_password = "test_password"
            service.jwt_secret = "test_secret"
            return service

    def test_init_default_values(self, mock_supabase):
        """Test EmailService initialization with default values."""
        with patch('services.email_service.get_supabase_client', return_value=mock_supabase):
            service = EmailService()
            
            assert service.smtp_server == "smtp.gmail.com"
            assert service.smtp_port == 587
            assert service.from_email == "noreply@cognie.app"
            assert service.app_name == "Cognie"
            assert service.app_url == "https://cognie.app"
            assert service.password_reset_expiry == timedelta(hours=24)
            assert service.email_verification_expiry == timedelta(days=7)

    def test_init_with_env_vars(self, mock_supabase):
        """Test EmailService initialization with environment variables."""
        env_vars = {
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "465",
            "SMTP_USERNAME": "user@test.com",
            "SMTP_PASSWORD": "test_pass",
            "FROM_EMAIL": "noreply@test.com",
            "APP_NAME": "TestApp",
            "APP_URL": "https://test.app",
            "JWT_SECRET": "test_secret"
        }
        
        with patch.dict('os.environ', env_vars), \
             patch('services.email_service.get_supabase_client', return_value=mock_supabase):
            
            service = EmailService()
            
            assert service.smtp_server == "smtp.test.com"
            assert service.smtp_port == 465
            assert service.smtp_username == "user@test.com"
            assert service.smtp_password == "test_pass"
            assert service.from_email == "noreply@test.com"
            assert service.app_name == "TestApp"
            assert service.app_url == "https://test.app"
            assert service.jwt_secret == "test_secret"

    def test_create_token(self, email_svc):
        """Test JWT token creation."""
        payload = {"user_id": "123", "type": "test"}
        expiry = timedelta(hours=1)
        
        token = email_svc._create_token(payload, expiry)
        
        # Decode and verify token
        decoded = jwt.decode(token, email_svc.jwt_secret, algorithms=["HS256"])
        assert decoded["user_id"] == "123"
        assert decoded["type"] == "test"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_verify_token_valid(self, email_svc):
        """Test verifying a valid token."""
        payload = {"user_id": "123", "type": "test"}
        token = email_svc._create_token(payload, timedelta(hours=1))
        
        result = email_svc._verify_token(token)
        
        assert result is not None
        assert result["user_id"] == "123"
        assert result["type"] == "test"

    def test_verify_token_expired(self, email_svc):
        """Test verifying an expired token."""
        payload = {"user_id": "123", "type": "test"}
        token = email_svc._create_token(payload, timedelta(seconds=-1))  # Already expired
        
        with patch('services.email_service.logger') as mock_logger:
            result = email_svc._verify_token(token)
            
            assert result is None
            mock_logger.warning.assert_called_with("Token has expired")

    def test_verify_token_invalid(self, email_svc):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.here"
        
        with patch('services.email_service.logger') as mock_logger:
            result = email_svc._verify_token(invalid_token)
            
            assert result is None
            mock_logger.warning.assert_called_with("Invalid token")

    def test_send_email_success(self, email_svc):
        """Test successful email sending."""
        mock_server = MagicMock()
        
        with patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email_service.logger') as mock_logger:
            
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = email_svc._send_email(
                "test@example.com",
                "Test Subject",
                "<h1>HTML Content</h1>",
                "Text Content"
            )
            
            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("test@example.com", "test_password")
            mock_server.send_message.assert_called_once()
            mock_logger.info.assert_called_with("Email sent successfully to test@example.com")

    def test_send_email_no_credentials(self, email_svc):
        """Test email sending without SMTP credentials."""
        email_svc.smtp_username = None
        email_svc.smtp_password = None
        
        with patch('services.email_service.logger') as mock_logger:
            result = email_svc._send_email(
                "test@example.com",
                "Test Subject", 
                "<h1>HTML Content</h1>",
                "Text Content"
            )
            
            assert result is False
            mock_logger.warning.assert_called_with(
                "SMTP credentials not configured, skipping email send"
            )

    def test_send_email_smtp_error(self, email_svc):
        """Test email sending with SMTP error."""
        with patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email_service.logger') as mock_logger:
            
            mock_smtp.side_effect = smtplib.SMTPException("SMTP Error")
            
            result = email_svc._send_email(
                "test@example.com",
                "Test Subject",
                "<h1>HTML Content</h1>",
                "Text Content"
            )
            
            assert result is False
            mock_logger.error.assert_called_once()

    def test_send_password_reset_email_success(self, email_svc):
        """Test successful password reset email sending."""
        mock_insert = MagicMock()
        mock_insert.execute.return_value = MagicMock()
        email_svc.supabase.table.return_value.insert.return_value = mock_insert
        
        with patch.object(email_svc, '_send_email', return_value=True) as mock_send:
            result = email_svc.send_password_reset_email(
                "user123", "test@example.com", "John Doe"
            )
            
            assert result is True
            
            # Verify token was stored in database
            email_svc.supabase.table.assert_called_with("auth_tokens")
            mock_insert.execute.assert_called_once()
            
            # Verify email was sent
            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            assert args[0] == "test@example.com"
            assert "Reset Your Cognie Password" in args[1]
            assert "John Doe" in args[2]  # HTML content
            assert "reset-password?token=" in args[2]

    def test_send_password_reset_email_db_error(self, email_svc):
        """Test password reset email with database error."""
        email_svc.supabase.table.return_value.insert.side_effect = Exception("DB Error")
        
        with patch('services.email_service.logger') as mock_logger:
            result = email_svc.send_password_reset_email(
                "user123", "test@example.com"
            )
            
            assert result is False
            mock_logger.error.assert_called_once()

    def test_send_email_verification_success(self, email_svc):
        """Test successful email verification sending."""
        mock_insert = MagicMock()
        mock_insert.execute.return_value = MagicMock()
        email_svc.supabase.table.return_value.insert.return_value = mock_insert
        
        with patch.object(email_svc, '_send_email', return_value=True) as mock_send:
            result = email_svc.send_email_verification(
                "user123", "test@example.com", "Jane Doe"
            )
            
            assert result is True
            
            # Verify token was stored in database
            email_svc.supabase.table.assert_called_with("auth_tokens")
            mock_insert.execute.assert_called_once()
            
            # Verify email was sent
            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            assert args[0] == "test@example.com"
            assert "Verify Your Cognie Email Address" in args[1]
            assert "Jane Doe" in args[2]  # HTML content
            assert "verify-email?token=" in args[2]

    def test_send_email_verification_email_send_failure(self, email_svc):
        """Test email verification with email send failure."""
        mock_insert = MagicMock()
        mock_insert.execute.return_value = MagicMock()
        email_svc.supabase.table.return_value.insert.return_value = mock_insert
        
        with patch.object(email_svc, '_send_email', return_value=False):
            result = email_svc.send_email_verification(
                "user123", "test@example.com"
            )
            
            assert result is False

    def test_verify_password_reset_token_valid(self, email_svc):
        """Test verifying valid password reset token."""
        # Create a valid token
        token = email_svc._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        # Mock database response
        mock_select = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{
            "token": token,
            "type": "password_reset",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }]
        mock_select.execute.return_value = mock_execute
        email_svc.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value = mock_select
        
        result = email_svc.verify_password_reset_token(token)
        
        assert result == "user123"

    def test_verify_password_reset_token_expired_in_db(self, email_svc):
        """Test verifying password reset token that's expired in database."""
        token = email_svc._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        # Mock database response with expired token
        mock_select = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{
            "token": token,
            "type": "password_reset",
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()  # Expired
        }]
        mock_select.execute.return_value = mock_execute
        email_svc.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value = mock_select
        
        result = email_svc.verify_password_reset_token(token)
        
        assert result is None

    def test_verify_password_reset_token_not_in_db(self, email_svc):
        """Test verifying password reset token not found in database."""
        token = email_svc._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        # Mock database response with no data
        mock_select = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = []
        mock_select.execute.return_value = mock_execute
        email_svc.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value = mock_select
        
        result = email_svc.verify_password_reset_token(token)
        
        assert result is None

    def test_verify_password_reset_token_wrong_type(self, email_svc):
        """Test verifying token with wrong type."""
        token = email_svc._create_token(
            {"user_id": "user123", "type": "email_verification"},  # Wrong type
            timedelta(hours=1)
        )
        
        result = email_svc.verify_password_reset_token(token)
        
        assert result is None

    def test_verify_email_token_valid(self, email_svc):
        """Test verifying valid email verification token."""
        token = email_svc._create_token(
            {"user_id": "user123", "type": "email_verification"},
            timedelta(days=1)
        )
        
        # Mock database response
        mock_select = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{
            "token": token,
            "type": "email_verification",
            "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat()
        }]
        mock_select.execute.return_value = mock_execute
        email_svc.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value = mock_select
        
        result = email_svc.verify_email_token(token)
        
        assert result == "user123"

    def test_verify_email_token_db_error(self, email_svc):
        """Test verifying email token with database error."""
        token = email_svc._create_token(
            {"user_id": "user123", "type": "email_verification"},
            timedelta(days=1)
        )
        
        email_svc.supabase.table.return_value.select.side_effect = Exception("DB Error")
        
        with patch('services.email_service.logger') as mock_logger:
            result = email_svc.verify_email_token(token)
            
            assert result is None
            mock_logger.error.assert_called_once()

    def test_invalidate_token_success(self, email_svc):
        """Test successful token invalidation."""
        mock_delete = MagicMock()
        mock_delete.execute.return_value = MagicMock()
        email_svc.supabase.table.return_value.delete.return_value.eq.return_value = mock_delete
        
        result = email_svc.invalidate_token("test_token")
        
        assert result is True
        email_svc.supabase.table.assert_called_with("auth_tokens")
        mock_delete.execute.assert_called_once()

    def test_invalidate_token_error(self, email_svc):
        """Test token invalidation with database error."""
        email_svc.supabase.table.return_value.delete.side_effect = Exception("DB Error")
        
        with patch('services.email_service.logger') as mock_logger:
            result = email_svc.invalidate_token("test_token")
            
            assert result is False
            mock_logger.error.assert_called_once()

    def test_cleanup_expired_tokens_success(self, email_svc):
        """Test successful cleanup of expired tokens."""
        mock_delete = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{"id": 1}, {"id": 2}, {"id": 3}]  # 3 deleted tokens
        mock_delete.execute.return_value = mock_execute
        email_svc.supabase.table.return_value.delete.return_value.lt.return_value = mock_delete
        
        with patch('services.email_service.logger') as mock_logger:
            result = email_svc.cleanup_expired_tokens()
            
            assert result == 3
            mock_logger.info.assert_called_with("Cleaned up 3 expired tokens")

    def test_cleanup_expired_tokens_no_data(self, email_svc):
        """Test cleanup when no expired tokens exist."""
        mock_delete = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = None
        mock_delete.execute.return_value = mock_execute
        email_svc.supabase.table.return_value.delete.return_value.lt.return_value = mock_delete
        
        with patch('services.email_service.logger') as mock_logger:
            result = email_svc.cleanup_expired_tokens()
            
            assert result == 0
            mock_logger.info.assert_called_with("Cleaned up 0 expired tokens")

    def test_cleanup_expired_tokens_error(self, email_svc):
        """Test cleanup with database error."""
        email_svc.supabase.table.return_value.delete.side_effect = Exception("DB Error")
        
        with patch('services.email_service.logger') as mock_logger:
            result = email_svc.cleanup_expired_tokens()
            
            assert result == 0
            mock_logger.error.assert_called_once()

    def test_html_content_generation(self, email_svc):
        """Test HTML content generation for emails."""
        mock_insert = MagicMock()
        mock_insert.execute.return_value = MagicMock()
        email_svc.supabase.table.return_value.insert.return_value = mock_insert
        
        with patch.object(email_svc, '_send_email', return_value=True) as mock_send:
            email_svc.send_password_reset_email("user123", "test@example.com", "John")
            
            # Check HTML content structure
            html_content = mock_send.call_args[0][2]
            assert "<!DOCTYPE html>" in html_content
            assert "Reset Your Cognie Password" in html_content
            assert "Hello John!" in html_content
            assert "reset-password?token=" in html_content
            assert "24 hours" in html_content

    def test_text_content_generation(self, email_svc):
        """Test text content generation for emails."""
        mock_insert = MagicMock()
        mock_insert.execute.return_value = MagicMock()
        email_svc.supabase.table.return_value.insert.return_value = mock_insert
        
        with patch.object(email_svc, '_send_email', return_value=True) as mock_send:
            email_svc.send_email_verification("user123", "test@example.com", "Jane")
            
            # Check text content structure
            text_content = mock_send.call_args[0][3]
            assert "Verify Your Cognie Email Address" in text_content
            assert "Welcome Jane!" in text_content
            assert "verify-email?token=" in text_content
            assert "7 days" in text_content


class TestGlobalEmailService:
    """Test global email service instance."""

    def test_global_email_service_exists(self):
        """Test that global email_service exists."""
        assert email_service is not None
        assert isinstance(email_service, EmailService)

    def test_global_service_configuration(self):
        """Test global service has proper configuration."""
        assert hasattr(email_service, 'smtp_server')
        assert hasattr(email_service, 'smtp_port')
        assert hasattr(email_service, 'supabase')


class TestEmailServiceIntegration:
    """Integration tests for email service."""

    @pytest.fixture
    def mock_supabase_integration(self):
        """Mock Supabase for integration tests."""
        mock_supabase = MagicMock()
        
        # Mock successful token storage
        mock_insert = MagicMock()
        mock_insert.execute.return_value = MagicMock()
        mock_supabase.table.return_value.insert.return_value = mock_insert
        
        # Mock successful token retrieval
        mock_select = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{
            "token": "test_token",
            "type": "password_reset",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }]
        mock_select.execute.return_value = mock_execute
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value = mock_select
        
        return mock_supabase

    def test_full_password_reset_flow(self, mock_supabase_integration):
        """Test complete password reset flow."""
        with patch('services.email_service.get_supabase_client', return_value=mock_supabase_integration), \
             patch('smtplib.SMTP') as mock_smtp:
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            service = EmailService()
            service.smtp_username = "test@example.com"
            service.smtp_password = "test_password"
            
            # Send password reset email
            result = service.send_password_reset_email(
                "user123", "test@example.com", "John Doe"
            )
            assert result is True
            
            # Verify email was sent
            mock_server.send_message.assert_called_once()
            
            # Get the token from the database call
            insert_call = mock_supabase_integration.table.return_value.insert.call_args[0][0]
            token = insert_call["token"]
            
            # Verify the token
            user_id = service.verify_password_reset_token(token)
            assert user_id == "user123"
            
            # Invalidate the token
            invalidate_result = service.invalidate_token(token)
            assert invalidate_result is True

    def test_email_verification_flow(self, mock_supabase_integration):
        """Test complete email verification flow."""
        with patch('services.email_service.get_supabase_client', return_value=mock_supabase_integration), \
             patch('smtplib.SMTP') as mock_smtp:
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            service = EmailService()
            service.smtp_username = "test@example.com"
            service.smtp_password = "test_password"
            
            # Mock email verification token in database
            mock_execute = MagicMock()
            mock_execute.data = [{
                "token": "test_token",
                "type": "email_verification",
                "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat()
            }]
            mock_supabase_integration.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_execute
            
            # Send verification email
            result = service.send_email_verification(
                "user123", "test@example.com", "Jane Doe"
            )
            assert result is True
            
            # Verify email was sent
            mock_server.send_message.assert_called_once()
            
            # Create and verify token
            token = service._create_token(
                {"user_id": "user123", "type": "email_verification"},
                timedelta(days=1)
            )
            
            user_id = service.verify_email_token(token)
            assert user_id == "user123"