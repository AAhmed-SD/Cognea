"""
Security configuration for the application.
This module centralizes all security-related settings.
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import secrets
from datetime import timedelta

class SecurityConfig(BaseSettings):
    """Security configuration settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_KEY: Optional[str] = None
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    
    # Stripe Configuration
    STRIPE_PUBLISHING_KEY: Optional[str] = None
    STRIPE_API: Optional[str] = None
    
    # Secret Key
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    
    # CORS Settings
    ALLOWED_ORIGINS: Optional[str] = None
    
    # Trusted Hosts
    TRUSTED_HOSTS: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 1000
    DISABLE_RATE_LIMIT: Optional[bool] = None
    
    # Budget Limits
    DAILY_BUDGET_LIMIT_USD: float = 10.0
    MONTHLY_BUDGET_LIMIT_USD: float = 100.0
    
    # Redis
    REDIS_URL: Optional[str] = None
    
    # Monitoring
    ENABLE_MONITORING: bool = True
    METRICS_ENDPOINT: str = "/metrics"
    
    # HTTPS
    ENABLE_HTTPS: bool = False
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None
    
    # Authentication
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Security
    MIN_PASSWORD_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL_CHARS: bool = True
    
    # Session Security
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    SESSION_COOKIE_MAX_AGE: int = 3600  # 1 hour
    
    # API Security
    API_KEY_HEADER: str = "X-API-Key"
    ENABLE_API_KEY_AUTH: bool = False
    
    # Content Security Policy
    CSP_DEFAULT_SRC: str = "'self'"
    CSP_SCRIPT_SRC: str = "'self' 'unsafe-inline'"
    CSP_STYLE_SRC: str = "'self' 'unsafe-inline'"
    CSP_IMG_SRC: str = "'self' data: https:"
    CSP_FONT_SRC: str = "'self' https:"
    CSP_CONNECT_SRC: str = "'self'"
    CSP_FRAME_SRC: str = "'none'"
    CSP_OBJECT_SRC: str = "'none'"
    
    # Security Headers
    ENABLE_HSTS: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    ENABLE_CSP: bool = True
    ENABLE_XSS_PROTECTION: bool = True
    ENABLE_CONTENT_TYPE_NOSNIFF: bool = True
    ENABLE_FRAME_DENY: bool = True
    
    # Database Security
    DATABASE_SSL_REQUIRED: bool = True
    DB_CONNECTION_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    
    # Logging Security
    LOG_SENSITIVE_DATA: bool = False
    MASK_EMAILS_IN_LOGS: bool = True
    MASK_PHONES_IN_LOGS: bool = True
    LOG_LEVEL: str = "INFO"
    
    # File Upload Security
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [
        "image/jpeg",
        "image/png", 
        "image/gif",
        "application/pdf",
        "text/plain"
    ]
    
    # Input Validation
    MAX_STRING_LENGTH: int = 1000
    MAX_ARRAY_LENGTH: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"

# Global security settings instance
security_config = SecurityConfig()

def get_cors_origins() -> List[str]:
    """Get CORS origins based on environment"""
    if security_config.ENVIRONMENT == "production":
        return security_config.PRODUCTION_ORIGINS
    return security_config.ALLOWED_ORIGINS

def get_trusted_hosts() -> List[str]:
    """Get trusted hosts based on environment"""
    if security_config.ENVIRONMENT == "production":
        return security_config.TRUSTED_HOSTS
    return ["localhost", "127.0.0.1"]

def get_content_security_policy() -> str:
    """Generate Content Security Policy header"""
    return "; ".join([
        f"default-src {security_config.CSP_DEFAULT_SRC}",
        f"script-src {security_config.CSP_SCRIPT_SRC}",
        f"style-src {security_config.CSP_STYLE_SRC}",
        f"img-src {security_config.CSP_IMG_SRC}",
        f"font-src {security_config.CSP_FONT_SRC}",
        f"connect-src {security_config.CSP_CONNECT_SRC}",
        f"frame-src {security_config.CSP_FRAME_SRC}",
        f"object-src {security_config.CSP_OBJECT_SRC}"
    ])

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength based on security configuration.
    Returns (is_valid, error_message)
    """
    if len(password) < security_config.MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {security_config.MIN_PASSWORD_LENGTH} characters long"
    
    if security_config.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if security_config.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if security_config.PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if security_config.PASSWORD_REQUIRE_SPECIAL_CHARS and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password meets security requirements"

def sanitize_input(text: str, max_length: int = None) -> str:
    """Sanitize user input"""
    if max_length is None:
        max_length = security_config.MAX_STRING_LENGTH
    
    # Remove null bytes and control characters
    sanitized = "".join(char for char in text if ord(char) >= 32 or char in "\n\r\t")
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe"""
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    return not any(char in filename for char in dangerous_chars)

def get_rate_limit_config() -> dict:
    """Get rate limiting configuration"""
    return {
        "enabled": security_config.RATE_LIMIT_ENABLED,
        "requests_per_minute": security_config.RATE_LIMIT_REQUESTS_PER_MINUTE,
        "requests_per_hour": security_config.RATE_LIMIT_REQUESTS_PER_HOUR
    } 