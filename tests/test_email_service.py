import pytest
import os
import smtplib
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, Mock
from email.mime.multipart import MIMEMultipart

import jwt

from services.email_service import EmailService, email_service


class TestEmailService:
    """Test EmailService functionality."""

    @pytest.fixture
    def email_service_instance(self):
        """Create an EmailService instance for testing."""
        with patch.dict(os.environ, {
            'SMTP_SERVER': 'test.smtp.com',
            'SMTP_PORT': '587',
            'SMTP_USERNAME': 'test@example.com',
            'SMTP_PASSWORD': 'test_password',
            'FROM_EMAIL': 'noreply@test.com',
            'APP_NAME': 'TestApp',
            'APP_URL': 'https://test.app',
            'JWT_SECRET': 'test-secret-key'
        }):
            return EmailService()

    @pytest.fixture
    def mock_supabase(self):
        """Mock supabase client for testing."""
        with patch('services.email_service.get_supabase_client') as mock_client:
            mock_supabase = MagicMock()
            mock_client.return_value = mock_supabase
            yield mock_supabase

    def test_email_service_initialization(self, email_service_instance):
        """Test EmailService initialization."""
        assert email_service_instance.smtp_server == 'test.smtp.com'
        assert email_service_instance.smtp_port == 587
        assert email_service_instance.smtp_username == 'test@example.com'
        assert email_service_instance.smtp_password == 'test_password'
        assert email_service_instance.from_email == 'noreply@test.com'
        assert email_service_instance.app_name == 'TestApp'
        assert email_service_instance.app_url == 'https://test.app'
        assert email_service_instance.jwt_secret == 'test-secret-key'

    def test_email_service_default_values(self):
        """Test EmailService with default environment values."""
        with patch.dict(os.environ, {}, clear=True):
            service = EmailService()
            assert service.smtp_server == 'smtp.gmail.com'
            assert service.smtp_port == 587
            assert service.from_email == 'noreply@cognie.app'
            assert service.app_name == 'Cognie'
            assert service.app_url == 'https://cognie.app'
            assert service.jwt_secret == 'your-secret-key'

    def test_email_service_expiry_times(self, email_service_instance):
        """Test that expiry times are set correctly."""
        assert email_service_instance.password_reset_expiry == timedelta(hours=24)
        assert email_service_instance.email_verification_expiry == timedelta(days=7)

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

    def test_create_token_with_different_payloads(self, email_service_instance):
        """Test JWT token creation with different payloads."""
        payloads = [
            {"user_id": "456", "type": "email_verification"},
            {"user_id": "789", "type": "password_reset", "extra": "data"},
            {"user_id": "abc", "type": "custom", "nested": {"key": "value"}}
        ]
        
        for payload in payloads:
            token = email_service_instance._create_token(payload, timedelta(hours=1))
            decoded = jwt.decode(token, email_service_instance.jwt_secret, algorithms=["HS256"])
            
            for key, value in payload.items():
                assert decoded[key] == value

    def test_verify_token_valid(self, email_service_instance):
        """Test verifying valid JWT token."""
        payload = {"user_id": "123", "type": "password_reset"}
        token = email_service_instance._create_token(payload, timedelta(hours=1))
        
        result = email_service_instance._verify_token(token)
        
        assert result is not None
        assert result["user_id"] == "123"
        assert result["type"] == "password_reset"

    def test_verify_token_expired(self, email_service_instance):
        """Test verifying expired JWT token."""
        payload = {"user_id": "123", "type": "password_reset"}
        token = email_service_instance._create_token(payload, timedelta(seconds=-1))
        
        result = email_service_instance._verify_token(token)
        
        assert result is None

    def test_verify_token_invalid(self, email_service_instance):
        """Test verifying invalid JWT token."""
        invalid_token = "invalid.token.here"
        
        result = email_service_instance._verify_token(invalid_token)
        
        assert result is None

    def test_verify_token_wrong_secret(self, email_service_instance):
        """Test verifying token with wrong secret."""
        # Create token with different secret
        payload = {"user_id": "123", "type": "password_reset"}
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        
        result = email_service_instance._verify_token(token)
        
        assert result is None

    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, email_service_instance):
        """Test successful email sending."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_service_instance._send_email(
            "test@example.com",
            "Test Subject",
            "<h1>HTML Content</h1>",
            "Text Content"
        )
        
        assert result is True
        mock_smtp.assert_called_once_with('test.smtp.com', 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@example.com', 'test_password')
        mock_server.send_message.assert_called_once()

    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_no_credentials(self, mock_smtp, email_service_instance):
        """Test email sending without SMTP credentials."""
        email_service_instance.smtp_username = None
        email_service_instance.smtp_password = None
        
        result = email_service_instance._send_email(
            "test@example.com",
            "Test Subject",
            "<h1>HTML Content</h1>",
            "Text Content"
        )
        
        assert result is False
        mock_smtp.assert_not_called()

    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_smtp_error(self, mock_smtp, email_service_instance):
        """Test email sending with SMTP error."""
        mock_smtp.side_effect = smtplib.SMTPException("SMTP Error")
        
        result = email_service_instance._send_email(
            "test@example.com",
            "Test Subject",
            "<h1>HTML Content</h1>",
            "Text Content"
        )
        
        assert result is False

    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_connection_error(self, mock_smtp, email_service_instance):
        """Test email sending with connection error."""
        mock_smtp.side_effect = ConnectionError("Connection failed")
        
        result = email_service_instance._send_email(
            "test@example.com",
            "Test Subject",
            "<h1>HTML Content</h1>",
            "Text Content"
        )
        
        assert result is False

    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_message_structure(self, mock_smtp, email_service_instance):
        """Test that email message has correct structure."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        email_service_instance._send_email(
            "test@example.com",
            "Test Subject",
            "<h1>HTML Content</h1>",
            "Text Content"
        )
        
        # Check that send_message was called with a MIMEMultipart message
        call_args = mock_server.send_message.call_args
        message = call_args[0][0]
        
        assert message["Subject"] == "Test Subject"
        assert message["From"] == "noreply@test.com"
        assert message["To"] == "test@example.com"

    def test_send_password_reset_email_success(self, email_service_instance, mock_supabase):
        """Test successful password reset email sending."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        with patch.object(email_service_instance, '_send_email', return_value=True) as mock_send:
            result = email_service_instance.send_password_reset_email(
                "user123", "test@example.com", "John Doe"
            )
            
            assert result is True
            mock_send.assert_called_once()
            mock_supabase.table.assert_called_with("auth_tokens")

    def test_send_password_reset_email_content(self, email_service_instance, mock_supabase):
        """Test password reset email content."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        with patch.object(email_service_instance, '_send_email', return_value=True) as mock_send:
            email_service_instance.send_password_reset_email(
                "user123", "test@example.com", "John Doe"
            )
            
            call_args = mock_send.call_args
            subject = call_args[0][1]
            html_content = call_args[0][2]
            text_content = call_args[0][3]
            
            assert "Reset Your TestApp Password" in subject
            assert "John Doe" in html_content
            assert "John Doe" in text_content
            assert "reset-password?token=" in html_content
            assert "reset-password?token=" in text_content

    def test_send_password_reset_email_no_name(self, email_service_instance, mock_supabase):
        """Test password reset email without user name."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        with patch.object(email_service_instance, '_send_email', return_value=True) as mock_send:
            email_service_instance.send_password_reset_email(
                "user123", "test@example.com"
            )
            
            call_args = mock_send.call_args
            html_content = call_args[0][2]
            text_content = call_args[0][3]
            
            assert "Hello!" in html_content
            assert "Hello!" in text_content

    def test_send_password_reset_email_database_error(self, email_service_instance, mock_supabase):
        """Test password reset email with database error."""
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("DB Error")
        
        result = email_service_instance.send_password_reset_email(
            "user123", "test@example.com", "John Doe"
        )
        
        assert result is False

    def test_send_password_reset_email_send_failure(self, email_service_instance, mock_supabase):
        """Test password reset email with send failure."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        with patch.object(email_service_instance, '_send_email', return_value=False):
            result = email_service_instance.send_password_reset_email(
                "user123", "test@example.com", "John Doe"
            )
            
            assert result is False

    def test_send_email_verification_success(self, email_service_instance, mock_supabase):
        """Test successful email verification sending."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        with patch.object(email_service_instance, '_send_email', return_value=True) as mock_send:
            result = email_service_instance.send_email_verification(
                "user123", "test@example.com", "Jane Doe"
            )
            
            assert result is True
            mock_send.assert_called_once()
            mock_supabase.table.assert_called_with("auth_tokens")

    def test_send_email_verification_content(self, email_service_instance, mock_supabase):
        """Test email verification content."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        with patch.object(email_service_instance, '_send_email', return_value=True) as mock_send:
            email_service_instance.send_email_verification(
                "user123", "test@example.com", "Jane Doe"
            )
            
            call_args = mock_send.call_args
            subject = call_args[0][1]
            html_content = call_args[0][2]
            text_content = call_args[0][3]
            
            assert "Verify Your TestApp Email Address" in subject
            assert "Jane Doe" in html_content
            assert "Jane Doe" in text_content
            assert "verify-email?token=" in html_content
            assert "verify-email?token=" in text_content

    def test_send_email_verification_no_name(self, email_service_instance, mock_supabase):
        """Test email verification without user name."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        with patch.object(email_service_instance, '_send_email', return_value=True) as mock_send:
            email_service_instance.send_email_verification(
                "user123", "test@example.com"
            )
            
            call_args = mock_send.call_args
            html_content = call_args[0][2]
            text_content = call_args[0][3]
            
            assert "Welcome!" in html_content
            assert "Welcome!" in text_content

    def test_send_email_verification_database_error(self, email_service_instance, mock_supabase):
        """Test email verification with database error."""
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("DB Error")
        
        result = email_service_instance.send_email_verification(
            "user123", "test@example.com", "Jane Doe"
        )
        
        assert result is False

    def test_verify_password_reset_token_valid(self, email_service_instance, mock_supabase):
        """Test verifying valid password reset token."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        # Mock database response
        mock_result = MagicMock()
        mock_result.data = [{
            "token": token,
            "type": "password_reset",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        
        result = email_service_instance.verify_password_reset_token(token)
        
        assert result == "user123"

    def test_verify_password_reset_token_expired(self, email_service_instance, mock_supabase):
        """Test verifying expired password reset token."""
        # Create an expired token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(seconds=-1)
        )
        
        result = email_service_instance.verify_password_reset_token(token)
        
        assert result is None

    def test_verify_password_reset_token_wrong_type(self, email_service_instance, mock_supabase):
        """Test verifying token with wrong type."""
        # Create token with wrong type
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "email_verification"},
            timedelta(hours=1)
        )
        
        result = email_service_instance.verify_password_reset_token(token)
        
        assert result is None

    def test_verify_password_reset_token_not_in_database(self, email_service_instance, mock_supabase):
        """Test verifying token not in database."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        # Mock empty database response
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        
        result = email_service_instance.verify_password_reset_token(token)
        
        assert result is None

    def test_verify_password_reset_token_database_expired(self, email_service_instance, mock_supabase):
        """Test verifying token that's expired in database."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        # Mock database response with expired token
        mock_result = MagicMock()
        mock_result.data = [{
            "token": token,
            "type": "password_reset",
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        
        result = email_service_instance.verify_password_reset_token(token)
        
        assert result is None

    def test_verify_password_reset_token_database_error(self, email_service_instance, mock_supabase):
        """Test verifying token with database error."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        # Mock database error
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB Error")
        
        result = email_service_instance.verify_password_reset_token(token)
        
        assert result is None

    def test_verify_email_token_valid(self, email_service_instance, mock_supabase):
        """Test verifying valid email verification token."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "email_verification"},
            timedelta(days=1)
        )
        
        # Mock database response
        mock_result = MagicMock()
        mock_result.data = [{
            "token": token,
            "type": "email_verification",
            "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        
        result = email_service_instance.verify_email_token(token)
        
        assert result == "user123"

    def test_verify_email_token_wrong_type(self, email_service_instance, mock_supabase):
        """Test verifying email token with wrong type."""
        # Create token with wrong type
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "password_reset"},
            timedelta(hours=1)
        )
        
        result = email_service_instance.verify_email_token(token)
        
        assert result is None

    def test_verify_email_token_expired(self, email_service_instance, mock_supabase):
        """Test verifying expired email token."""
        # Create an expired token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "email_verification"},
            timedelta(seconds=-1)
        )
        
        result = email_service_instance.verify_email_token(token)
        
        assert result is None

    def test_verify_email_token_database_error(self, email_service_instance, mock_supabase):
        """Test verifying email token with database error."""
        # Create a valid token
        token = email_service_instance._create_token(
            {"user_id": "user123", "type": "email_verification"},
            timedelta(days=1)
        )
        
        # Mock database error
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB Error")
        
        result = email_service_instance.verify_email_token(token)
        
        assert result is None

    def test_invalidate_token_success(self, email_service_instance, mock_supabase):
        """Test successful token invalidation."""
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()
        
        result = email_service_instance.invalidate_token("test_token")
        
        assert result is True
        mock_supabase.table.assert_called_with("auth_tokens")

    def test_invalidate_token_database_error(self, email_service_instance, mock_supabase):
        """Test token invalidation with database error."""
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.side_effect = Exception("DB Error")
        
        result = email_service_instance.invalidate_token("test_token")
        
        assert result is False

    def test_cleanup_expired_tokens_success(self, email_service_instance, mock_supabase):
        """Test successful cleanup of expired tokens."""
        mock_result = MagicMock()
        mock_result.data = [{"id": 1}, {"id": 2}, {"id": 3}]
        mock_supabase.table.return_value.delete.return_value.lt.return_value.execute.return_value = mock_result
        
        result = email_service_instance.cleanup_expired_tokens()
        
        assert result == 3
        mock_supabase.table.assert_called_with("auth_tokens")

    def test_cleanup_expired_tokens_no_data(self, email_service_instance, mock_supabase):
        """Test cleanup with no expired tokens."""
        mock_result = MagicMock()
        mock_result.data = None
        mock_supabase.table.return_value.delete.return_value.lt.return_value.execute.return_value = mock_result
        
        result = email_service_instance.cleanup_expired_tokens()
        
        assert result == 0

    def test_cleanup_expired_tokens_database_error(self, email_service_instance, mock_supabase):
        """Test cleanup with database error."""
        mock_supabase.table.return_value.delete.return_value.lt.return_value.execute.side_effect = Exception("DB Error")
        
        result = email_service_instance.cleanup_expired_tokens()
        
        assert result == 0


