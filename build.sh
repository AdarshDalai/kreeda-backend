#!/bin/bash
set -e

echo "Starting Render build process..."

# Set ALL possible environment variables to avoid Rust compilation
export CRYPTOGRAPHY_DONT_BUILD_RUST=1
export BCRYPT_DONT_BUILD_RUST=1
export RUST_BACKTRACE=0
export PYO3_CROSS_LIB_DIR=""
export CARGO_NET_OFFLINE=true
export MATURIN_BUILD_ARGS="--no-default-features"

# Upgrade pip and install build tools
pip install --upgrade pip wheel setuptools

# First, try to install everything with binary-only
echo "Attempting binary-only installation for ALL packages..."
pip install --only-binary=:all: --prefer-binary --no-cache-dir -r requirements.txt || {
    echo "Full binary-only failed, trying with specific binary packages..."
    
    # Install problematic packages individually with specific versions that have wheels
    pip install --only-binary=cryptography cryptography==41.0.7
    pip install --only-binary=bcrypt bcrypt==4.0.1
    pip install --only-binary=cffi cffi
    
    # Install remaining packages
    pip install --prefer-binary --no-cache-dir -r requirements.txt
}

echo "Build completed successfully!"
