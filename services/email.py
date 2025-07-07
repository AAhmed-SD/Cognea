import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, reset_link: str):
    pass
    try:
        smtp_host = os.getenv("SMTP_HOST", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", 1025))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASS", "")
        from_email = os.getenv("FROM_EMAIL", "no-reply@example.com")

        reset_link = reset_link.replace(
            "https://your-frontend-domain.com", "http://localhost:3000"
        )

        subject = "Password Reset Request"
        body = f"""
        <p>You requested a password reset. Click the link below to reset your password:</p>
        <p><a href='{reset_link}'>Reset Password</a></p>
        <p>If you did not request this, you can ignore this email.</p>
        """
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_pass:
                server.starttls()
                server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to_email, msg.as_string())

        logger.info(f"Password reset email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        # Don't raise the error - just log it so the API doesn't crash
        # In production, you'd want to use a proper email service
