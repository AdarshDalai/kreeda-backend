#!/bin/bash

# Test Runner Script for Kreeda Backend
# This script runs comprehensive pytest tests with proper configuration

echo "🏏 Kreeda Backend Test Suite Runner"
echo "=================================="

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing pytest..."
    pip install pytest pytest-asyncio pytest-cov httpx
fi

# Set environment variables for testing
export TESTING=true
export DATABASE_URL="sqlite:///./test.db"
export SUPABASE_URL="https://test.supabase.co"
export SUPABASE_KEY="test_key"

# Clean up any existing test database
rm -f test.db

echo ""
echo "🧪 Running Test Suite..."
echo "========================"

# Run different test categories
echo ""
echo "1️⃣ Running Unit Tests..."
pytest tests/ -m unit -v --tb=short

echo ""
echo "2️⃣ Running Integration Tests..."
pytest tests/ -m integration -v --tb=short

echo ""
echo "3️⃣ Running End-to-End Tests..."
pytest tests/ -m e2e -v --tb=short

echo ""
echo "4️⃣ Running Performance Tests..."
pytest tests/ -m performance -v --tb=short

echo ""
echo "📊 Running Full Test Suite with Coverage..."
echo "============================================"
pytest tests/ -v \
    --cov=app \
    --cov-report=html:htmlcov \
    --cov-report=term-missing \
    --cov-report=xml:coverage.xml \
    --tb=short \
    --durations=10

echo ""
echo "🔍 Test Summary by Category:"
echo "============================="
echo "Unit Tests:"
pytest tests/ -m unit --collect-only -q | grep "test session starts" -A 1

echo ""
echo "Integration Tests:"
pytest tests/ -m integration --collect-only -q | grep "test session starts" -A 1

echo ""
echo "E2E Tests:"
pytest tests/ -m e2e --collect-only -q | grep "test session starts" -A 1

echo ""
echo "Performance Tests:"
pytest tests/ -m performance --collect-only -q | grep "test session starts" -A 1

echo ""
echo "📈 Coverage Report Generated:"
echo "- HTML Report: htmlcov/index.html"
echo "- XML Report: coverage.xml"

echo ""
echo "✅ Test Suite Complete!"
echo "======================="

# Clean up test database
rm -f test.db

echo "🧹 Cleanup completed."