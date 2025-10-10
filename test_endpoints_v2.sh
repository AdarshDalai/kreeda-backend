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
health_response=$(curl -s "${BASE_URL}/health")
echo "$health_response" | jq '.' 2>/dev/null || echo "$health_response"

if echo "$health_response" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
fi
echo

# Test 2: Register User
echo -e "${YELLOW}2. Testing User Registration (POST /auth/register)${NC}"
register_response=$(curl -s -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@kreeda.com",
    "password": "SecurePass@123",
    "phone_number": "+19876543210",
    "name": "Test User"
  }')

echo "$register_response" | jq '.' 2>/dev/null || echo "$register_response"

access_token=$(echo "$register_response" | jq -r '.session.access_token' 2>/dev/null)
refresh_token=$(echo "$register_response" | jq -r '.session.refresh_token' 2>/dev/null)
user_id=$(echo "$register_response" | jq -r '.user.id' 2>/dev/null)

if [ "$access_token" != "null" ] && [ -n "$access_token" ]; then
    echo -e "${GREEN}✓ User registration successful${NC}"
    echo -e "  User ID: $user_id"
else
    echo -e "${RED}✗ User registration failed${NC}"
fi
echo

# Test 3: Login 
echo -e "${YELLOW}3. Testing Login (POST /auth/signin/password)${NC}"
login_response=$(curl -s -X POST "${BASE_URL}/auth/signin/password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@kreeda.com",
    "password": "SecurePass@123"
  }')

echo "$login_response" | jq '.' 2>/dev/null || echo "$login_response"

login_token=$(echo "$login_response" | jq -r '.session.access_token' 2>/dev/null)
if [ "$login_token" != "null" ] && [ -n "$login_token" ]; then
    echo -e "${GREEN}✓ Login successful${NC}"
    access_token="$login_token"
    refresh_token=$(echo "$login_response" | jq -r '.session.refresh_token' 2>/dev/null)
else
    echo -e "${YELLOW}Using registration token if login failed${NC}"
fi
echo

# Test 4: Get Current User
echo -e "${YELLOW}4. Testing Get Current User (GET /auth/user)${NC}"
user_response=$(curl -s -X GET "${BASE_URL}/auth/user" \
  -H "Authorization: Bearer ${access_token}")

echo "$user_response" | jq '.' 2>/dev/null || echo "$user_response"

if echo "$user_response" | grep -q "email"; then
    echo -e "${GREEN}✓ Get current user successful${NC}"
else
    echo -e "${RED}✗ Get current user failed${NC}"
fi
echo

# Test 5: Get User Profile  
echo -e "${YELLOW}5. Testing Get User Profile (GET /user/profile/)${NC}"
profile_response=$(curl -s -X GET "${BASE_URL}/user/profile/" \
  -H "Authorization: Bearer ${access_token}")

echo "$profile_response" | jq '.' 2>/dev/null || echo "$profile_response"

if echo "$profile_response" | grep -q "name"; then
    echo -e "${GREEN}✓ Get user profile successful${NC}"
else
    echo -e "${YELLOW}Note: Profile might not exist yet${NC}"
fi
echo

# Test 6: Update User Profile
echo -e "${YELLOW}6. Testing Update User Profile (PUT /user/profile/${user_id})${NC}"
update_response=$(curl -s -X PUT "${BASE_URL}/user/profile/${user_id}" \
  -H "Authorization: Bearer ${access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Test User",
    "bio": "This is my updated bio",
    "location": "San Francisco, CA"
  }')

echo "$update_response" | jq '.' 2>/dev/null || echo "$update_response"

if echo "$update_response" | grep -q "Updated Test User"; then
    echo -e "${GREEN}✓ Update user profile successful${NC}"
else
    echo -e "${RED}✗ Update user profile failed${NC}"
fi
echo

