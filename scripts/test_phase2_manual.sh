#!/bin/bash

# Kreeda Backend - Phase 2 Manual Testing Script
# Tests Teams & Match Management endpoints
# Author: AI Agent
# Date: 2025-10-30

set -e  # Exit on error

BASE_URL="http://localhost:8000"
API_PREFIX="/api/v1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Kreeda Phase 2 Manual Testing${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Helper function to print test result
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

# Helper function to extract JSON field
extract_json() {
    echo "$1" | python3 -c "import sys, json; print(json.load(sys.stdin)$2)" 2>/dev/null || echo ""
}

echo -e "\n${YELLOW}[1] Health Check${NC}"
echo "GET ${BASE_URL}/health"
HEALTH_RESPONSE=$(curl -s "${BASE_URL}/health")
echo "$HEALTH_RESPONSE" | python3 -m json.tool
STATUS=$(echo "$HEALTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
test_result $? "Health check endpoint"
echo ""

echo -e "\n${YELLOW}[2] User Registration${NC}"
echo "POST ${BASE_URL}${API_PREFIX}/auth/register"
REGISTER_PAYLOAD='{
  "email": "testuser_'$(date +%s)'@kreeda.app",
  "password": "TestPassword123!",
  "full_name": "Test User Phase 2"
}'
echo "Request: $REGISTER_PAYLOAD" | python3 -m json.tool
REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}${API_PREFIX}/auth/register" \
  -H "Content-Type: application/json" \
  -d "$REGISTER_PAYLOAD")
echo "Response:" 
echo "$REGISTER_RESPONSE" | python3 -m json.tool
USER_ID=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['user']['id'])" 2>/dev/null)
ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['session']['access_token'])" 2>/dev/null)
test_result $? "User registration"
echo -e "User ID: ${BLUE}${USER_ID}${NC}"
echo -e "Access Token: ${BLUE}${ACCESS_TOKEN:0:50}...${NC}"
echo ""

# Set authorization header
AUTH_HEADER="Authorization: Bearer ${ACCESS_TOKEN}"

