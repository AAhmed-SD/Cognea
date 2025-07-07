#!/usr/bin/env python3
"""Script to run tests that don't require complex dependencies."""

import os
import sys
import subprocess
from typing import List

# Set up test environment
def setup_test_env() -> None:
    """Set up test environment variables."""
    test_env = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_ANON_KEY": "test_anon_key",
        "SUPABASE_SERVICE_ROLE_KEY": "test_service_role_key",
        "SUPABASE_JWT_KEY": "test_jwt_secret_key_minimum_32_chars_long",
        "OPENAI_API_KEY": "sk-test_openai_api_key",
        "SECRET_KEY": "test_secret_key_minimum_32_characters_long_for_testing",
        "REDIS_URL": "redis://localhost:6379",
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "DISABLE_RATE_LIMIT": "true",
        "ENABLE_AI_FEATURES": "true",
        "ENABLE_NOTION_INTEGRATION": "false",
    }
    
    for key, value in test_env.items():
        os.environ[key] = value

def run_tests(test_files: List[str]) -> int:
    """Run specified test files and return the exit code."""
    setup_test_env()
    
    cmd = [
        "python", "-m", "pytest",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v"
    ] + test_files
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def main() -> None:
    """Main function."""
    # Start with basic tests that we know work
    safe_tests = [
        "test_basic.py",
        "test_simple_coverage.py",
    ]
    
    print("Running safe tests...")
    exit_code = run_tests(safe_tests)
    
    if exit_code == 0:
        print("✅ All safe tests passed!")
        
        # Try to add more tests gradually
        additional_tests = [
            "tests/test_review_engine.py",
        ]
        
        print("\nTrying additional tests...")
        all_tests = safe_tests + additional_tests
        exit_code = run_tests(all_tests)
        
        if exit_code == 0:
            print("✅ Additional tests also passed!")
        else:
            print("❌ Some additional tests failed")
    else:
        print("❌ Safe tests failed")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()