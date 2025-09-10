#!/bin/bash
# Comprehensive Newman Testing Script for Kreeda API
# This script simulates a realistic cricket match scenario with multiple users

set -e  # Exit on any error

echo "🏏 Starting Kreeda API Comprehensive Testing with Newman"
echo "=================================================="

# Check if newman is installed
if ! command -v newman &> /dev/null; then
    echo "❌ Newman is not installed. Installing..."
    npm install -g newman
fi

# Configuration
API_BASE_URL="http://localhost:8000"
COLLECTION_FILE="postman/Kreeda_API.postman_collection.json"
DEV_ENV_FILE="postman/Kreeda_Development.postman_environment.json"
RESULTS_DIR="test_results/$(date +%Y%m%d_%H%M%S)"

# Create results directory
mkdir -p "$RESULTS_DIR"

echo "📁 Test results will be saved to: $RESULTS_DIR"

# Function to run newman with proper error handling
run_newman_test() {
    local test_name=$1
    local additional_vars=$2
    local report_name="${test_name// /_}"
    
    echo "🧪 Running test: $test_name"
    
    newman run "$COLLECTION_FILE" \
        --environment "$DEV_ENV_FILE" \
        --reporters cli,json,html \
        --reporter-json-export "$RESULTS_DIR/${report_name}.json" \
        --reporter-html-export "$RESULTS_DIR/${report_name}.html" \
        --delay-request 100 \
        --timeout-request 10000 \
        $additional_vars || {
            echo "❌ Test failed: $test_name"
            return 1
        }
    
    echo "✅ Test completed: $test_name"
    return 0
}

# Function to check API health
check_api_health() {
    echo "🏥 Checking API Health..."
    
    if curl -f -s "$API_BASE_URL/health" > /dev/null; then
        echo "✅ API is healthy and responsive"
        return 0
    else
        echo "❌ API is not responding. Please start the API server."
        echo "Run: docker-compose up -d"
        exit 1
    fi
}

# Function to generate unique test data
generate_test_data() {
    local timestamp=$(date +%s)
    echo "📊 Generating unique test data for this run..."
    
    # Generate unique emails and usernames for each test user
    export CAPTAIN_A_EMAIL="captain_a_${timestamp}@kreeda.com"
    export CAPTAIN_A_USERNAME="captain_a_${timestamp}"
    export CAPTAIN_B_EMAIL="captain_b_${timestamp}@kreeda.com" 
    export CAPTAIN_B_USERNAME="captain_b_${timestamp}"
    export UMPIRE_EMAIL="umpire_${timestamp}@kreeda.com"
    export UMPIRE_USERNAME="umpire_${timestamp}"
    export SPECTATOR_EMAIL="spectator_${timestamp}@kreeda.com"
    export SPECTATOR_USERNAME="spectator_${timestamp}"
    
    # Generate team names
    export TEAM_A_NAME="Warriors ${timestamp:(-4)}"
    export TEAM_A_SHORT="WAR${timestamp:(-2)}"
    export TEAM_B_NAME="Champions ${timestamp:(-4)}"
    export TEAM_B_SHORT="CHA${timestamp:(-2)}"
    
    # Generate match data
    export MATCH_VENUE="Stadium ${timestamp:(-4)}"
    export MATCH_DATE=$(date -d "+1 day" -Iseconds)
    
    echo "✅ Test data generated successfully"
}

