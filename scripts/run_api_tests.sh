#!/bin/bash

# Kreeda API Test Automation Script
# This script runs comprehensive API tests using Newman

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
POSTMAN_DIR="$PROJECT_DIR/postman"
RESULTS_DIR="$PROJECT_DIR/test-results"

# Files
COLLECTION_FILE="$POSTMAN_DIR/Kreeda_API_Complete.postman_collection.json"
DEV_ENV_FILE="$POSTMAN_DIR/Kreeda_Development.postman_environment.json"
PROD_ENV_FILE="$POSTMAN_DIR/Kreeda_Production.postman_environment.json"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if server is running
check_server() {
    local url=$1
    local max_retries=10
    local retry_count=0
    
    print_status "Checking if server is running at $url..."
    
    while [ $retry_count -lt $max_retries ]; do
        if curl -s -f "$url/health" > /dev/null 2>&1 || curl -s -f "$url" > /dev/null 2>&1; then
            print_success "Server is running at $url"
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        print_warning "Server not ready, retrying in 2 seconds... ($retry_count/$max_retries)"
        sleep 2
    done
    
    print_error "Server is not running at $url after $max_retries attempts"
    return 1
}

# Function to run Newman tests
run_newman_tests() {
    local environment_file=$1
    local environment_name=$2
    local base_url=$3
    
    print_status "Running Newman tests for $environment_name environment..."
    
    # Check if server is running
    if ! check_server "$base_url"; then
        print_error "Cannot run tests - server is not accessible"
        return 1
    fi
    
    # Get current timestamp
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local results_file="$RESULTS_DIR/newman_results_${environment_name}_${timestamp}.json"
    local html_report="$RESULTS_DIR/newman_report_${environment_name}_${timestamp}.html"
    
    # Install newman if not present
    if ! command -v newman &> /dev/null; then
        print_status "Installing Newman..."
        npm install -g newman newman-reporter-html
    fi
    
    # Run Newman tests
    newman run "$COLLECTION_FILE" \
        --environment "$environment_file" \
        --reporters cli,json,html \
        --reporter-json-export "$results_file" \
        --reporter-html-export "$html_report" \
        --delay-request 100 \
        --timeout-request 30000 \
        --timeout-script 30000 \
        --global-var "timestamp=$timestamp" \
        --color on \
        --verbose
    
    local newman_exit_code=$?
    
    if [ $newman_exit_code -eq 0 ]; then
        print_success "Newman tests completed successfully for $environment_name"
        print_status "Results saved to: $results_file"
        print_status "HTML report saved to: $html_report"
    else
        print_error "Newman tests failed for $environment_name (exit code: $newman_exit_code)"
        return $newman_exit_code
    fi
    
    return 0
}

# Function to analyze test results
analyze_results() {
    local environment_name=$1
    local results_pattern="$RESULTS_DIR/newman_results_${environment_name}_*.json"
    
    # Get the latest results file
    local latest_results=$(ls -t $results_pattern 2>/dev/null | head -n1)
    
    if [ -z "$latest_results" ]; then
        print_warning "No results found for $environment_name"
        return 1
    fi
    
    print_status "Analyzing results from: $latest_results"
    
    # Extract key metrics using jq
    if command -v jq &> /dev/null; then
        local total_requests=$(jq '.run.stats.requests.total' "$latest_results")
        local failed_requests=$(jq '.run.stats.requests.failed' "$latest_results")
        local total_tests=$(jq '.run.stats.tests.total' "$latest_results")
        local failed_tests=$(jq '.run.stats.tests.failed' "$latest_results")
        local total_assertions=$(jq '.run.stats.assertions.total' "$latest_results")
        local failed_assertions=$(jq '.run.stats.assertions.failed' "$latest_results")
        
        echo ""
        echo "=== TEST RESULTS SUMMARY ($environment_name) ==="
        echo "Requests: $((total_requests - failed_requests))/$total_requests passed"
        echo "Tests: $((total_tests - failed_tests))/$total_tests passed"
        echo "Assertions: $((total_assertions - failed_assertions))/$total_assertions passed"
        echo ""
        
        if [ "$failed_requests" -gt 0 ] || [ "$failed_tests" -gt 0 ] || [ "$failed_assertions" -gt 0 ]; then
            print_warning "Some tests failed. Check the detailed report for more information."
            return 1
        else
            print_success "All tests passed!"
            return 0
        fi
    else
        print_warning "jq not found. Install jq for detailed result analysis."
        return 0
    fi
}

