"""
Monitoring configuration for Sentry and Prometheus.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class MonitoringConfig:
    """Configuration for monitoring and observability services."""

    # Sentry Configuration
    SENTRY_DSN: str | None = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "development")
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    SENTRY_PROFILES_SAMPLE_RATE: float = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))

    # Prometheus Configuration
    PROMETHEUS_ENABLED: bool = os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"
    PROMETHEUS_PORT: int = int(os.getenv("PROMETHEUS_PORT", "9090"))
    PROMETHEUS_PATH: str = os.getenv("PROMETHEUS_PATH", "/metrics")

    # Application Monitoring
    APP_NAME: str = "cognie-ai"
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")

    # Performance Monitoring
    PERFORMANCE_MONITORING_ENABLED: bool = os.getenv("PERFORMANCE_MONITORING_ENABLED", "true").lower() == "true"
    SLOW_QUERY_THRESHOLD: float = float(os.getenv("SLOW_QUERY_THRESHOLD", "1.0"))  # seconds
    ERROR_RATE_THRESHOLD: float = float(os.getenv("ERROR_RATE_THRESHOLD", "5.0"))  # percentage

    # Alerting Configuration
    ALERT_EMAIL_ENABLED: bool = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true"
    ALERT_EMAIL_RECIPIENTS: list[str] = os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(",") if os.getenv("ALERT_EMAIL_RECIPIENTS") else []

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    LOG_TO_SENTRY: bool = os.getenv("LOG_TO_SENTRY", "true").lower() == "true"


# Global monitoring config instance
monitoring_config = MonitoringConfig()