class TestEmailServiceIntegration:
    """Integration tests for EmailService."""

    def test_global_email_service_instance(self):
        """Test that global email_service instance exists."""
        assert email_service is not None
        assert isinstance(email_service, EmailService)

    def test_password_reset_workflow(self, mock_supabase):
        """Test complete password reset workflow."""
        with patch.dict(os.environ, {
            'SMTP_USERNAME': 'test@example.com',
            'SMTP_PASSWORD': 'test_password',
            'JWT_SECRET': 'test-secret'
        }):
            service = EmailService()
            
            # Mock database operations
            mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
            mock_result = MagicMock()
            mock_result.data = [{
                "token": "test_token",
                "type": "password_reset",
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
            }]
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
            
            # Mock email sending
            with patch.object(service, '_send_email', return_value=True):
                # Send password reset email
                result = service.send_password_reset_email("user123", "test@example.com")
                assert result is True
                
                # Get the token from the database call
                insert_call = mock_supabase.table.return_value.insert.call_args
                token_data = insert_call[0][0]
                token = token_data["token"]
                
                # Verify the token
                user_id = service.verify_password_reset_token(token)
                assert user_id == "user123"
                
                # Invalidate the token
                invalidate_result = service.invalidate_token(token)
                assert invalidate_result is True

    def test_email_verification_workflow(self, mock_supabase):
        """Test complete email verification workflow."""
        with patch.dict(os.environ, {
            'SMTP_USERNAME': 'test@example.com',
            'SMTP_PASSWORD': 'test_password',
            'JWT_SECRET': 'test-secret'
        }):
            service = EmailService()
            
            # Mock database operations
            mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
            mock_result = MagicMock()
            mock_result.data = [{
                "token": "test_token",
                "type": "email_verification",
                "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
            }]
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
            
            # Mock email sending
            with patch.object(service, '_send_email', return_value=True):
                # Send email verification
                result = service.send_email_verification("user123", "test@example.com")
                assert result is True
                
                # Get the token from the database call
                insert_call = mock_supabase.table.return_value.insert.call_args
                token_data = insert_call[0][0]
                token = token_data["token"]
                
                # Verify the token
                user_id = service.verify_email_token(token)
                assert user_id == "user123"

    def test_token_expiry_consistency(self):
        """Test that token expiry times are consistent."""
        with patch.dict(os.environ, {'JWT_SECRET': 'test-secret'}):
            service = EmailService()
            
            # Create tokens with different expiry times
            reset_token = service._create_token(
                {"user_id": "user123", "type": "password_reset"},
                service.password_reset_expiry
            )
            
            verify_token = service._create_token(
                {"user_id": "user123", "type": "email_verification"},
                service.email_verification_expiry
            )
            
            # Decode and check expiry times
            reset_decoded = jwt.decode(reset_token, service.jwt_secret, algorithms=["HS256"])
            verify_decoded = jwt.decode(verify_token, service.jwt_secret, algorithms=["HS256"])
            
            # Password reset should expire in 24 hours
            reset_exp = datetime.fromtimestamp(reset_decoded["exp"])
            reset_iat = datetime.fromtimestamp(reset_decoded["iat"])
            assert (reset_exp - reset_iat).total_seconds() == 24 * 3600
            
            # Email verification should expire in 7 days
            verify_exp = datetime.fromtimestamp(verify_decoded["exp"])
            verify_iat = datetime.fromtimestamp(verify_decoded["iat"])
            assert (verify_exp - verify_iat).total_seconds() == 7 * 24 * 3600


