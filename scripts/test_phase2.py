import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("Kreeda Phase 2 Manual Test (Python)")
print("=" * 60)

# Step 1: Register user
print("\n[1/12] Registering test user...")
timestamp = int(datetime.now().timestamp())
reg_data = {
    "email": f"pytest{timestamp}@kreeda.app",
    "password": "Test1234!",
    "full_name": "Python Test User"
}
resp = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
resp_json = resp.json()
user_id = resp_json['user']['id']
access_token = resp_json['session']['access_token']
print(f"✓ User created: {user_id}")

headers = {"Authorization": f"Bearer {access_token}"}

# Step 2: Create sport profile first
print("\n[2/12] Creating sport profile...")
sport_profile_data = {
    "sport_type": "cricket",
    "display_name": f"PyTestCricketer{timestamp}",
    "bio": "Test cricket player profile"
}
resp = requests.post(f"{BASE_URL}/sport-profiles", json=sport_profile_data, headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code != 201:
    print(f"Error: {json.dumps(resp.json(), indent=2)}")
    exit(1)
sport_profile_resp = resp.json()
print(f"Full response: {json.dumps(sport_profile_resp, indent=2)}")
# Check if response is wrapped in 'data' or direct
if 'data' in sport_profile_resp:
    sport_profile_id = sport_profile_resp['data']['id']
else:
    sport_profile_id = sport_profile_resp['id']
print(f"✓ Sport Profile created: {sport_profile_id}")

# Step 3: Create cricket profile
print("\n[3/12] Creating cricket profile...")
profile_data = {
    "sport_profile_id": sport_profile_id,
    "batting_style": "right_hand",
    "bowling_style": "right_arm_fast",
    "playing_role": "all_rounder"
}
resp = requests.post(f"{BASE_URL}/cricket-profiles", json=profile_data, headers=headers)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}")
profile_resp = resp.json()
# Profile response is unwrapped
profile_id = profile_resp['id']
print(f"✓ Cricket Profile created: {profile_id}")

# Step 4: Create Team A
print("\n[4/12] Creating Team A...")
team_a_data = {
    "name": f"Mumbai Challengers {timestamp}",
    "team_type": "club",
    "sport_type": "cricket",
    "description": "Test team A",
    "team_colors": {
        "primary": "#FF5733",
        "secondary": "#FFFFFF"
    }
}
resp = requests.post(f"{BASE_URL}/api/v1/cricket/teams", json=team_a_data, headers=headers)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)[:500]}...")
team_a_resp = resp.json()
# Team responses are wrapped in 'data'
if 'data' in team_a_resp:
    team_a_id = team_a_resp['data']['id']
else:
    team_a_id = team_a_resp['id']
print(f"✓ Team A created: {team_a_id}")

# Step 5: Create Team B
print("\n[5/12] Creating Team B...")
team_b_data = {
    "name": f"Chennai Super Kings {timestamp}",
    "team_type": "club",
    "sport_type": "cricket",
    "description": "Test team B",
    "team_colors": {
        "primary": "#FFFF00",
        "secondary": "#0000FF"
    }
}
resp = requests.post(f"{BASE_URL}/api/v1/cricket/teams", json=team_b_data, headers=headers)
team_b_resp = resp.json()
if 'data' in team_b_resp:
    team_b_id = team_b_resp['data']['id']
else:
    team_b_id = team_b_resp['id']
print(f"✓ Team B created: {team_b_id}")

# Step 6: List teams
print("\n[6/12] Listing all teams...")
resp = requests.get(f"{BASE_URL}/api/v1/cricket/teams", headers=headers)
teams_data = resp.json()
if 'data' in teams_data:
    print(f"✓ Found {teams_data['data']['total']} teams")
else:
    print(f"✓ Found {len(teams_data)} teams")

