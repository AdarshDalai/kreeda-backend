#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"

echo -e "${YELLOW}=== Testing Kreeda Backend API ===${NC}\n"

# Test 1: Health Check
echo -e "${YELLOW}1. Testing Health Check${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
if [ "$response" -eq 200 ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed (HTTP $response)${NC}"
fi
echo

# Test 2: Register User
echo -e "${YELLOW}2. Testing User Registration${NC}"
register_response=$(curl -s -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test@123456",
    "phone_number": "+1234567890",
    "name": "Test User"
  }')

echo "$register_response" | jq '.' 2>/dev/null || echo "$register_response"

access_token=$(echo "$register_response" | jq -r '.access_token' 2>/dev/null)
refresh_token=$(echo "$register_response" | jq -r '.refresh_token' 2>/dev/null)

if [ "$access_token" != "null" ] && [ -n "$access_token" ]; then
    echo -e "${GREEN}✓ User registration successful${NC}"
else
    echo -e "${RED}✗ User registration failed${NC}"
fi
echo

# Test 3: Login (duplicate - should show user exists)
echo -e "${YELLOW}3. Testing Login with Same User${NC}"
login_response=$(curl -s -X POST "${BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test@123456"
  }')

echo "$login_response" | jq '.' 2>/dev/null || echo "$login_response"

login_token=$(echo "$login_response" | jq -r '.access_token' 2>/dev/null)
if [ "$login_token" != "null" ] && [ -n "$login_token" ]; then
    echo -e "${GREEN}✓ Login successful${NC}"
    access_token="$login_token"
    refresh_token=$(echo "$login_response" | jq -r '.refresh_token' 2>/dev/null)
else
    echo -e "${YELLOW}Note: User might already exist, continuing with previous token${NC}"
fi
echo

# Test 4: Get Current User
echo -e "${YELLOW}4. Testing Get Current User${NC}"
user_response=$(curl -s -X GET "${BASE_URL}/auth/me" \
  -H "Authorization: Bearer ${access_token}")

echo "$user_response" | jq '.' 2>/dev/null || echo "$user_response"

if echo "$user_response" | grep -q "email"; then
    echo -e "${GREEN}✓ Get current user successful${NC}"
else
    echo -e "${RED}✗ Get current user failed${NC}"
fi
echo

# Test 5: Get User Profile
echo -e "${YELLOW}5. Testing Get User Profile${NC}"
user_id=$(echo "$user_response" | jq -r '.user_id' 2>/dev/null)

profile_response=$(curl -s -X GET "${BASE_URL}/users/${user_id}" \
  -H "Authorization: Bearer ${access_token}")

echo "$profile_response" | jq '.' 2>/dev/null || echo "$profile_response"

if echo "$profile_response" | grep -q "name"; then
    echo -e "${GREEN}✓ Get user profile successful${NC}"
else
    echo -e "${RED}✗ Get user profile failed${NC}"
fi
echo

# Test 6: Update User Profile
echo -e "${YELLOW}6. Testing Update User Profile${NC}"
update_response=$(curl -s -X PUT "${BASE_URL}/users/${user_id}" \
  -H "Authorization: Bearer ${access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Test User",
    "bio": "This is my updated bio"
  }')

echo "$update_response" | jq '.' 2>/dev/null || echo "$update_response"

if echo "$update_response" | grep -q "Updated Test User"; then
    echo -e "${GREEN}✓ Update user profile successful${NC}"
else
    echo -e "${RED}✗ Update user profile failed${NC}"
fi
echo

# Test 7: Refresh Access Token
echo -e "${YELLOW}7. Testing Refresh Token${NC}"
refresh_response=$(curl -s -X POST "${BASE_URL}/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"${refresh_token}\"
  }")

echo "$refresh_response" | jq '.' 2>/dev/null || echo "$refresh_response"

new_access_token=$(echo "$refresh_response" | jq -r '.access_token' 2>/dev/null)
if [ "$new_access_token" != "null" ] && [ -n "$new_access_token" ]; then
    echo -e "${GREEN}✓ Refresh token successful${NC}"
    access_token="$new_access_token"
else
    echo -e "${RED}✗ Refresh token failed${NC}"
fi
echo

# Test 8: Send OTP
echo -e "${YELLOW}8. Testing Send OTP${NC}"
otp_response=$(curl -s -X POST "${BASE_URL}/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890"
  }')

echo "$otp_response" | jq '.' 2>/dev/null || echo "$otp_response"

if echo "$otp_response" | grep -q "OTP sent"; then
    echo -e "${GREEN}✓ Send OTP successful${NC}"
else
    echo -e "${RED}✗ Send OTP failed${NC}"
fi
echo

# Test 9: Request Password Reset
echo -e "${YELLOW}9. Testing Request Password Reset${NC}"
reset_request_response=$(curl -s -X POST "${BASE_URL}/auth/password-reset/request" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com"
  }')

echo "$reset_request_response" | jq '.' 2>/dev/null || echo "$reset_request_response"

if echo "$reset_request_response" | grep -q "reset"; then
    echo -e "${GREEN}✓ Request password reset successful${NC}"
else
    echo -e "${RED}✗ Request password reset failed${NC}"
fi
echo

# Test 10: Update User (with auth)
echo -e "${YELLOW}10. Testing Update User Details${NC}"
update_user_response=$(curl -s -X PUT "${BASE_URL}/auth/update" \
  -H "Authorization: Bearer ${access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Final Test User",
    "phone_number": "+9876543210"
  }')

echo "$update_user_response" | jq '.' 2>/dev/null || echo "$update_user_response"

if echo "$update_user_response" | grep -q "Final Test User"; then
    echo -e "${GREEN}✓ Update user details successful${NC}"
else
    echo -e "${RED}✗ Update user details failed${NC}"
fi
echo

# Test 11: Logout
echo -e "${YELLOW}11. Testing Logout${NC}"
logout_response=$(curl -s -X POST "${BASE_URL}/auth/logout" \
  -H "Authorization: Bearer ${access_token}" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"${refresh_token}\"
  }")

echo "$logout_response" | jq '.' 2>/dev/null || echo "$logout_response"

if echo "$logout_response" | grep -q "success"; then
    echo -e "${GREEN}✓ Logout successful${NC}"
else
    echo -e "${RED}✗ Logout failed${NC}"
fi
echo

# Test 12: Try using token after logout (should fail)
echo -e "${YELLOW}12. Testing Token After Logout (should fail)${NC}"
after_logout_response=$(curl -s -X GET "${BASE_URL}/auth/me" \
  -H "Authorization: Bearer ${access_token}")

echo "$after_logout_response" | jq '.' 2>/dev/null || echo "$after_logout_response"

if echo "$after_logout_response" | grep -q "Invalid\|expired\|Unauthorized"; then
    echo -e "${GREEN}✓ Token correctly invalidated after logout${NC}"
else
    echo -e "${YELLOW}Note: Token might still be valid (check Redis expiry)${NC}"
fi
echo

echo -e "${YELLOW}=== Testing Complete ===${NC}"
