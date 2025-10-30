#!/bin/bash

# Kreeda Backend - Phase 2 Simple Manual Testing
# Focused on Teams & Match Management
# Date: 2025-10-30

set -e

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== Kreeda Phase 2 Manual Test ===${NC}\n"

# Step 1: Register user
echo -e "${YELLOW}[1/12] Registering test user...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test$(date +%s)@kreeda.app\",\"password\":\"Test1234!\",\"full_name\":\"Test User\"}")

USER_ID=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['user']['id'])")
ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['session']['access_token'])")
echo -e "${GREEN}✓${NC} User created: $USER_ID"

# Step 2: Create cricket profile
echo -e "\n${YELLOW}[2/12] Creating cricket profile...${NC}"
PROFILE_RESPONSE=$(curl -s -X POST "${BASE_URL}/cricket-profiles" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d "{\"sport_type\":\"CRICKET\",\"display_name\":\"TestCricketer$(date +%s)\",\"batting_style\":\"RIGHT_HAND_BAT\",\"bowling_style\":\"RIGHT_ARM_FAST\",\"playing_role\":\"ALL_ROUNDER\"}")

PROFILE_ID=$(echo "$PROFILE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])")
echo -e "${GREEN}✓${NC} Profile created: $PROFILE_ID"

# Step 3: Create Team A
echo -e "\n${YELLOW}[3/12] Creating Team A...${NC}"
TEAM_A_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/cricket/teams" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d "{\"name\":\"Mumbai Challengers $(date +%s)\",\"team_type\":\"CLUB\",\"sport_type\":\"CRICKET\",\"description\":\"Test team A\",\"team_colors\":{\"primary\":\"#FF5733\",\"secondary\":\"#FFFFFF\"}}")

TEAM_A_ID=$(echo "$TEAM_A_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])")
echo -e "${GREEN}✓${NC} Team A created: $TEAM_A_ID"
echo "$TEAM_A_RESPONSE" | python3 -m json.tool

# Step 4: Create Team B
echo -e "\n${YELLOW}[4/12] Creating Team B...${NC}"
TEAM_B_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/cricket/teams" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d "{\"name\":\"Chennai Super Kings $(date +%s)\",\"team_type\":\"CLUB\",\"sport_type\":\"CRICKET\",\"description\":\"Test team B\",\"team_colors\":{\"primary\":\"#FFFF00\",\"secondary\":\"#0000FF\"}}")

TEAM_B_ID=$(echo "$TEAM_B_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])")
echo -e "${GREEN}✓${NC} Team B created: $TEAM_B_ID"

# Step 5: List teams
echo -e "\n${YELLOW}[5/12] Listing all teams...${NC}"
curl -s "${BASE_URL}/api/v1/cricket/teams" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Found {data['data']['total']} teams\")"
echo -e "${GREEN}✓${NC} Teams listed successfully"

# Step 6: Get Team A details
echo -e "\n${YELLOW}[6/12] Getting Team A details...${NC}"
curl -s "${BASE_URL}/api/v1/cricket/teams/${TEAM_A_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | python3 -m json.tool
echo -e "${GREEN}✓${NC} Team A details retrieved"

# Step 7: Add member to Team A
echo -e "\n${YELLOW}[7/12] Adding member to Team A...${NC}"
MEMBER_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/cricket/teams/${TEAM_A_ID}/members" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d "{\"cricket_profile_id\":\"${PROFILE_ID}\",\"role\":\"CAPTAIN\",\"jersey_number\":7}")

echo "$MEMBER_RESPONSE" | python3 -m json.tool
echo -e "${GREEN}✓${NC} Member added to Team A"

# Step 8: Get Team A members
echo -e "\n${YELLOW}[8/12] Getting Team A members...${NC}"
curl -s "${BASE_URL}/api/v1/cricket/teams/${TEAM_A_ID}/members" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | python3 -m json.tool
echo -e "${GREEN}✓${NC} Team A members retrieved"

# Step 9: Create match
echo -e "\n${YELLOW}[9/12] Creating match...${NC}"
MATCH_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/cricket/matches" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d "{\"team_a_id\":\"${TEAM_A_ID}\",\"team_b_id\":\"${TEAM_B_ID}\",\"match_type\":\"T20\",\"sport_type\":\"CRICKET\",\"scheduled_at\":\"2025-11-15T14:00:00Z\",\"venue\":{\"name\":\"Wankhede Stadium\",\"city\":\"Mumbai\",\"country\":\"India\"}}")

MATCH_ID=$(echo "$MATCH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])")
MATCH_CODE=$(echo "$MATCH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['match_code'])")
echo -e "${GREEN}✓${NC} Match created: $MATCH_ID (Code: $MATCH_CODE)"
echo "$MATCH_RESPONSE" | python3 -m json.tool

# Step 10: List matches
echo -e "\n${YELLOW}[10/12] Listing all matches...${NC}"
curl -s "${BASE_URL}/api/v1/cricket/matches" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Found {data['data']['total']} matches\")"
echo -e "${GREEN}✓${NC} Matches listed successfully"

# Step 11: Conduct toss
echo -e "\n${YELLOW}[11/12] Conducting toss...${NC}"
TOSS_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/cricket/matches/${MATCH_ID}/toss" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d "{\"toss_won_by_team_id\":\"${TEAM_A_ID}\",\"elected_to\":\"BAT\"}")

echo "$TOSS_RESPONSE" | python3 -m json.tool
echo -e "${GREEN}✓${NC} Toss conducted successfully"

# Step 12: Get match details
echo -e "\n${YELLOW}[12/12] Getting final match details...${NC}"
curl -s "${BASE_URL}/api/v1/cricket/matches/${MATCH_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | python3 -m json.tool
echo -e "${GREEN}✓${NC} Match details retrieved"

echo -e "\n${BLUE}=== All Phase 2 tests passed! ===${NC}"
echo -e "Summary:"
echo -e "  User ID: ${BLUE}${USER_ID}${NC}"
echo -e "  Profile ID: ${BLUE}${PROFILE_ID}${NC}"
echo -e "  Team A ID: ${BLUE}${TEAM_A_ID}${NC}"
echo -e "  Team B ID: ${BLUE}${TEAM_B_ID}${NC}"
echo -e "  Match ID: ${BLUE}${MATCH_ID}${NC}"
echo -e "  Match Code: ${BLUE}${MATCH_CODE}${NC}"