# Test 7: Refresh Access Token
echo -e "${YELLOW}7. Testing Refresh Token (POST /auth/token)${NC}"
refresh_response=$(curl -s -X POST "${BASE_URL}/auth/token" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"${refresh_token}\"
  }")

echo "$refresh_response" | jq '.' 2>/dev/null || echo "$refresh_response"

new_access_token=$(echo "$refresh_response" | jq -r '.session.access_token' 2>/dev/null)
if [ "$new_access_token" != "null" ] && [ -n "$new_access_token" ]; then
    echo -e "${GREEN}✓ Refresh token successful${NC}"
    access_token="$new_access_token"
else
    echo -e "${RED}✗ Refresh token failed${NC}"
fi
echo

# Test 8: Send OTP
echo -e "${YELLOW}8. Testing Send OTP (POST /auth/signin/otp)${NC}"
otp_response=$(curl -s -X POST "${BASE_URL}/auth/signin/otp" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+19876543210"
  }')

echo "$otp_response" | jq '.' 2>/dev/null || echo "$otp_response"

if echo "$otp_response" | grep -q "OTP\|sent\|success"; then
    echo -e "${GREEN}✓ Send OTP successful${NC}"
else
    echo -e "${YELLOW}Note: OTP response received${NC}"
fi
echo

# Test 9: Request Password Recovery
echo -e "${YELLOW}9. Testing Request Password Recovery (POST /auth/recover)${NC}"
recover_response=$(curl -s -X POST "${BASE_URL}/auth/recover" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@kreeda.com"
  }')

echo "$recover_response" | jq '.' 2>/dev/null || echo "$recover_response"

if echo "$recover_response" | grep -q "reset\|sent\|success\|message"; then
    echo -e "${GREEN}✓ Request password recovery successful${NC}"
else
    echo -e "${YELLOW}Note: Recovery response received${NC}"
fi
echo

# Test 10: Resend Verification Email
echo -e "${YELLOW}10. Testing Resend Verification Email (POST /auth/resend-verification)${NC}"
resend_response=$(curl -s -X POST "${BASE_URL}/auth/resend-verification" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@kreeda.com"
  }')

echo "$resend_response" | jq '.' 2>/dev/null || echo "$resend_response"

if echo "$resend_response" | grep -q "verification\|sent\|success\|message"; then
    echo -e "${GREEN}✓ Resend verification email successful${NC}"
else
    echo -e "${YELLOW}Note: Resend response received${NC}"
fi
echo

# Test 11: Logout
echo -e "${YELLOW}11. Testing Logout (POST /auth/signout)${NC}"
logout_response=$(curl -s -X POST "${BASE_URL}/auth/signout" \
  -H "Authorization: Bearer ${access_token}")

echo "$logout_response" | jq '.' 2>/dev/null || echo "$logout_response"

if echo "$logout_response" | grep -q "success\|logout\|signout"; then
    echo -e "${GREEN}✓ Logout successful${NC}"
else
    echo -e "${YELLOW}Note: Logout response received${NC}"
fi
echo

# Test 12: Anonymous Sign In
echo -e "${YELLOW}12. Testing Anonymous Sign In (POST /auth/signin/anonymous)${NC}"
anon_response=$(curl -s -X POST "${BASE_URL}/auth/signin/anonymous")

echo "$anon_response" | jq '.' 2>/dev/null || echo "$anon_response"

anon_token=$(echo "$anon_response" | jq -r '.session.access_token' 2>/dev/null)
if [ "$anon_token" != "null" ] && [ -n "$anon_token" ]; then
    echo -e "${GREEN}✓ Anonymous sign in successful${NC}"
else
    echo -e "${YELLOW}Note: Anonymous sign in response received${NC}"
fi
echo

echo -e "${YELLOW}=== Testing Complete ===${NC}"
echo -e "\n${YELLOW}API Documentation available at:${NC}"
echo -e "  ${GREEN}http://localhost:8000/api/docs${NC}"
echo -e "  ${GREEN}http://localhost:8000/api/redoc${NC}"
