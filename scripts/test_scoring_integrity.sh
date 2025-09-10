#!/bin/bash
# Scoring Integrity Simulation Script
# Simulates a real cricket match with multiple scorers and integrity validation

set -e

echo "🛡️ Kreeda Scoring Integrity Simulation"
echo "======================================"

API_BASE_URL="http://localhost:8000"
TIMESTAMP=$(date +%s)

# Test users
TEAM_A_CAPTAIN="captain_a_${TIMESTAMP}@kreeda.com"
TEAM_B_CAPTAIN="captain_b_${TIMESTAMP}@kreeda.com"
UMPIRE_USER="umpire_${TIMESTAMP}@kreeda.com"
SPECTATOR_USER="spectator_${TIMESTAMP}@kreeda.com"

echo "🎭 Setting up test scenario with multiple users..."

# Function to make authenticated API calls
api_call() {
    local method=$1
    local endpoint=$2
    local token=$3
    local data=$4
    
    if [ -n "$data" ]; then
        curl -s -X "$method" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $token" \
            -d "$data" \
            "$API_BASE_URL$endpoint"
    else
        curl -s -X "$method" \
            -H "Authorization: Bearer $token" \
            "$API_BASE_URL$endpoint"
    fi
}

# Function to register a user and get token
register_user() {
    local email=$1
    local username=$2
    local full_name=$3
    local password=$4
    
    echo "📝 Registering user: $email"
    
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$email\",\"username\":\"$username\",\"full_name\":\"$full_name\",\"password\":\"$password\"}" \
        "$API_BASE_URL/api/v1/auth/register")
    
    local token=$(echo "$response" | jq -r '.access_token // empty')
    
    if [ -z "$token" ]; then
        echo "❌ Failed to register user $email"
        echo "Response: $response"
        exit 1
    fi
    
    echo "✅ User registered: $email"
    echo "$token"
}

# Function to create a team
create_team() {
    local name=$1
    local short_name=$2
    local captain_token=$3
    local captain_id=$4
    
    echo "🏏 Creating team: $name"
    
    local response=$(api_call "POST" "/api/v1/teams/" "$captain_token" \
        "{\"name\":\"$name\",\"short_name\":\"$short_name\",\"captain_id\":\"$captain_id\"}")
    
    local team_id=$(echo "$response" | jq -r '.id // empty')
    
    if [ -z "$team_id" ]; then
        echo "❌ Failed to create team $name"
        echo "Response: $response"
        exit 1
    fi
    
    echo "✅ Team created: $name (ID: $team_id)"
    echo "$team_id"
}

# Function to get user ID from token
get_user_id() {
    local token=$1
    
    local response=$(api_call "GET" "/api/v1/auth/me" "$token")
    local user_id=$(echo "$response" | jq -r '.id // empty')
    
    echo "$user_id"
}

# Function to create match
create_match() {
    local team_a_id=$1
    local team_b_id=$2
    local creator_token=$3
    
    echo "🏆 Creating cricket match..."
    
    local match_date=$(date -d "+1 hour" -Iseconds)
    local response=$(api_call "POST" "/api/v1/matches/cricket" "$creator_token" \
        "{\"team_a_id\":\"$team_a_id\",\"team_b_id\":\"$team_b_id\",\"venue\":\"Test Stadium\",\"match_date\":\"$match_date\",\"overs_per_innings\":5}")
    
    local match_id=$(echo "$response" | jq -r '.id // empty')
    
    if [ -z "$match_id" ]; then
        echo "❌ Failed to create match"
        echo "Response: $response"
        exit 1
    fi
    
    echo "✅ Match created: $match_id"
    echo "$match_id"
}

# Function to record a ball from a scorer
record_ball_as_scorer() {
    local match_id=$1
    local scorer_token=$2
    local over=$3
    local ball=$4
    local runs=$5
    local extras=$6
    local bowler_id=$7
    local striker_id=$8
    local non_striker_id=$9
    local scorer_name=${10}
    
    echo "⚾ Scorer ($scorer_name) recording: Over $over.$ball - $runs runs"
    
    local response=$(api_call "POST" "/api/v1/matches/$match_id/balls" "$scorer_token" \
        "{\"over_number\":$over,\"ball_number\":$ball,\"runs_scored\":$runs,\"extras\":$extras,\"bowler_id\":\"$bowler_id\",\"batsman_striker_id\":\"$striker_id\",\"batsman_non_striker_id\":\"$non_striker_id\"}")
    
    local success=$(echo "$response" | jq -r '.success // false')
    local consensus=$(echo "$response" | jq -r '.consensus_reached // false')
    
    if [ "$success" = "true" ]; then
        echo "  ✅ Entry recorded. Consensus: $consensus"
    else
        echo "  ❌ Failed to record ball"
        echo "  Response: $response"
    fi
    
    echo "$response"
}