# Main testing workflow
main() {
    echo "🚀 Starting comprehensive testing workflow..."
    
    # Phase 1: Pre-flight checks
    check_api_health
    generate_test_data
    
    # Phase 2: Health checks
    echo -e "\n📋 Phase 1: Health Checks"
    run_newman_test "Health Checks" \
        "--folder 'Health Checks'"
    
    # Phase 3: User Registration and Authentication
    echo -e "\n👥 Phase 2: User Registration & Authentication"
    
    # Register Captain A
    run_newman_test "Register Captain A" \
        "--folder 'Authentication' \
         --global-var 'test_email=${CAPTAIN_A_EMAIL}' \
         --global-var 'test_username=${CAPTAIN_A_USERNAME}' \
         --global-var 'test_full_name=Captain Team A' \
         --global-var 'test_password=password123' \
         --global-var 'captain_a_token=' \
         --bail folder"
    
    # Register Captain B  
    run_newman_test "Register Captain B" \
        "--global-var 'test_email=${CAPTAIN_B_EMAIL}' \
         --global-var 'test_username=${CAPTAIN_B_USERNAME}' \
         --global-var 'test_full_name=Captain Team B' \
         --global-var 'test_password=password123' \
         --global-var 'captain_b_token=' \
         --bail folder"
    
    # Register Umpire
    run_newman_test "Register Umpire" \
        "--global-var 'test_email=${UMPIRE_EMAIL}' \
         --global-var 'test_username=${UMPIRE_USERNAME}' \
         --global-var 'test_full_name=Match Umpire' \
         --global-var 'test_password=password123' \
         --global-var 'umpire_token=' \
         --bail folder"
    
    # Register Spectator
    run_newman_test "Register Spectator" \
        "--global-var 'test_email=${SPECTATOR_EMAIL}' \
         --global-var 'test_username=${SPECTATOR_USERNAME}' \
         --global-var 'test_full_name=Cricket Spectator' \
         --global-var 'test_password=password123' \
         --global-var 'spectator_token=' \
         --bail folder"
    
    # Phase 4: Team Management
    echo -e "\n🏏 Phase 3: Team Management"
    
    # Captain A creates Team A
    run_newman_test "Create Team A" \
        "--folder 'Teams Management' \
         --global-var 'team_name=${TEAM_A_NAME}' \
         --global-var 'team_short_name=${TEAM_A_SHORT}' \
         --global-var 'captain_email=${CAPTAIN_A_EMAIL}' \
         --bail folder"
    
    # Captain B creates Team B
    run_newman_test "Create Team B" \
        "--global-var 'team_name=${TEAM_B_NAME}' \
         --global-var 'team_short_name=${TEAM_B_SHORT}' \
         --global-var 'captain_email=${CAPTAIN_B_EMAIL}' \
         --bail folder"
    
    # Phase 5: Match Creation and Management
    echo -e "\n🏆 Phase 4: Match Creation & Management"
    
    run_newman_test "Create Cricket Match" \
        "--folder 'Cricket Matches' \
         --global-var 'venue=${MATCH_VENUE}' \
         --global-var 'match_date=${MATCH_DATE}' \
         --global-var 'overs_per_innings=5' \
         --bail folder"
    
    # Phase 6: Scoring Integrity Tests
    echo -e "\n🔐 Phase 5: Scoring Integrity & Multi-User Scenario"
    
    # Test scorer assignment
    run_newman_test "Scoring Integrity Tests" \
        "--folder 'Cricket Matches' \
         --global-var 'team_a_scorer_email=${CAPTAIN_A_EMAIL}' \
         --global-var 'team_b_scorer_email=${CAPTAIN_B_EMAIL}' \
         --global-var 'umpire_email=${UMPIRE_EMAIL}' \
         --bail folder"
    
    # Phase 7: Live Scoring Simulation
    echo -e "\n⚾ Phase 6: Live Match Simulation"
    
    # Simulate ball-by-ball scoring with multiple scorers
    run_newman_test "Multi-Scorer Ball Recording" \
        "--folder 'Cricket Matches' \
         --global-var 'over_number=1' \
         --global-var 'ball_number=1' \
         --bail folder"
    
    # Phase 8: Spectator Experience
    echo -e "\n👀 Phase 7: Spectator Experience"
    
    run_newman_test "Live Updates for Spectators" \
        "--folder 'Cricket Matches' \
         --global-var 'spectator_email=${SPECTATOR_EMAIL}' \
         --bail folder"
    
    # Phase 9: Complete Testing Report
    echo -e "\n📊 Phase 8: Generating Final Report"
    
    generate_final_report
    
    echo -e "\n🎉 All tests completed successfully!"
    echo "📂 Detailed reports available in: $RESULTS_DIR"
    echo "🌐 Open the HTML reports in your browser for detailed analysis"
}

