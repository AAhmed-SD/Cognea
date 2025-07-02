"""
Email service for password reset and email verification
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from services.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending transactional emails"""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@cognie.app")
        self.app_name = os.getenv("APP_NAME", "Cognie")
        self.app_url = os.getenv("APP_URL", "https://cognie.app")
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key")

        # Token expiration times
        self.password_reset_expiry = timedelta(hours=24)
        self.email_verification_expiry = timedelta(days=7)

        self.supabase = get_supabase_client()

    def _create_token(self, payload: Dict[str, Any], expiry: timedelta) -> str:
        """Create a JWT token with expiration"""
        payload.update({"exp": datetime.utcnow() + expiry, "iat": datetime.utcnow()})
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

    def _send_email(
        self, to_email: str, subject: str, html_content: str, text_content: str
    ) -> bool:
        """Send email using SMTP"""
        try:
            if not all([self.smtp_username, self.smtp_password]):
                logger.warning("SMTP credentials not configured, skipping email send")
                return False

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            # Attach both HTML and text versions
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_password_reset_email(
        self, user_id: str, email: str, user_name: str = None
    ) -> bool:
        """Send password reset email"""
        try:
            # Create password reset token
            token = self._create_token(
                {"user_id": user_id, "type": "password_reset"},
                self.password_reset_expiry,
            )

            # Store token in database
            token_data = {
                "user_id": user_id,
                "token": token,
                "type": "password_reset",
                "expires_at": (
                    datetime.utcnow() + self.password_reset_expiry
                ).isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            }

            self.supabase.table("auth_tokens").insert(token_data).execute()

            # Create reset URL
            reset_url = f"{self.app_url}/reset-password?token={token}"

            # Email content
            subject = f"Reset Your {self.app_name} Password"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Reset Your Password</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{self.app_name}</h1>
                        <p>Password Reset Request</p>
                    </div>
                    <div class="content">
                        <h2>Hello{f" {user_name}" if user_name else ""}!</h2>
                        <p>We received a request to reset your password for your {self.app_name} account.</p>
                        <p>Click the button below to reset your password:</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">Reset Password</a>
                        </p>
                        <p>If the button doesn't work, copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #666;">{reset_url}</p>
                        <p><strong>This link will expire in 24 hours.</strong></p>
                        <p>If you didn't request this password reset, you can safely ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>This email was sent from {self.app_name}. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_content = f"""
            Reset Your {self.app_name} Password
            
            Hello{f" {user_name}" if user_name else ""}!
            
            We received a request to reset your password for your {self.app_name} account.
            
            Click the link below to reset your password:
            {reset_url}
            
            This link will expire in 24 hours.
            
            If you didn't request this password reset, you can safely ignore this email.
            
            Best regards,
            The {self.app_name} Team
            """

            return self._send_email(email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return False

    def send_email_verification(
        self, user_id: str, email: str, user_name: str = None
    ) -> bool:
        """Send email verification email"""
        try:
            # Create verification token
            token = self._create_token(
                {"user_id": user_id, "type": "email_verification"},
                self.email_verification_expiry,
            )

            # Store token in database
            token_data = {
                "user_id": user_id,
                "token": token,
                "type": "email_verification",
                "expires_at": (
                    datetime.utcnow() + self.email_verification_expiry
                ).isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            }

            self.supabase.table("auth_tokens").insert(token_data).execute()

            # Create verification URL
            verify_url = f"{self.app_url}/verify-email?token={token}"

            # Email content
            subject = f"Verify Your {self.app_name} Email Address"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Verify Your Email</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{self.app_name}</h1>
                        <p>Email Verification</p>
                    </div>
                    <div class="content">
                        <h2>Welcome{f" {user_name}" if user_name else ""}!</h2>
                        <p>Thank you for signing up for {self.app_name}. To complete your registration, please verify your email address.</p>
                        <p>Click the button below to verify your email:</p>
                        <p style="text-align: center;">
                            <a href="{verify_url}" class="button">Verify Email</a>
                        </p>
                        <p>If the button doesn't work, copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #666;">{verify_url}</p>
                        <p><strong>This link will expire in 7 days.</strong></p>
                    </div>
                    <div class="footer">
                        <p>This email was sent from {self.app_name}. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_content = f"""
            Verify Your {self.app_name} Email Address
            
            Welcome{f" {user_name}" if user_name else ""}!
            
            Thank you for signing up for {self.app_name}. To complete your registration, please verify your email address.
            
            Click the link below to verify your email:
            {verify_url}
            
            This link will expire in 7 days.
            
            Best regards,
            The {self.app_name} Team
            """

            return self._send_email(email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Failed to send email verification: {str(e)}")
            return False

    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verify password reset token and return user_id"""
        try:
            # Verify token
            payload = self._verify_token(token)
            if not payload or payload.get("type") != "password_reset":
                return None

            user_id = payload.get("user_id")
            if not user_id:
                return None

            # Check if token exists in database and is not expired
            result = (
                self.supabase.table("auth_tokens")
                .select("*")
                .eq("token", token)
                .eq("type", "password_reset")
                .execute()
            )

            if not result.data:
                return None

            token_record = result.data[0]
            expires_at = datetime.fromisoformat(
                token_record["expires_at"].replace("Z", "+00:00")
            )

            if datetime.utcnow() > expires_at:
                return None

            return user_id

        except Exception as e:
            logger.error(f"Failed to verify password reset token: {str(e)}")
            return None

    def verify_email_token(self, token: str) -> Optional[str]:
        """Verify email verification token and return user_id"""
        try:
            # Verify token
            payload = self._verify_token(token)
            if not payload or payload.get("type") != "email_verification":
                return None

            user_id = payload.get("user_id")
            if not user_id:
                return None

            # Check if token exists in database and is not expired
            result = (
                self.supabase.table("auth_tokens")
                .select("*")
                .eq("token", token)
                .eq("type", "email_verification")
                .execute()
            )

            if not result.data:
                return None

            token_record = result.data[0]
            expires_at = datetime.fromisoformat(
                token_record["expires_at"].replace("Z", "+00:00")
            )

            if datetime.utcnow() > expires_at:
                return None

            return user_id

        except Exception as e:
            logger.error(f"Failed to verify email token: {str(e)}")
            return None

    def invalidate_token(self, token: str) -> bool:
        """Invalidate a token by deleting it from database"""
        try:
            self.supabase.table("auth_tokens").delete().eq("token", token).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate token: {str(e)}")
            return False

    def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens from database"""
        try:
            # Delete tokens that have expired
            result = (
                self.supabase.table("auth_tokens")
                .delete()
                .lt("expires_at", datetime.utcnow().isoformat())
                .execute()
            )
            deleted_count = len(result.data) if result.data else 0
            logger.info(f"Cleaned up {deleted_count} expired tokens")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {str(e)}")
            return 0


# Global email service instance
email_service = EmailService()