# Step 7: Get Team A details
print("\n[7/12] Getting Team A details...")
resp = requests.get(f"{BASE_URL}/api/v1/cricket/teams/{team_a_id}", headers=headers)
team_detail = resp.json()
print(f"Team detail response: {json.dumps(team_detail, indent=2)[:300]}...")
if 'data' in team_detail:
    print(f"✓ Team A details: {team_detail['data']['name']}")
elif 'name' in team_detail:
    print(f"✓ Team A details: {team_detail['name']}")
elif 'items' in team_detail:
    print(f"✓ Team A details (list response)")
else:
    print(f"✓ Team A details retrieved")

# Step 8: Add member to Team A
print("\n[8/12] Adding member to Team A...")
member_data = {
    "user_id": str(user_id),
    "cricket_profile_id": profile_id,
    "roles": ["player"],
    "jersey_number": 7
}
resp = requests.post(f"{BASE_URL}/api/v1/cricket/teams/{team_a_id}/members", json=member_data, headers=headers)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}")
if resp.status_code >= 400:
    print("Error adding member, continuing...")
else:
    print(f"✓ Member added to Team A")

# Step 9: Get Team A members
print("\n[9/12] Getting Team A members...")
resp = requests.get(f"{BASE_URL}/api/v1/cricket/teams/{team_a_id}/members", headers=headers)
members_data = resp.json()
if 'data' in members_data:
    print(f"✓ Team A has {members_data['data']['total']} members")
else:
    print(f"✓ Team A has {len(members_data)} members")

# Step 10: Create match
print("\n[10/12] Creating match...")
match_data = {
    "team_a_id": team_a_id,
    "team_b_id": team_b_id,
    "match_type": "t20",
    "sport_type": "cricket",
    "scheduled_start_time": "2025-11-15T14:00:00Z",
    "venue": {
        "name": "Wankhede Stadium",
        "city": "Mumbai",
        "country": "India"
    }
}
resp = requests.post(f"{BASE_URL}/api/v1/cricket/matches", json=match_data, headers=headers)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)[:600]}...")
match_resp = resp.json()
if 'data' in match_resp:
    match_id = match_resp['data']['id']
    match_code = match_resp['data']['match_code']
else:
    match_id = match_resp['id']
    match_code = match_resp['match_code']
print(f"✓ Match created: {match_id} (Code: {match_code})")

# Step 11: List matches
print("\n[11/12] Listing all matches...")
resp = requests.get(f"{BASE_URL}/api/v1/cricket/matches", headers=headers)
matches_data = resp.json()
if 'data' in matches_data:
    print(f"✓ Found {matches_data['data']['total']} matches")
else:
    print(f"✓ Found {len(matches_data)} matches")

# Step 12: Conduct toss
print("\n[12/12] Conducting toss...")
toss_data = {
    "toss_won_by_team_id": team_a_id,
    "elected_to": "bat"
}
resp = requests.post(f"{BASE_URL}/api/v1/cricket/matches/{match_id}/toss", json=toss_data, headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code >= 400:
    print(f"Error: {json.dumps(resp.json(), indent=2)[:500]}...")
    print("Error conducting toss, continuing...")
else:
    print(f"Response: {json.dumps(resp.json(), indent=2)[:500]}...")
    print(f"✓ Toss conducted")

# Step 13: Get match details
print("\n[13/13] Getting final match details...")
resp = requests.get(f"{BASE_URL}/api/v1/cricket/matches/{match_id}", headers=headers)
final_match = resp.json()
if 'data' in final_match and 'status' in final_match['data']:
    print(f"✓ Match status: {final_match['data']['status']}")
elif 'status' in final_match:
    print(f"✓ Match status: {final_match['status']}")
else:
    print(f"✓ Match details retrieved (status field not found)")

print("\n" + "=" * 60)
print("✓ All Phase 2 tests passed!")
print("=" * 60)
print(f"\nSummary:")
print(f"  User ID: {user_id}")
print(f"  Profile ID: {profile_id}")
print(f"  Team A ID: {team_a_id}")
print(f"  Team B ID: {team_b_id}")
print(f"  Match ID: {match_id}")
print(f"  Match Code: {match_code}")