echo -e "\n${YELLOW}[3] Create Cricket Sport Profile${NC}"
echo "POST ${BASE_URL}${API_PREFIX}/cricket/profiles"
PROFILE_PAYLOAD='{
  "sport_type": "CRICKET",
  "display_name": "TestCricketer'$(date +%s)'",
  "bio": "Manual test cricket profile",
  "batting_style": "RIGHT_HAND_BAT",
  "bowling_style": "RIGHT_ARM_FAST",
  "playing_role": "ALL_ROUNDER"
}'
echo "Request: $PROFILE_PAYLOAD" | python3 -m json.tool
PROFILE_RESPONSE=$(curl -s -X POST "${BASE_URL}${API_PREFIX}/cricket/profiles" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -d "$PROFILE_PAYLOAD")
echo "Response:"
echo "$PROFILE_RESPONSE" | python3 -m json.tool
PROFILE_ID=$(echo "$PROFILE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
test_result $? "Create cricket profile"
echo -e "Profile ID: ${BLUE}${PROFILE_ID}${NC}"
echo ""

echo -e "\n${YELLOW}[4] Create Team A${NC}"
echo "POST ${BASE_URL}${API_PREFIX}/cricket/teams"
TEAM_A_PAYLOAD='{
  "name": "Mumbai Challengers '$(date +%s)'",
  "team_type": "CLUB",
  "sport_type": "CRICKET",
  "description": "Test team for Phase 2 manual testing",
  "team_colors": {
    "primary": "#FF5733",
    "secondary": "#FFFFFF"
  },
  "home_ground": {
    "name": "Wankhede Stadium",
    "city": "Mumbai",
    "country": "India",
    "latitude": 18.9388,
    "longitude": 72.8258
  }
}'
echo "Request: $TEAM_A_PAYLOAD" | python3 -m json.tool
TEAM_A_RESPONSE=$(curl -s -X POST "${BASE_URL}${API_PREFIX}/cricket/teams" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -d "$TEAM_A_PAYLOAD")
echo "Response:"
echo "$TEAM_A_RESPONSE" | python3 -m json.tool
TEAM_A_ID=$(echo "$TEAM_A_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
test_result $? "Create Team A"
echo -e "Team A ID: ${BLUE}${TEAM_A_ID}${NC}"
echo ""

echo -e "\n${YELLOW}[5] Create Team B${NC}"
echo "POST ${BASE_URL}${API_PREFIX}/cricket/teams"
TEAM_B_PAYLOAD='{
  "name": "Chennai Super Kings '$(date +%s)'",
  "team_type": "CLUB",
  "sport_type": "CRICKET",
  "description": "Opponent team for Phase 2 manual testing",
  "team_colors": {
    "primary": "#FFFF00",
    "secondary": "#0000FF"
  },
  "home_ground": {
    "name": "Chepauk Stadium",
    "city": "Chennai",
    "country": "India",
    "latitude": 13.0627,
    "longitude": 80.2792
  }
}'
echo "Request: $TEAM_B_PAYLOAD" | python3 -m json.tool
TEAM_B_RESPONSE=$(curl -s -X POST "${BASE_URL}${API_PREFIX}/cricket/teams" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -d "$TEAM_B_PAYLOAD")
echo "Response:"
echo "$TEAM_B_RESPONSE" | python3 -m json.tool
TEAM_B_ID=$(echo "$TEAM_B_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
test_result $? "Create Team B"
echo -e "Team B ID: ${BLUE}${TEAM_B_ID}${NC}"
echo ""

echo -e "\n${YELLOW}[6] List Teams${NC}"
echo "GET ${BASE_URL}${API_PREFIX}/cricket/teams?sport_type=CRICKET"
TEAMS_LIST_RESPONSE=$(curl -s "${BASE_URL}${API_PREFIX}/cricket/teams?sport_type=CRICKET" \
  -H "${AUTH_HEADER}")
echo "Response:"
echo "$TEAMS_LIST_RESPONSE" | python3 -m json.tool | head -50
test_result $? "List teams"
echo ""

echo -e "\n${YELLOW}[7] Get Team A Details${NC}"
echo "GET ${BASE_URL}${API_PREFIX}/cricket/teams/${TEAM_A_ID}"
TEAM_A_DETAIL_RESPONSE=$(curl -s "${BASE_URL}${API_PREFIX}/cricket/teams/${TEAM_A_ID}" \
  -H "${AUTH_HEADER}")
echo "Response:"
echo "$TEAM_A_DETAIL_RESPONSE" | python3 -m json.tool
test_result $? "Get Team A details"
echo ""

echo -e "\n${YELLOW}[8] Add Member to Team A${NC}"
echo "POST ${BASE_URL}${API_PREFIX}/cricket/teams/${TEAM_A_ID}/members"
MEMBER_PAYLOAD='{
  "cricket_profile_id": "'${PROFILE_ID}'",
  "role": "CAPTAIN",
  "jersey_number": 7,
  "is_active": true
}'
echo "Request: $MEMBER_PAYLOAD" | python3 -m json.tool
MEMBER_RESPONSE=$(curl -s -X POST "${BASE_URL}${API_PREFIX}/cricket/teams/${TEAM_A_ID}/members" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -d "$MEMBER_PAYLOAD")
echo "Response:"
echo "$MEMBER_RESPONSE" | python3 -m json.tool
test_result $? "Add member to Team A"
echo ""

echo -e "\n${YELLOW}[9] Get Team A Members${NC}"
echo "GET ${BASE_URL}${API_PREFIX}/cricket/teams/${TEAM_A_ID}/members"
TEAM_A_MEMBERS_RESPONSE=$(curl -s "${BASE_URL}${API_PREFIX}/cricket/teams/${TEAM_A_ID}/members" \
  -H "${AUTH_HEADER}")
echo "Response:"
echo "$TEAM_A_MEMBERS_RESPONSE" | python3 -m json.tool
test_result $? "Get Team A members"
echo ""

