import pytest
import smtplib
from unittest.mock import MagicMock, patch, Mock
from email.mime.multipart import MIMEMultipart

from services.email import send_password_reset_email


class TestEmailService:
    """Test basic email service functionality."""

    def test_send_password_reset_email_success(self):
        """Test successful password reset email sending."""
        with patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email.logger') as mock_logger:
            
            # Mock SMTP server
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            # Test email sending
            to_email = "test@example.com"
            reset_link = "https://your-frontend-domain.com/reset?token=abc123"
            
            send_password_reset_email(to_email, reset_link)
            
            # Verify SMTP was called correctly
            mock_smtp.assert_called_once_with("localhost", 1025)
            mock_server.sendmail.assert_called_once()
            
            # Verify logging
            mock_logger.info.assert_called_once_with(f"Password reset email sent to {to_email}")

    def test_send_password_reset_email_with_auth(self):
        """Test password reset email with SMTP authentication."""
        env_vars = {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@gmail.com",
            "SMTP_PASS": "password123",
            "FROM_EMAIL": "noreply@company.com"
        }
        
        with patch.dict('os.environ', env_vars), \
             patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email.logger') as mock_logger:
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            send_password_reset_email("test@example.com", "http://test.com/reset")
            
            # Verify SMTP configuration
            mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
            
            # Verify authentication was used
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("user@gmail.com", "password123")
            
            # Verify email was sent
            mock_server.sendmail.assert_called_once()
            
            # Check sendmail arguments
            call_args = mock_server.sendmail.call_args[0]
            assert call_args[0] == "noreply@company.com"  # from_email
            assert call_args[1] == "test@example.com"  # to_email
            assert isinstance(call_args[2], str)  # message

    def test_send_password_reset_email_no_auth(self):
        """Test password reset email without SMTP authentication."""
        env_vars = {
            "SMTP_HOST": "localhost",
            "SMTP_PORT": "1025",
            "SMTP_USER": "",
            "SMTP_PASS": "",
            "FROM_EMAIL": "test@localhost"
        }
        
        with patch.dict('os.environ', env_vars), \
             patch('smtplib.SMTP') as mock_smtp:
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            send_password_reset_email("test@example.com", "http://localhost:3000/reset")
            
            # Verify no authentication was attempted
            mock_server.starttls.assert_not_called()
            mock_server.login.assert_not_called()
            
            # Verify email was still sent
            mock_server.sendmail.assert_called_once()

    def test_send_password_reset_email_link_replacement(self):
        """Test that reset link is properly replaced."""
        with patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email.logger'):
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            # Use the original domain that should be replaced
            original_link = "https://your-frontend-domain.com/reset?token=abc123"
            
            send_password_reset_email("test@example.com", original_link)
            
            # Get the message that was sent
            call_args = mock_server.sendmail.call_args[0]
            message_content = call_args[2]
            
            # Verify the link was replaced
            assert "http://localhost:3000" in message_content
            assert "https://your-frontend-domain.com" not in message_content

    def test_send_password_reset_email_html_content(self):
        """Test that email contains proper HTML content."""
        with patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email.logger'):
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            reset_link = "http://localhost:3000/reset?token=test123"
            
            send_password_reset_email("test@example.com", reset_link)
            
            # Get the message that was sent
            call_args = mock_server.sendmail.call_args[0]
            message_content = call_args[2]
            
            # Verify HTML content
            assert "Password Reset Request" in message_content
            assert "You requested a password reset" in message_content
            assert reset_link in message_content
            assert "Reset Password" in message_content
            assert "ignore this email" in message_content

    def test_send_password_reset_email_smtp_error(self):
        """Test handling of SMTP errors."""
        with patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email.logger') as mock_logger:
            
            # Mock SMTP to raise an exception
            mock_smtp.side_effect = smtplib.SMTPException("SMTP server error")
            
            # Should not raise exception, just log error
            send_password_reset_email("test@example.com", "http://test.com/reset")
            
            # Verify error was logged
            mock_logger.error.assert_called_once()
            error_message = mock_logger.error.call_args[0][0]
            assert "Failed to send email to test@example.com" in error_message
            assert "SMTP server error" in error_message

    def test_send_password_reset_email_connection_error(self):
        """Test handling of connection errors."""
        with patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email.logger') as mock_logger:
            
            # Mock connection error
            mock_smtp.side_effect = ConnectionRefusedError("Connection refused")
            
            send_password_reset_email("test@example.com", "http://test.com/reset")
            
            # Verify error was logged and function didn't crash
            mock_logger.error.assert_called_once()

    def test_send_password_reset_email_auth_error(self):
        """Test handling of authentication errors."""
        env_vars = {
            "SMTP_USER": "user@gmail.com",
            "SMTP_PASS": "wrongpassword"
        }
        
        with patch.dict('os.environ', env_vars), \
             patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email.logger') as mock_logger:
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            # Mock authentication failure
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
            
            send_password_reset_email("test@example.com", "http://test.com/reset")
            
            # Verify error was logged
            mock_logger.error.assert_called_once()

    def test_send_password_reset_email_default_config(self):
        """Test email sending with default configuration."""
        # Clear environment variables to test defaults
        with patch.dict('os.environ', {}, clear=True), \
             patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email.logger'):
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            send_password_reset_email("test@example.com", "http://test.com/reset")
            
            # Verify default configuration was used
            mock_smtp.assert_called_once_with("localhost", 1025)
            
            # Verify default from_email
            call_args = mock_server.sendmail.call_args[0]
            assert call_args[0] == "no-reply@example.com"

    def test_send_password_reset_email_message_structure(self):
        """Test that email message has proper MIME structure."""
        with patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email.logger'):
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            to_email = "recipient@example.com"
            reset_link = "http://localhost:3000/reset?token=test"
            
            send_password_reset_email(to_email, reset_link)
            
            # Get the message
            call_args = mock_server.sendmail.call_args[0]
            message_content = call_args[2]
            
            # Verify MIME headers are present
            assert "From:" in message_content
            assert "To:" in message_content
            assert "Subject:" in message_content
            assert "Content-Type:" in message_content
            assert to_email in message_content

    def test_send_password_reset_email_port_conversion(self):
        """Test that SMTP_PORT environment variable is properly converted to int."""
        env_vars = {
            "SMTP_PORT": "465"  # String value
        }
        
        with patch.dict('os.environ', env_vars), \
             patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email.logger'):
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            send_password_reset_email("test@example.com", "http://test.com/reset")
            
            # Verify port was converted to integer
            mock_smtp.assert_called_once_with("localhost", 465)

    def test_send_password_reset_email_special_characters(self):
        """Test email sending with special characters in email and link."""
        with patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email.logger') as mock_logger:
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            # Email with special characters
            special_email = "test+user@example.com"
            special_link = "http://localhost:3000/reset?token=abc123&user=test%40example.com"
            
            send_password_reset_email(special_email, special_link)
            
            # Verify it was processed without errors
            mock_server.sendmail.assert_called_once()
            mock_logger.info.assert_called_once_with(f"Password reset email sent to {special_email}")


