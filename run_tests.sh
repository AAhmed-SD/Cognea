#!/bin/bash

# Run tests with rate limiting disabled
export DISABLE_RATE_LIMIT=true
export TEST_ENV=true

echo "Running tests with rate limiting disabled..."
python -m pytest "$@" 