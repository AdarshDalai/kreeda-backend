#!/bin/bash
set -e

echo "Starting build process..."

# Upgrade pip and install build tools
pip install --upgrade pip setuptools wheel

# Set environment variables to avoid Rust compilation
export CRYPTOGRAPHY_DONT_BUILD_RUST=1
export BCRYPT_DONT_BUILD_RUST=1

# Install dependencies with binary wheels only for problematic packages
echo "Installing dependencies with binary wheels..."
pip install --only-binary=cryptography,bcrypt,cffi \
    --prefer-binary \
    --no-cache-dir \
    -r requirements.txt

echo "Build completed successfully!"