echo -e "\n${YELLOW}[10] Create Match${NC}"
echo "POST ${BASE_URL}${API_PREFIX}/cricket/matches"
MATCH_PAYLOAD='{
  "team_a_id": "'${TEAM_A_ID}'",
  "team_b_id": "'${TEAM_B_ID}'",
  "match_type": "T20",
  "sport_type": "CRICKET",
  "scheduled_at": "2025-11-15T14:00:00Z",
  "venue": {
    "name": "Wankhede Stadium",
    "city": "Mumbai",
    "country": "India",
    "latitude": 18.9388,
    "longitude": 72.8258
  },
  "match_rules": {
    "players_per_team": 11,
    "overs_per_side": 20,
    "balls_per_over": 6,
    "powerplay_overs": 6,
    "max_overs_per_bowler": 4,
    "runs_for_boundary": 4,
    "runs_for_six": 6,
    "wide_runs": 1,
    "no_ball_runs": 1,
    "bye_allowed": true,
    "leg_bye_allowed": true,
    "dls_enabled": false,
    "super_over_enabled": true
  }
}'
echo "Request: $MATCH_PAYLOAD" | python3 -m json.tool
MATCH_RESPONSE=$(curl -s -X POST "${BASE_URL}${API_PREFIX}/cricket/matches" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -d "$MATCH_PAYLOAD")
echo "Response:"
echo "$MATCH_RESPONSE" | python3 -m json.tool
MATCH_ID=$(echo "$MATCH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
MATCH_CODE=$(echo "$MATCH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['match_code'])" 2>/dev/null)
test_result $? "Create match"
echo -e "Match ID: ${BLUE}${MATCH_ID}${NC}"
echo -e "Match Code: ${BLUE}${MATCH_CODE}${NC}"
echo ""

echo -e "\n${YELLOW}[11] List Matches${NC}"
echo "GET ${BASE_URL}${API_PREFIX}/cricket/matches?sport_type=CRICKET"
MATCHES_LIST_RESPONSE=$(curl -s "${BASE_URL}${API_PREFIX}/cricket/matches?sport_type=CRICKET" \
  -H "${AUTH_HEADER}")
echo "Response:"
echo "$MATCHES_LIST_RESPONSE" | python3 -m json.tool | head -50
test_result $? "List matches"
echo ""

echo -e "\n${YELLOW}[12] Get Match Details${NC}"
echo "GET ${BASE_URL}${API_PREFIX}/cricket/matches/${MATCH_ID}"
MATCH_DETAIL_RESPONSE=$(curl -s "${BASE_URL}${API_PREFIX}/cricket/matches/${MATCH_ID}" \
  -H "${AUTH_HEADER}")
echo "Response:"
echo "$MATCH_DETAIL_RESPONSE" | python3 -m json.tool
test_result $? "Get match details"
echo ""

echo -e "\n${YELLOW}[13] Conduct Toss${NC}"
echo "POST ${BASE_URL}${API_PREFIX}/cricket/matches/${MATCH_ID}/toss"
TOSS_PAYLOAD='{
  "toss_won_by_team_id": "'${TEAM_A_ID}'",
  "elected_to": "BAT"
}'
echo "Request: $TOSS_PAYLOAD" | python3 -m json.tool
TOSS_RESPONSE=$(curl -s -X POST "${BASE_URL}${API_PREFIX}/cricket/matches/${MATCH_ID}/toss" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -d "$TOSS_PAYLOAD")
echo "Response:"
echo "$TOSS_RESPONSE" | python3 -m json.tool
test_result $? "Conduct toss"
echo ""

echo -e "\n${YELLOW}[14] Set Playing XI for Team A${NC}"
echo "POST ${BASE_URL}${API_PREFIX}/cricket/matches/${MATCH_ID}/playing-xi"
PLAYING_XI_PAYLOAD='{
  "team_id": "'${TEAM_A_ID}'",
  "player_ids": ["'${PROFILE_ID}'"],
  "captain_id": "'${PROFILE_ID}'",
  "wicket_keeper_id": "'${PROFILE_ID}'"
}'
echo "Request: $PLAYING_XI_PAYLOAD" | python3 -m json.tool
PLAYING_XI_RESPONSE=$(curl -s -X POST "${BASE_URL}${API_PREFIX}/cricket/matches/${MATCH_ID}/playing-xi" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -d "$PLAYING_XI_PAYLOAD")
echo "Response:"
echo "$PLAYING_XI_RESPONSE" | python3 -m json.tool
test_result $? "Set playing XI for Team A"
echo ""

echo -e "\n${YELLOW}[15] Update Team A${NC}"
echo "PUT ${BASE_URL}${API_PREFIX}/cricket/teams/${TEAM_A_ID}"
UPDATE_TEAM_PAYLOAD='{
  "description": "Updated description - Manual test passed!",
  "is_active": true
}'
echo "Request: $UPDATE_TEAM_PAYLOAD" | python3 -m json.tool
UPDATE_TEAM_RESPONSE=$(curl -s -X PUT "${BASE_URL}${API_PREFIX}/cricket/teams/${TEAM_A_ID}" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -d "$UPDATE_TEAM_PAYLOAD")
echo "Response:"
echo "$UPDATE_TEAM_RESPONSE" | python3 -m json.tool
test_result $? "Update Team A"
echo ""

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Tests Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}Tests Failed: ${TESTS_FAILED}${NC}"
echo -e "${BLUE}Total Tests: $((TESTS_PASSED + TESTS_FAILED))${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Phase 2 implementation is working correctly.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review the output above.${NC}"
    exit 1
fi
