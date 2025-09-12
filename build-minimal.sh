#!/bin/bash
set -e

echo "Starting Render build process with minimal dependencies..."

# Set ALL environment variables to avoid any compilation
export CRYPTOGRAPHY_DONT_BUILD_RUST=1
export BCRYPT_DONT_BUILD_RUST=1
export RUST_BACKTRACE=0
export PYO3_CROSS_LIB_DIR=""
export CARGO_NET_OFFLINE=true

# Upgrade pip
pip install --upgrade pip wheel setuptools

# Use minimal requirements that avoid Rust compilation entirely
echo "Installing minimal dependencies..."
if [ -f "requirements-minimal.txt" ]; then
    pip install --prefer-binary --no-cache-dir -r requirements-minimal.txt
else
    echo "Falling back to regular requirements..."
    pip install --only-binary=:all: --prefer-binary --no-cache-dir -r requirements.txt || {
        pip install --prefer-binary --no-cache-dir -r requirements.txt
    }
fi

echo "Build completed successfully!"