# Function to start Docker services
start_docker_services() {
    print_status "Starting Docker services..."
    cd "$PROJECT_DIR"
    
    if docker-compose ps | grep -q "Up"; then
        print_status "Docker services are already running"
    else
        docker-compose up -d
        print_status "Waiting for services to start..."
        sleep 10
    fi
}

# Function to update OpenAPI spec and regenerate collection
update_collection() {
    local base_url=${1:-"http://localhost:8000"}
    
    print_status "Updating OpenAPI specification and regenerating Postman collection..."
    
    # Download latest OpenAPI spec
    if curl -s -f "$base_url/openapi.json" -o "$POSTMAN_DIR/openapi.json"; then
        print_success "Downloaded latest OpenAPI specification"
    else
        print_error "Failed to download OpenAPI specification from $base_url"
        return 1
    fi
    
    # Regenerate Postman collection
    cd "$PROJECT_DIR"
    if python3 generate_postman_collection.py "$POSTMAN_DIR/openapi.json" "$COLLECTION_FILE"; then
        print_success "Regenerated Postman collection"
    else
        print_error "Failed to regenerate Postman collection"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev          Run tests against development environment (default)"
    echo "  prod         Run tests against production environment"
    echo "  both         Run tests against both environments"
    echo "  update       Update OpenAPI spec and regenerate collection"
    echo "  docker       Start Docker services and run dev tests"
    echo ""
    echo "Options:"
    echo "  -h, --help   Show this help message"
    echo "  -v, --verbose Enable verbose output"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run development tests"
    echo "  $0 dev                # Run development tests"
    echo "  $0 prod               # Run production tests"
    echo "  $0 both               # Run tests on both environments"
    echo "  $0 docker             # Start Docker and run tests"
    echo "  $0 update             # Update collection from API"
}

# Main execution
main() {
    local command=${1:-"dev"}
    local verbose=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            dev|prod|both|update|docker)
                command=$1
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_status "Starting Kreeda API Test Automation..."
    print_status "Command: $command"
    
    # Check if required files exist
    if [ ! -f "$COLLECTION_FILE" ]; then
        print_error "Postman collection not found: $COLLECTION_FILE"
        print_status "Run '$0 update' to generate the collection first"
        exit 1
    fi
    
    case $command in
        "update")
            update_collection
            ;;
        "docker")
            start_docker_services
            update_collection "http://localhost:8000"
            run_newman_tests "$DEV_ENV_FILE" "development" "http://localhost:8000"
            analyze_results "development"
            ;;
        "dev")
            run_newman_tests "$DEV_ENV_FILE" "development" "http://localhost:8000"
            analyze_results "development"
            ;;
        "prod")
            run_newman_tests "$PROD_ENV_FILE" "production" "https://your-production-domain.com"
            analyze_results "production"
            ;;
        "both")
            print_status "Running tests on both environments..."
            
            # Development tests
            run_newman_tests "$DEV_ENV_FILE" "development" "http://localhost:8000"
            local dev_result=$?
            analyze_results "development"
            
            # Production tests
            run_newman_tests "$PROD_ENV_FILE" "production" "https://your-production-domain.com"
            local prod_result=$?
            analyze_results "production"
            
            # Overall result
            if [ $dev_result -eq 0 ] && [ $prod_result -eq 0 ]; then
                print_success "All tests passed on both environments!"
                exit 0
            else
                print_error "Some tests failed. Check the reports for details."
                exit 1
            fi
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
