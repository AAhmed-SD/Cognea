import smtplib
from unittest.mock import MagicMock, patch

from services.email import send_password_reset_email


class TestSendPasswordResetEmail:
    """Test the send_password_reset_email function"""

    @patch('services.email.smtplib.SMTP')
    @patch('services.email.os.getenv')
    def test_send_password_reset_email_success(self, mock_getenv, mock_smtp):
        """Test successful password reset email sending"""
        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "test@example.com",
            "SMTP_PASS": "password123",
            "FROM_EMAIL": "noreply@example.com"
        }.get(key, default)

        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Test the function
        to_email = "user@example.com"
        reset_link = "https://your-frontend-domain.com/reset?token=abc123"

        send_password_reset_email(to_email, reset_link)

        # Verify SMTP was called correctly
        mock_smtp.assert_called_once_with("smtp.example.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "password123")
        mock_server.sendmail.assert_called_once()

        # Verify the reset link was modified
        call_args = mock_server.sendmail.call_args
        assert "http://localhost:3000/reset?token=abc123" in call_args[0][2]

    @patch('services.email.smtplib.SMTP')
    @patch('services.email.os.getenv')
    def test_send_password_reset_email_no_auth(self, mock_getenv, mock_smtp):
        """Test password reset email sending without authentication"""
        # Mock environment variables (no auth)
        mock_getenv.side_effect = lambda key, default=None: {
            "SMTP_HOST": "localhost",
            "SMTP_PORT": "1025",
            "SMTP_USER": "",
            "SMTP_PASS": "",
            "FROM_EMAIL": "no-reply@example.com"
        }.get(key, default)

        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Test the function
        to_email = "user@example.com"
        reset_link = "https://your-frontend-domain.com/reset?token=abc123"

        send_password_reset_email(to_email, reset_link)

        # Verify SMTP was called correctly (no auth)
        mock_smtp.assert_called_once_with("localhost", 1025)
        mock_server.starttls.assert_not_called()
        mock_server.login.assert_not_called()
        mock_server.sendmail.assert_called_once()

    @patch('services.email.smtplib.SMTP')
    @patch('services.email.os.getenv')
    def test_send_password_reset_email_custom_port(self, mock_getenv, mock_smtp):
        """Test password reset email sending with custom port"""
        # Mock environment variables with custom port
        mock_getenv.side_effect = lambda key, default=None: {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "465",
            "SMTP_USER": "test@gmail.com",
            "SMTP_PASS": "password123",
            "FROM_EMAIL": "test@gmail.com"
        }.get(key, default)

        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Test the function
        to_email = "user@example.com"
        reset_link = "https://your-frontend-domain.com/reset?token=abc123"

        send_password_reset_email(to_email, reset_link)

        # Verify SMTP was called with custom port
        mock_smtp.assert_called_once_with("smtp.gmail.com", 465)

    @patch('services.email.smtplib.SMTP')
    @patch('services.email.os.getenv')
    def test_send_password_reset_email_link_replacement(self, mock_getenv, mock_smtp):
        """Test that the reset link is properly replaced"""
        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "SMTP_HOST": "localhost",
            "SMTP_PORT": "1025",
            "SMTP_USER": "",
            "SMTP_PASS": "",
            "FROM_EMAIL": "no-reply@example.com"
        }.get(key, default)

        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Test with different link formats
        test_cases = [
            "https://your-frontend-domain.com/reset?token=abc123",
            "https://your-frontend-domain.com/password-reset?token=xyz789",
            "https://your-frontend-domain.com/",
            "https://your-frontend-domain.com"
        ]

        for reset_link in test_cases:
            mock_server.sendmail.reset_mock()
            send_password_reset_email("user@example.com", reset_link)

            # Verify the link was replaced
            call_args = mock_server.sendmail.call_args
            email_content = call_args[0][2]
            assert "http://localhost:3000" in email_content
            assert "https://your-frontend-domain.com" not in email_content

    @patch('services.email.smtplib.SMTP')
    @patch('services.email.os.getenv')
    def test_send_password_reset_email_smtp_error(self, mock_getenv, mock_smtp):
        """Test handling of SMTP errors"""
        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "SMTP_HOST": "localhost",
            "SMTP_PORT": "1025",
            "SMTP_USER": "",
            "SMTP_PASS": "",
            "FROM_EMAIL": "no-reply@example.com"
        }.get(key, default)

        # Mock SMTP to raise an exception
        mock_smtp.side_effect = smtplib.SMTPException("SMTP server error")

        # Test the function - should not raise exception
        to_email = "user@example.com"
        reset_link = "https://your-frontend-domain.com/reset?token=abc123"

        # Should not raise an exception
        send_password_reset_email(to_email, reset_link)

    @patch('services.email.smtplib.SMTP')
    @patch('services.email.os.getenv')
    def test_send_password_reset_email_connection_error(self, mock_getenv, mock_smtp):
        """Test handling of connection errors"""
        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "SMTP_HOST": "localhost",
            "SMTP_PORT": "1025",
            "SMTP_USER": "",
            "SMTP_PASS": "",
            "FROM_EMAIL": "no-reply@example.com"
        }.get(key, default)

        # Mock SMTP to raise a connection error
        mock_smtp.side_effect = ConnectionError("Connection failed")

        # Test the function - should not raise exception
        to_email = "user@example.com"
        reset_link = "https://your-frontend-domain.com/reset?token=abc123"

        # Should not raise an exception
        send_password_reset_email(to_email, reset_link)

    @patch('services.email.smtplib.SMTP')
    @patch('services.email.os.getenv')
    def test_send_password_reset_email_auth_error(self, mock_getenv, mock_smtp):
        """Test handling of authentication errors"""
        # Mock environment variables with auth
        mock_getenv.side_effect = lambda key, default=None: {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "test@example.com",
            "SMTP_PASS": "wrongpassword",
            "FROM_EMAIL": "noreply@example.com"
        }.get(key, default)

        # Mock SMTP server that fails on login
        mock_server = MagicMock()
        mock_server.starttls.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Test the function - should not raise exception
        to_email = "user@example.com"
        reset_link = "https://your-frontend-domain.com/reset?token=abc123"

        # Should not raise an exception
        send_password_reset_email(to_email, reset_link)

    @patch('services.email.smtplib.SMTP')
    @patch('services.email.os.getenv')
    def test_send_password_reset_email_empty_credentials(self, mock_getenv, mock_smtp):
        """Test with empty SMTP credentials"""
        # Mock environment variables with empty auth
        mock_getenv.side_effect = lambda key, default=None: {
            "SMTP_HOST": "localhost",
            "SMTP_PORT": "1025",
            "SMTP_USER": "",
            "SMTP_PASS": "",
            "FROM_EMAIL": "no-reply@example.com"
        }.get(key, default)

        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Test the function
        to_email = "user@example.com"
        reset_link = "https://your-frontend-domain.com/reset?token=abc123"

        send_password_reset_email(to_email, reset_link)

        # Verify no auth was attempted
        mock_server.starttls.assert_not_called()
        mock_server.login.assert_not_called()

    @patch('services.email.smtplib.SMTP')
    @patch('services.email.os.getenv')
    def test_send_password_reset_email_email_content(self, mock_getenv, mock_smtp):
        """Test that email content is properly formatted"""
        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "SMTP_HOST": "localhost",
            "SMTP_PORT": "1025",
            "SMTP_USER": "",
            "SMTP_PASS": "",
            "FROM_EMAIL": "no-reply@example.com"
        }.get(key, default)

        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Test the function
        to_email = "user@example.com"
        reset_link = "https://your-frontend-domain.com/reset?token=abc123"

        send_password_reset_email(to_email, reset_link)

        # Verify email content
        call_args = mock_server.sendmail.call_args
        email_content = call_args[0][2]

        # Check that email contains expected content
        assert "Password Reset Request" in email_content
        assert "You requested a password reset" in email_content
        assert "Reset Password" in email_content
        assert "If you did not request this" in email_content
        assert "http://localhost:3000/reset?token=abc123" in email_content

    @patch('services.email.smtplib.SMTP')
    @patch('services.email.os.getenv')
    def test_send_password_reset_email_headers(self, mock_getenv, mock_smtp):
        """Test that email headers are properly set"""
        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "SMTP_HOST": "localhost",
            "SMTP_PORT": "1025",
            "SMTP_USER": "",
            "SMTP_PASS": "",
            "FROM_EMAIL": "no-reply@example.com"
        }.get(key, default)

        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Test the function
        to_email = "user@example.com"
        reset_link = "https://your-frontend-domain.com/reset?token=abc123"

        send_password_reset_email(to_email, reset_link)

        # Verify email headers
        call_args = mock_server.sendmail.call_args
        from_email = call_args[0][0]
        to_email_sent = call_args[0][1]

        assert from_email == "no-reply@example.com"
        assert to_email_sent == "user@example.com"

    @patch('services.email.smtplib.SMTP')
    @patch('services.email.os.getenv')
    def test_send_password_reset_email_multiple_recipients(self, mock_getenv, mock_smtp):
        """Test sending to multiple recipients"""
        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "SMTP_HOST": "localhost",
            "SMTP_PORT": "1025",
            "SMTP_USER": "",
            "SMTP_PASS": "",
            "FROM_EMAIL": "no-reply@example.com"
        }.get(key, default)

        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Test the function with different email formats
        test_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user123@subdomain.example.com"
        ]

        for email in test_emails:
            mock_server.sendmail.reset_mock()
            reset_link = "https://your-frontend-domain.com/reset?token=abc123"

            send_password_reset_email(email, reset_link)

            # Verify the email was sent to the correct address
            call_args = mock_server.sendmail.call_args
            to_email_sent = call_args[0][1]
            assert to_email_sent == email
