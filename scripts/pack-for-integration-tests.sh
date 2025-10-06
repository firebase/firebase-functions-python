#!/usr/bin/env bash

# Script to build Python SDK and prepare it for integration tests
# This is the Python equivalent of the TypeScript SDK's pack-for-integration-tests command

set -e  # Exit on error

echo "Building firebase-functions Python SDK from source..."

# Clean any previous builds
rm -rf dist/
rm -f integration_test/firebase-functions-python-local.whl

# Build the package using uv
echo "Building wheel package..."
uv build

# Find the built wheel file
WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -n 1)

if [ -z "$WHEEL_FILE" ]; then
    echo "Error: No wheel file found in dist/ directory"
    exit 1
fi

# Copy wheel to integration test directory
echo "Copying wheel to integration_test directory..."
cp "$WHEEL_FILE" integration_test/firebase-functions-python-local.whl

echo "SDK built and packed successfully!"
echo "Wheel file: integration_test/firebase-functions-python-local.whl"