#!/usr/bin/env python3
"""Basic test file to verify testing infrastructure."""

import os
import sys
import pytest
from typing import Dict, Any

# Set up environment for testing
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test_anon_key"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test_service_role_key"
os.environ["SUPABASE_JWT_KEY"] = "test_jwt_secret_key_minimum_32_chars_long"
os.environ["OPENAI_API_KEY"] = "sk-test_openai_api_key"
os.environ["SECRET_KEY"] = "test_secret_key_minimum_32_characters_long_for_testing"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["DISABLE_RATE_LIMIT"] = "true"
os.environ["ENABLE_AI_FEATURES"] = "true"
os.environ["ENABLE_NOTION_INTEGRATION"] = "false"

def test_basic_functionality() -> None:
    """Test basic functionality."""
    assert 1 + 1 == 2
    assert "test" in "testing"
    assert True is True

def test_environment_variables() -> None:
    """Test that environment variables are set correctly."""
    assert os.environ.get("ENVIRONMENT") == "test"
    assert os.environ.get("DEBUG") == "true"
    assert os.environ.get("DISABLE_RATE_LIMIT") == "true"

def test_imports() -> None:
    """Test that basic imports work."""
    try:
        import fastapi
        import pydantic
        import httpx
        import pytest
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_type_annotations() -> None:
    """Test that type annotations work correctly."""
    def typed_function(x: int, y: str) -> Dict[str, Any]:
        return {"number": x, "text": y}
    
    result = typed_function(42, "hello")
    assert result["number"] == 42
    assert result["text"] == "hello"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])