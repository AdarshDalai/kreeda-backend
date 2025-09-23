#!/usr/bin/env python3
import json
import uuid
from datetime import datetime

def create_enhanced_collection():
    collection = {
        "info": {
            "_postman_id": str(uuid.uuid4()),
            "name": "Kreeda Cricket API - Complete Enhanced Collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": {
                "content": "Complete API collection for Kreeda cricket platform with all endpoints, realistic test data, and comprehensive validation",
                "type": "text/plain"
            }
        },
        "item": [],
        "event": [
            {
                "listen": "prerequest",
                "script": {
                    "type": "text/javascript",
                    "exec": [
                        "// Global pre-request script for authentication",
                        "if (pm.info.requestName !== 'User Registration' && pm.info.requestName !== 'User Login') {",
                        "    const token = pm.collectionVariables.get('accessToken');",
                        "    if (token) {",
                        "        pm.request.headers.add({",
                        "            key: 'Authorization',",
                        "            value: `Bearer ${token}`",
                        "        });",
                        "    }",
                        "}"
                    ]
                }
            },
            {
                "listen": "test",
                "script": {
                    "type": "text/javascript",
                    "exec": [
                        "// Global test script for response validation",
                        "pm.test('Response status is not 5xx', function () {",
                        "    pm.expect(pm.response.code).to.be.below(500);",
                        "});",
                        "",
                        "pm.test('Response time is acceptable', function () {",
                        "    pm.expect(pm.response.responseTime).to.be.below(10000);",
                        "});",
                        "",
                        "if (pm.response.headers.get('Content-Type') && pm.response.headers.get('Content-Type').includes('application/json')) {",
                        "    pm.test('Response is valid JSON', function () {",
                        "        pm.response.json();",
                        "    });",
                        "}"
                    ]
                }
            }
        ],
        "variable": [
            {"key": "baseUrl", "value": "https://kreeda-backend-5dwv.onrender.com", "type": "string"},
            {"key": "baseUrlDev", "value": "http://localhost:8000", "type": "string"},
            {"key": "accessToken", "value": "", "type": "string"},
            {"key": "refreshToken", "value": "", "type": "string"},
            {"key": "userId", "value": "", "type": "string"},
            {"key": "teamId", "value": "", "type": "string"},
            {"key": "matchId", "value": "", "type": "string"},
            {"key": "tournamentId", "value": "", "type": "string"},
            {"key": "notificationId", "value": "", "type": "string"},
            {"key": "invitationToken", "value": "", "type": "string"}
        ]
    }
    
    # Authentication Workflow
    auth_folder = {
        "name": "🔐 Authentication Workflow",
        "item": [
            {
                "name": "1. Register User",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "email": "{{$randomEmail}}",
                            "username": "player_{{$randomInt}}",
                            "full_name": "{{$randomFirstName}} {{$randomLastName}}",
                            "password": "TestPass123!"
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/auth/register",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "auth", "register"]
                    }
                },
                "event": [
                    {
                        "listen": "test",
                        "script": {
                            "exec": [
                                "pm.test('Registration successful', function () {",
                                "    pm.expect(pm.response.code).to.be.oneOf([200, 201]);",
                                "});",
                                "",
                                "if (pm.response.code === 200 || pm.response.code === 201) {",
                                "    const response = pm.response.json();",
                                "    if (response.access_token) {",
                                "        pm.collectionVariables.set('accessToken', response.access_token);",
                                "    }",
                                "    if (response.user && response.user.id) {",
                                "        pm.collectionVariables.set('userId', response.user.id);",
                                "    }",
                                "}"
                            ]
                        }
                    }
                ]
            },
            {
                "name": "2. Login User",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "email": "test@cricket.com",
                            "password": "TestPass123!"
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/auth/login",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "auth", "login"]
                    }
                },
                "event": [
                    {
                        "listen": "test",
                        "script": {
                            "exec": [
                                "pm.test('Login successful', function () {",
                                "    pm.expect(pm.response.code).to.equal(200);",
                                "});",
                                "",
                                "if (pm.response.code === 200) {",
                                "    const response = pm.response.json();",
                                "    pm.collectionVariables.set('accessToken', response.access_token);",
                                "    if (response.refresh_token) {",
                                "        pm.collectionVariables.set('refreshToken', response.refresh_token);",
                                "    }",
                                "}"
                            ]
                        }
                    }
                ]
            },
            {
                "name": "3. Get Current User",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/auth/me",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "auth", "me"]
                    }
                },
                "event": [
                    {
                        "listen": "test",
                        "script": {
                            "exec": [
                                "pm.test('Get user profile successful', function () {",
                                "    pm.expect(pm.response.code).to.equal(200);",
                                "});",
                                "",
                                "if (pm.response.code === 200) {",
                                "    const response = pm.response.json();",
                                "    pm.collectionVariables.set('userId', response.id);",
                                "}"
                            ]
                        }
                    }
                ]
            },
            {
                "name": "4. Refresh Token",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "refresh_token": "{{refreshToken}}"
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/auth/refresh",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "auth", "refresh"]
                    }
                }
            }
        ]
    }
    
    # Team Management
    team_folder = {
        "name": "👥 Team Management",
        "item": [
            {
                "name": "1. Create Team",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "name": "Mumbai Strikers",
                            "short_name": "MUM",
                            "logo_url": "https://example.com/mumbai-strikers-logo.png",
                            "captain_id": "{{userId}}"
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/teams/",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "teams", ""]
                    }
                },
                "event": [
                    {
                        "listen": "test",
                        "script": {
                            "exec": [
                                "pm.test('Team creation successful', function () {",
                                "    pm.expect(pm.response.code).to.equal(200);",
                                "});",
                                "",
                                "if (pm.response.code === 200) {",
                                "    const response = pm.response.json();",
                                "    pm.collectionVariables.set('teamId', response.id);",
                                "}"
                            ]
                        }
                    }
                ]
            },
            {
                "name": "2. Get User Teams",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/teams/",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "teams", ""]
                    }
                }
            },
            {
                "name": "3. Invite User to Team",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "email": "player2@cricket.com",
                            "message": "Join our cricket team!"
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/teams/{{teamId}}/invite",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "teams", "{{teamId}}", "invite"]
                    }
                }
            },
            {
                "name": "4. Get Team Members",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/teams/{{teamId}}/members",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "teams", "{{teamId}}", "members"]
                    }
                }
            }
        ]
    }
    
    # Match Management
    match_folder = {
        "name": "🏏 Match Management & Live Scoring",
        "item": [
            {
                "name": "1. Create Cricket Match",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "team_a_id": "{{teamId}}",
                            "team_b_id": "{{teamId}}",
                            "venue": "Wankhede Stadium, Mumbai",
                            "match_date": "2024-12-25T14:30:00Z",
                            "overs_per_innings": 20
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/matches/",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "matches", ""]
                    }
                },
                "event": [
                    {
                        "listen": "test",
                        "script": {
                            "exec": [
                                "pm.test('Match creation successful', function () {",
                                "    pm.expect(pm.response.code).to.equal(200);",
                                "});",
                                "",
                                "if (pm.response.code === 200) {",
                                "    const response = pm.response.json();",
                                "    pm.collectionVariables.set('matchId', response.id);",
                                "}"
                            ]
                        }
                    }
                ]
            },
            {
                "name": "2. Record Toss",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "toss_winner_id": "{{teamId}}",
                            "toss_decision": "bat"
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/matches/{{matchId}}/toss",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "matches", "{{matchId}}", "toss"]
                    }
                }
            },
            {
                "name": "3. Record Ball - Four Runs",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "over_number": 1,
                            "ball_number": 1,
                            "bowler_id": "{{userId}}",
                            "batsman_striker_id": "{{userId}}",
                            "batsman_non_striker_id": "{{userId}}",
                            "runs_scored": 4,
                            "extras": 0,
                            "ball_type": "legal",
                            "is_wicket": False,
                            "is_boundary": True,
                            "boundary_type": "four"
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/matches/{{matchId}}/balls",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "matches", "{{matchId}}", "balls"]
                    }
                }
            },
            {
                "name": "4. Get Live Scorecard",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/matches/{{matchId}}/scorecard",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "matches", "{{matchId}}", "scorecard"]
                    }
                }
            }
        ]
    }
    
    # Tournament Management
    tournament_folder = {
        "name": "🏆 Tournament Management",
        "item": [
            {
                "name": "1. Create Tournament",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "name": "Mumbai Premier League 2024",
                            "tournament_type": "league",
                            "start_date": "2024-12-01T00:00:00Z",
                            "description": "Premier cricket tournament in Mumbai",
                            "end_date": "2024-12-31T23:59:59Z",
                            "registration_deadline": "2024-11-25T23:59:59Z",
                            "max_teams": 16,
                            "min_teams": 8,
                            "entry_fee": "50000",
                            "prize_money": "500000",
                            "overs_per_innings": 20,
                            "venue_details": "Multiple venues across Mumbai",
                            "organizer_contact": "tournament@kreeda.com",
                            "is_public": True
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/tournaments/",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "tournaments", ""]
                    }
                },
                "event": [
                    {
                        "listen": "test",
                        "script": {
                            "exec": [
                                "pm.test('Tournament creation successful', function () {",
                                "    pm.expect(pm.response.code).to.equal(201);",
                                "});",
                                "",
                                "if (pm.response.code === 201) {",
                                "    const response = pm.response.json();",
                                "    pm.collectionVariables.set('tournamentId', response.id);",
                                "}"
                            ]
                        }
                    }
                ]
            },
            {
                "name": "2. Register Team for Tournament",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "team_id": "{{teamId}}",
                            "payment_reference": "PAY_{{$randomInt}}"
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/tournaments/{{tournamentId}}/register",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "tournaments", "{{tournamentId}}", "register"]
                    }
                }
            },
            {
                "name": "3. Get Tournament Standings",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/tournaments/{{tournamentId}}/standings",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "tournaments", "{{tournamentId}}", "standings"]
                    }
                }
            }
        ]
    }
    
    # Statistics & Analytics
    stats_folder = {
        "name": "📊 Statistics & Analytics",
        "item": [
            {
                "name": "1. Get Player Career Stats",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/statistics/career/{{userId}}",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "statistics", "career", "{{userId}}"]
                    }
                }
            },
            {
                "name": "2. Get Player Performance",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/statistics/players/performance?limit=20",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "statistics", "players", "performance"],
                        "query": [{"key": "limit", "value": "20"}]
                    }
                }
            },
            {
                "name": "3. Get Leaderboard",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/statistics/leaderboard/runs?limit=10",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "statistics", "leaderboard", "runs"],
                        "query": [{"key": "limit", "value": "10"}]
                    }
                }
            },
            {
                "name": "4. Update Player Career Stats",
                "request": {
                    "method": "POST",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/statistics/career/{{userId}}/update",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "statistics", "career", "{{userId}}", "update"]
                    }
                }
            }
        ]
    }
    
    # Notifications
    notifications_folder = {
        "name": "🔔 Notifications",
        "item": [
            {
                "name": "1. Get My Notifications",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/notifications/?page=1&page_size=20",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "notifications", ""],
                        "query": [
                            {"key": "page", "value": "1"},
                            {"key": "page_size", "value": "20"}
                        ]
                    }
                }
            },
            {
                "name": "2. Get Notification Summary",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/notifications/summary",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "notifications", "summary"]
                    }
                }
            },
            {
                "name": "3. Mark All Notifications Read",
                "request": {
                    "method": "PATCH",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": "{}"
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/notifications/mark-all-read",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "notifications", "mark-all-read"]
                    }
                }
            }
        ]
    }
    
    # User Profile
    profile_folder = {
        "name": "👤 User Profile",
        "item": [
            {
                "name": "1. Get Profile",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/user/",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "user", ""]
                    }
                }
            },
            {
                "name": "2. Update Profile",
                "request": {
                    "method": "PUT",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "bio": "Cricket enthusiast and player",
                            "location": "Mumbai, India",
                            "favorite_sports": ["Cricket", "Football"]
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/user/",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "user", ""]
                    }
                }
            },
            {
                "name": "3. Get Dashboard Stats",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/user/dashboard",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "user", "dashboard"]
                    }
                }
            }
        ]
    }
    
    # Health Checks
    health_folder = {
        "name": "🏥 Health Checks",
        "item": [
            {
                "name": "1. General Health",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/health",
                        "host": ["{{baseUrl}}"],
                        "path": ["health"]
                    }
                }
            },
            {
                "name": "2. Auth Health",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/auth/health",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "auth", "health"]
                    }
                }
            },
            {
                "name": "3. Teams Health",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/teams/health",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "teams", "health"]
                    }
                }
            },
            {
                "name": "4. Notifications Health",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/notifications/health",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "notifications", "health"]
                    }
                }
            }
        ]
    }
    
    # Add all folders to collection
    collection["item"] = [
        auth_folder,
        team_folder,
        match_folder,
        tournament_folder,
        stats_folder,
        notifications_folder,
        profile_folder,
        health_folder
    ]
    
    return collection

if __name__ == "__main__":
    collection = create_enhanced_collection()
    with open("postman-collection/kreeda-api-complete-collection.json", "w") as f:
        json.dump(collection, f, indent=2)
    print("✅ Complete Postman collection generated successfully!")
