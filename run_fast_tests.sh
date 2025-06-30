#!/bin/bash

# Run only the fast tests that don't make real API calls
echo "Running fast tests only..."

export DISABLE_RATE_LIMIT=true

# Core tests that work
echo "Running core tests..."
python -m pytest test_comprehensive.py tests/test_async_comprehensive.py -v --tb=short

# Simple tests that work
echo "Running simple tests..."
python -m pytest test_simple_coverage.py::test_rate_limit_check test_simple_coverage.py::test_budget_limit_check -v --tb=short

# App tests that work
echo "Running app tests..."
python -m pytest test_app.py -v --tb=short

# Scheduler tests that work
echo "Running scheduler tests..."
python -m pytest tests/test_scheduler_scoring.py -v --tb=short

# Rate limit tests that work
echo "Running rate limit tests..."
python -m pytest tests/test_rate_limit_backoff.py -v --tb=short

echo "Fast tests completed!" 