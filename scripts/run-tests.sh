#!/bin/bash

# Kreeda API Test Automation Runner
# This script runs the complete test suite using Newman CLI

echo "🚀 Kreeda API Test Automation"
echo "================================="

# Check if Newman is installed
if ! command -v newman &> /dev/null; then
    echo "❌ Newman is not installed. Installing..."
    npm install -g newman
fi

# Set default environment
ENVIRONMENT=${1:-development}
REPORT_FORMAT=${2:-cli}

# File paths
COLLECTION_FILE="./postman/Kreeda_API_Complete_Tests.postman_collection.json"

if [ "$ENVIRONMENT" = "development" ]; then
    ENV_FILE="./postman/Kreeda_Development_TestAutomation.postman_environment.json"
    echo "🏠 Running tests against DEVELOPMENT environment"
elif [ "$ENVIRONMENT" = "production" ]; then
    ENV_FILE="./postman/Kreeda_Production_TestAutomation.postman_environment.json"
    echo "🌐 Running tests against PRODUCTION environment"
    echo "⚠️  WARNING: This will test production endpoints!"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Test cancelled"
        exit 1
    fi
else
    echo "❌ Invalid environment. Use 'development' or 'production'"
    exit 1
fi

# Check if files exist
if [ ! -f "$COLLECTION_FILE" ]; then
    echo "❌ Collection file not found: $COLLECTION_FILE"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Environment file not found: $ENV_FILE"
    exit 1
fi

# Create results directory
mkdir -p ./test-results

# Run tests based on report format
echo "📋 Starting test execution..."
echo "Collection: $COLLECTION_FILE"
echo "Environment: $ENV_FILE"
echo "Report Format: $REPORT_FORMAT"
echo ""

if [ "$REPORT_FORMAT" = "html" ]; then
    newman run "$COLLECTION_FILE" \
        -e "$ENV_FILE" \
        --reporters html,cli \
        --reporter-html-export "./test-results/kreeda-api-test-report.html" \
        --color on \
        --delay-request 100
elif [ "$REPORT_FORMAT" = "junit" ]; then
    newman run "$COLLECTION_FILE" \
        -e "$ENV_FILE" \
        --reporters junit,cli \
        --reporter-junit-export "./test-results/kreeda-api-test-results.xml" \
        --color on \
        --delay-request 100
else
    newman run "$COLLECTION_FILE" \
        -e "$ENV_FILE" \
        --reporters cli \
        --color on \
        --delay-request 100
fi

TEST_EXIT_CODE=$?

echo ""
echo "================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed successfully!"
    echo "🎉 API is ready for production deployment"
else
    echo "❌ Some tests failed"
    echo "🔍 Review the output above for details"
fi

if [ "$REPORT_FORMAT" = "html" ]; then
    echo "📊 HTML report generated: ./test-results/kreeda-api-test-report.html"
elif [ "$REPORT_FORMAT" = "junit" ]; then
    echo "📊 JUnit report generated: ./test-results/kreeda-api-test-results.xml"
fi

echo "================================="

exit $TEST_EXIT_CODE