# Function to generate final comprehensive report
generate_final_report() {
    local summary_file="$RESULTS_DIR/test_summary.md"
    
    echo "# Kreeda API Test Summary" > "$summary_file"
    echo "Generated on: $(date)" >> "$summary_file"
    echo "" >> "$summary_file"
    
    echo "## Test Configuration" >> "$summary_file"
    echo "- API Base URL: $API_BASE_URL" >> "$summary_file"
    echo "- Total Test Phases: 8" >> "$summary_file"
    echo "- Test Data Timestamp: $(date +%s)" >> "$summary_file"
    echo "" >> "$summary_file"
    
    echo "## Test Scenarios Covered" >> "$summary_file"
    echo "1. ✅ API Health Verification" >> "$summary_file"
    echo "2. ✅ Multi-User Registration (4 users)" >> "$summary_file"
    echo "3. ✅ Team Creation and Management" >> "$summary_file"
    echo "4. ✅ Match Creation and Setup" >> "$summary_file"
    echo "5. ✅ Scorer Assignment for Integrity" >> "$summary_file"
    echo "6. ✅ Multi-Scorer Ball Recording" >> "$summary_file"
    echo "7. ✅ Live Updates for Spectators" >> "$summary_file"
    echo "8. ✅ Complete Workflow Integration" >> "$summary_file"
    echo "" >> "$summary_file"
    
    echo "## Users Created in This Test" >> "$summary_file"
    echo "- **Captain A**: $CAPTAIN_A_EMAIL ($CAPTAIN_A_USERNAME)" >> "$summary_file"
    echo "- **Captain B**: $CAPTAIN_B_EMAIL ($CAPTAIN_B_USERNAME)" >> "$summary_file"
    echo "- **Umpire**: $UMPIRE_EMAIL ($UMPIRE_USERNAME)" >> "$summary_file"
    echo "- **Spectator**: $SPECTATOR_EMAIL ($SPECTATOR_USERNAME)" >> "$summary_file"
    echo "" >> "$summary_file"
    
    echo "## Teams Created" >> "$summary_file"
    echo "- **Team A**: $TEAM_A_NAME ($TEAM_A_SHORT)" >> "$summary_file"
    echo "- **Team B**: $TEAM_B_NAME ($TEAM_B_SHORT)" >> "$summary_file"
    echo "" >> "$summary_file"
    
    echo "## Match Details" >> "$summary_file"
    echo "- **Venue**: $MATCH_VENUE" >> "$summary_file"
    echo "- **Date**: $MATCH_DATE" >> "$summary_file"
    echo "- **Format**: 5 overs per innings (T5)" >> "$summary_file"
    echo "" >> "$summary_file"
    
    echo "## Files Generated" >> "$summary_file"
    ls -la "$RESULTS_DIR" | sed 's/^/- /' >> "$summary_file"
    echo "" >> "$summary_file"
    
    echo "## Next Steps" >> "$summary_file"
    echo "1. Review HTML reports for detailed request/response analysis" >> "$summary_file"
    echo "2. Check JSON reports for programmatic analysis" >> "$summary_file"
    echo "3. Verify database state for data integrity" >> "$summary_file"
    echo "4. Test with real UI integration" >> "$summary_file"
    
    echo "✅ Final report generated: $summary_file"
}

# Error handling
trap 'echo "❌ Test execution interrupted"; exit 1' INT TERM

# Run main workflow
main "$@"

echo -e "\n🎯 Testing Complete! Check the results directory for detailed reports."
echo "💡 Tip: Open the HTML files in your browser for interactive test reports."