class TestEmailServiceIntegration:
    """Integration tests for email service."""

    def test_email_service_logging_integration(self):
        """Test that logging is properly integrated."""
        import logging
        
        # Verify logger exists and is configured
        logger = logging.getLogger('services.email')
        assert logger is not None
        
        # Test that logger name is correct
        from services.email import logger as email_logger
        assert email_logger.name == 'services.email'

    def test_email_service_environment_integration(self):
        """Test integration with environment variables."""
        import os
        
        # Test that os.getenv is used correctly
        test_vars = {
            "SMTP_HOST": "test.smtp.com",
            "SMTP_PORT": "2525",
            "SMTP_USER": "testuser",
            "SMTP_PASS": "testpass",
            "FROM_EMAIL": "test@company.com"
        }
        
        with patch.dict('os.environ', test_vars), \
             patch('smtplib.SMTP') as mock_smtp, \
             patch('services.email.logger'):
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            send_password_reset_email("test@example.com", "http://test.com/reset")
            
            # Verify all environment variables were used
            mock_smtp.assert_called_once_with("test.smtp.com", 2525)
            mock_server.login.assert_called_once_with("testuser", "testpass")
            
            # Check from_email in sendmail call
            call_args = mock_server.sendmail.call_args[0]
            assert call_args[0] == "test@company.com"