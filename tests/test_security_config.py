import importlib

import pytest

from config import security as security_mod

# Make sure we have a fresh module instance for each test where we mutate the global config


def _reload_security():
    """Reload security module to refresh the singleton config if needed."""
    return importlib.reload(security_mod)


class TestValidatePasswordStrength:
    """Tests for validate_password_strength function."""

    @pytest.mark.parametrize(
        "password, expected_valid, expected_msg_contains",
        [
            ("Abcdef1!", True, "meets"),  # Valid strong password
            ("abc", False, "at least"),  # Too short
            ("abcdefg1!", False, "uppercase"),  # Missing uppercase
            ("ABCDEFG1!", False, "lowercase"),  # Missing lowercase
            ("Abcdefgh!", False, "digit"),  # Missing digit
            ("Abcdefg1", False, "special"),  # Missing special char
        ],
    )
    def test_validate_password_strength(self, password, expected_valid, expected_msg_contains):
        valid, msg = security_mod.validate_password_strength(password)
        assert valid is expected_valid
        assert expected_msg_contains.lower() in msg.lower()


class TestSanitizeInput:
    """Tests for sanitize_input function."""

    def test_remove_dangerous_characters(self):
        text = '<script>alert("xss")</script>'
        sanitized = security_mod.sanitize_input(text)
        assert "<" not in sanitized and ">" not in sanitized and "&" not in sanitized

    def test_trim_whitespace_and_max_length(self):
        raw = "   abcdefghijk   "
        # Limit to 5; expect trimmed and truncated to 5 characters
        sanitized = security_mod.sanitize_input(raw, max_length=5)
        assert sanitized == "ab"

    def test_empty_string(self):
        assert security_mod.sanitize_input("") == ""


class TestIsSafeFilename:
    """Tests for is_safe_filename function."""

    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("report.pdf", True),
            ("../../secret.txt", False),
            ("image<1>.png", False),
            ("normal_file-name.txt", True),
            ("bad|file.txt", False),
        ],
    )
    def test_filename_safety(self, filename, expected):
        assert security_mod.is_safe_filename(filename) is expected


class TestRateLimitConfig:
    """Tests for get_rate_limit_config function."""

    def test_default_rate_limit_config(self):
        cfg = security_mod.get_rate_limit_config()
        assert cfg["requests_per_minute"] == security_mod.security_config.RATE_LIMIT_REQUESTS_PER_MINUTE
        assert cfg["requests_per_hour"] == security_mod.security_config.RATE_LIMIT_REQUESTS_PER_HOUR
        assert cfg["disabled"] is (security_mod.security_config.DISABLE_RATE_LIMIT or False)

    def test_disable_rate_limit_flag(self):
        # Temporarily toggle the flag
        original = security_mod.security_config.DISABLE_RATE_LIMIT
        security_mod.security_config.DISABLE_RATE_LIMIT = True
        try:
            cfg = security_mod.get_rate_limit_config()
            assert cfg["disabled"] is True
        finally:
            # Restore
            security_mod.security_config.DISABLE_RATE_LIMIT = original