class TestEmailServiceEdgeCases:
    """Test edge cases for EmailService."""

    def test_email_service_missing_user_id_in_token(self):
        """Test token verification with missing user_id."""
        with patch.dict(os.environ, {'JWT_SECRET': 'test-secret'}):
            service = EmailService()
            
            # Create token without user_id
            token = service._create_token(
                {"type": "password_reset"},
                timedelta(hours=1)
            )
            
            result = service.verify_password_reset_token(token)
            assert result is None

    def test_email_service_malformed_expires_at(self, mock_supabase):
        """Test token verification with malformed expires_at."""
        with patch.dict(os.environ, {'JWT_SECRET': 'test-secret'}):
            service = EmailService()
            
            token = service._create_token(
                {"user_id": "user123", "type": "password_reset"},
                timedelta(hours=1)
            )
            
            # Mock database response with malformed expires_at
            mock_result = MagicMock()
            mock_result.data = [{
                "token": token,
                "type": "password_reset",
                "expires_at": "invalid-date-format"
            }]
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
            
            result = service.verify_password_reset_token(token)
            assert result is None

    def test_email_service_empty_token(self):
        """Test token verification with empty token."""
        with patch.dict(os.environ, {'JWT_SECRET': 'test-secret'}):
            service = EmailService()
            
            result = service.verify_password_reset_token("")
            assert result is None
            
            result = service.verify_email_token("")
            assert result is None

    def test_email_service_none_token(self):
        """Test token verification with None token."""
        with patch.dict(os.environ, {'JWT_SECRET': 'test-secret'}):
            service = EmailService()
            
            result = service.verify_password_reset_token(None)  # type: ignore
            assert result is None
            
            result = service.verify_email_token(None)  # type: ignore
            assert result is None

    def test_email_service_empty_email_address(self, mock_supabase):
        """Test sending email with empty email address."""
        with patch.dict(os.environ, {
            'SMTP_USERNAME': 'test@example.com',
            'SMTP_PASSWORD': 'test_password'
        }):
            service = EmailService()
            
            mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
            
            with patch.object(service, '_send_email', return_value=False):
                result = service.send_password_reset_email("user123", "")
                assert result is False

    def test_email_service_very_long_user_name(self, mock_supabase):
        """Test sending email with very long user name."""
        with patch.dict(os.environ, {
            'SMTP_USERNAME': 'test@example.com',
            'SMTP_PASSWORD': 'test_password'
        }):
            service = EmailService()
            
            mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
            
            long_name = "A" * 1000
            
            with patch.object(service, '_send_email', return_value=True) as mock_send:
                result = service.send_password_reset_email("user123", "test@example.com", long_name)
                assert result is True
                
                # Check that the long name is included in the email
                call_args = mock_send.call_args
                html_content = call_args[0][2]
                assert long_name in html_content