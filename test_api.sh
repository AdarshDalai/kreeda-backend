#!/bin/bash

# Comprehensive test script for Kreeda Backend API
BASE_URL="http://localhost:8000"

echo "🚀 Testing Kreeda Backend API Endpoints"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Function to run test
run_test() {
    local test_name="$1"
    local curl_command="$2"
    local expected_pattern="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "\n${YELLOW}Test $TESTS_RUN: $test_name${NC}"
    
    response=$(eval "$curl_command" 2>/dev/null)
    
    if echo "$response" | grep -q "$expected_pattern"; then
        echo -e "${GREEN}✅ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "Response: $response"
    fi
}

# 1. Health Check
run_test "Health Check" \
    "curl -s $BASE_URL/health" \
    "healthy"

# 2. User Registration
echo -e "\n${YELLOW}Registering test user...${NC}"
TIMESTAMP=$(date +%s)
TEST_EMAIL="test-complete-${TIMESTAMP}@example.com"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"testpassword123\",
    \"phone_number\": \"+1234567890\"
  }")

TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['session']['access_token'])" 2>/dev/null)

run_test "User Registration" \
    "echo '$REGISTER_RESPONSE'" \
    "access_token"

# 3. User Login
run_test "User Login" \
    "curl -s -X POST '$BASE_URL/auth/login' -H 'Content-Type: application/json' -d '{\"email\": \"$TEST_EMAIL\", \"password\": \"testpassword123\"}'" \
    "access_token"

# 4. Anonymous User Creation
run_test "Anonymous User Creation" \
    "curl -s -X POST '$BASE_URL/auth/signin/anonymous' -H 'Content-Type: application/json' -d '{\"options\": {\"data\": {\"anonymous\": true}}}'" \
    "anonymous"

# 5. OTP Request
run_test "OTP Request" \
    "curl -s -X POST '$BASE_URL/auth/signin/otp' -H 'Content-Type: application/json' -d '{\"email\": \"otp-test@example.com\"}'" \
    "OTP sent successfully"

# 6. OTP Verification
run_test "OTP Verification" \
    "curl -s -X POST '$BASE_URL/auth/verify' -H 'Content-Type: application/json' -d '{\"email\": \"otp-test@example.com\", \"token\": \"123456\", \"type\": \"email\"}'" \
    "access_token"

# 7. Get User Info (requires token)
if [ -n "$TOKEN" ]; then
    run_test "Get User Info" \
        "curl -s -X GET '$BASE_URL/auth/user' -H 'Authorization: Bearer $TOKEN'" \
        "$TEST_EMAIL"

    # 8. Update User Profile
    run_test "Update User Profile" \
        "curl -s -X PUT '$BASE_URL/user/profile/' -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' -d '{\"name\": \"Test User\", \"bio\": \"Test bio\", \"location\": \"Test City\"}'" \
        "Test User"

    # 9. Get User Profile
    run_test "Get User Profile" \
        "curl -s -X GET '$BASE_URL/user/profile/' -H 'Authorization: Bearer $TOKEN'" \
        "Test User"

    # 10. Sign Out
    run_test "User Sign Out" \
        "curl -s -X POST '$BASE_URL/auth/signout' -H 'Authorization: Bearer $TOKEN'" \
        "Signed out successfully"
else
    echo -e "${RED}❌ Cannot run authenticated tests - no token available${NC}"
fi

# Test duplicate registration
run_test "Duplicate Registration (Should Fail)" \
    "curl -s -X POST '$BASE_URL/auth/register' -H 'Content-Type: application/json' -d '{\"email\": \"$TEST_EMAIL\", \"password\": \"newpassword\"}'" \
    "already registered"

# Summary
echo -e "\n${YELLOW}Test Summary${NC}"
echo "============"
echo -e "Tests run: $TESTS_RUN"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$((TESTS_RUN - TESTS_PASSED))${NC}"

if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed${NC}"
    exit 1
fi