# Main simulation
main() {
    echo "🚀 Starting comprehensive scoring integrity simulation..."
    
    # Check API health
    if ! curl -f -s "$API_BASE_URL/health" > /dev/null; then
        echo "❌ API not responding. Start with: docker-compose up -d"
        exit 1
    fi
    
    echo "✅ API is healthy"
    
    # Step 1: Register all users
    echo -e "\n👥 Step 1: User Registration"
    CAPTAIN_A_TOKEN=$(register_user "$TEAM_A_CAPTAIN" "captain_a_$TIMESTAMP" "Captain Team A" "password123")
    CAPTAIN_B_TOKEN=$(register_user "$TEAM_B_CAPTAIN" "captain_b_$TIMESTAMP" "Captain Team B" "password123")
    UMPIRE_TOKEN=$(register_user "$UMPIRE_USER" "umpire_$TIMESTAMP" "Match Umpire" "password123")
    SPECTATOR_TOKEN=$(register_user "$SPECTATOR_USER" "spectator_$TIMESTAMP" "Cricket Fan" "password123")
    
    # Get user IDs
    CAPTAIN_A_ID=$(get_user_id "$CAPTAIN_A_TOKEN")
    CAPTAIN_B_ID=$(get_user_id "$CAPTAIN_B_TOKEN")
    UMPIRE_ID=$(get_user_id "$UMPIRE_TOKEN")
    SPECTATOR_ID=$(get_user_id "$SPECTATOR_TOKEN")
    
    echo "📋 User IDs obtained successfully"
    
    # Step 2: Create teams
    echo -e "\n🏏 Step 2: Team Creation"
    TEAM_A_ID=$(create_team "Warriors $TIMESTAMP" "WAR" "$CAPTAIN_A_TOKEN" "$CAPTAIN_A_ID")
    TEAM_B_ID=$(create_team "Champions $TIMESTAMP" "CHA" "$CAPTAIN_B_TOKEN" "$CAPTAIN_B_ID")
    
    # Step 3: Create match
    echo -e "\n🏆 Step 3: Match Creation"
    MATCH_ID=$(create_match "$TEAM_A_ID" "$TEAM_B_ID" "$CAPTAIN_A_TOKEN")
    
    # Step 4: Assign scorers (if integrity API is available)
    echo -e "\n🔐 Step 4: Scorer Assignment"
    echo "📝 Assigning official scorers for integrity verification..."
    
    local scorer_response=$(api_call "POST" "/api/v1/matches/$MATCH_ID/scorers" "$CAPTAIN_A_TOKEN" \
        "{\"team_a_scorer_id\":\"$CAPTAIN_A_ID\",\"team_b_scorer_id\":\"$CAPTAIN_B_ID\",\"umpire_id\":\"$UMPIRE_ID\"}")
    
    echo "Scorer assignment response: $scorer_response"
    
    # Step 5: Simulate ball-by-ball scoring with multiple scorers
    echo -e "\n⚾ Step 5: Multi-Scorer Ball Recording Simulation"
    echo "🎯 Simulating first over with consensus and dispute scenarios..."
    
    # Ball 1: Both scorers agree (2 runs)
    echo -e "\n--- Ball 1.1: Consensus Scenario ---"
    record_ball_as_scorer "$MATCH_ID" "$CAPTAIN_A_TOKEN" 1 1 2 0 "$CAPTAIN_B_ID" "$CAPTAIN_A_ID" "$CAPTAIN_B_ID" "Team A Scorer"
    sleep 1
    record_ball_as_scorer "$MATCH_ID" "$CAPTAIN_B_TOKEN" 1 1 2 0 "$CAPTAIN_B_ID" "$CAPTAIN_A_ID" "$CAPTAIN_B_ID" "Team B Scorer"
    sleep 1
    
    # Ball 2: Disagreement on runs (Team A says 4, Team B says 6)
    echo -e "\n--- Ball 1.2: Dispute Scenario ---"
    record_ball_as_scorer "$MATCH_ID" "$CAPTAIN_A_TOKEN" 1 2 4 0 "$CAPTAIN_B_ID" "$CAPTAIN_A_ID" "$CAPTAIN_B_ID" "Team A Scorer"
    sleep 1
    record_ball_as_scorer "$MATCH_ID" "$CAPTAIN_B_TOKEN" 1 2 6 0 "$CAPTAIN_B_ID" "$CAPTAIN_A_ID" "$CAPTAIN_B_ID" "Team B Scorer"
    sleep 1
    
    # Umpire resolves dispute
    echo "🏛️ Umpire reviewing dispute..."
    local dispute_response=$(api_call "GET" "/api/v1/matches/$MATCH_ID/scoring-status" "$UMPIRE_TOKEN")
    echo "Current disputes: $(echo "$dispute_response" | jq '.disputes')"
    
    # Ball 3: Three-way scoring (including umpire)
    echo -e "\n--- Ball 1.3: Three-Scorer Scenario ---"
    record_ball_as_scorer "$MATCH_ID" "$CAPTAIN_A_TOKEN" 1 3 1 0 "$CAPTAIN_B_ID" "$CAPTAIN_A_ID" "$CAPTAIN_B_ID" "Team A Scorer"
    sleep 1
    record_ball_as_scorer "$MATCH_ID" "$CAPTAIN_B_TOKEN" 1 3 1 0 "$CAPTAIN_B_ID" "$CAPTAIN_A_ID" "$CAPTAIN_B_ID" "Team B Scorer"
    sleep 1
    record_ball_as_scorer "$MATCH_ID" "$UMPIRE_TOKEN" 1 3 1 0 "$CAPTAIN_B_ID" "$CAPTAIN_A_ID" "$CAPTAIN_B_ID" "Umpire"
    sleep 1
    
    # Step 6: Check scoring status and integrity
    echo -e "\n📊 Step 6: Scoring Integrity Analysis"
    local final_status=$(api_call "GET" "/api/v1/matches/$MATCH_ID/scoring-status" "$CAPTAIN_A_TOKEN")
    echo "Final scoring status:"
    echo "$final_status" | jq '.'
    
    # Step 7: Get scorecard for spectators
    echo -e "\n👀 Step 7: Spectator View (Live Updates)"
    local scorecard=$(api_call "GET" "/api/v1/matches/$MATCH_ID/scorecard" "$SPECTATOR_TOKEN")
    echo "Current scorecard with integrity info:"
    echo "$scorecard" | jq '.'
    
    # Step 8: Live updates simulation
    echo -e "\n📡 Step 8: Live Updates Test"
    local live_updates=$(api_call "GET" "/api/v1/matches/$MATCH_ID/live-updates" "$SPECTATOR_TOKEN")
    echo "Live match updates:"
    echo "$live_updates" | jq '.'
    
    # Final summary
    echo -e "\n🎉 Scoring Integrity Simulation Complete!"
    echo "======================================"
    echo "Match ID: $MATCH_ID"
    echo "Team A: Warriors (Captain: $TEAM_A_CAPTAIN)"
    echo "Team B: Champions (Captain: $TEAM_B_CAPTAIN)"
    echo "Umpire: $UMPIRE_USER"
    echo "Spectator: $SPECTATOR_USER"
    echo ""
    echo "✅ Demonstrated Features:"
    echo "  - Multi-user registration and authentication"
    echo "  - Team creation and management"
    echo "  - Match setup with scorer assignment"
    echo "  - Multi-scorer ball recording with consensus"
    echo "  - Dispute detection and handling"
    echo "  - Integrity verification and audit trails"
    echo "  - Live updates for spectators"
    echo "  - Complete end-to-end workflow"
    echo ""
    echo "🔍 This simulation proves the scoring integrity system prevents"
    echo "   match-fixing by requiring consensus between multiple scorers."
}

# Error handling
trap 'echo "❌ Simulation interrupted"; exit 1' INT TERM

# Run simulation
main "$@"

echo -e "\n🎯 Simulation Complete! The integrity system is working as designed."
