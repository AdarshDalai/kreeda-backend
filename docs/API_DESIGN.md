# Kreeda Backend - API Design Specification
**Version:** 1.0  
**Date:** October 26, 2025  
**Sport Module:** Cricket (MVP)  
**Status:** Design Phase

---

## Table of Contents
1. [Design Principles](#design-principles)
2. [Authentication & Authorization](#authentication--authorization)
3. [API Structure](#api-structure)
4. [Endpoint Categories](#endpoint-categories)
5. [Detailed Endpoint Specifications](#detailed-endpoint-specifications)
6. [Real-time Features](#real-time-features)
7. [Error Handling](#error-handling)
8. [Rate Limiting & Performance](#rate-limiting--performance)

---

## Design Principles

### RESTful Architecture
- Resource-based URLs
- Standard HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Proper status codes
- HATEOAS for navigation where appropriate

### API Versioning
- URL-based versioning: `/api/v1/`
- Allows backward compatibility
- Clear deprecation strategy

### Consistency
- Uniform response structure
- Consistent naming conventions (snake_case for JSON)
- Standard error format
- Pagination for list endpoints

### Security
- JWT-based authentication
- Role-based access control (RBAC)
- Match-level permissions (creator, team members, scorers, spectators)
- Rate limiting per endpoint

### Performance
- Efficient pagination (cursor-based for real-time data)
- Field selection/sparse fieldsets
- Caching headers
- WebSocket for live updates

---

## Authentication & Authorization

### Auth Flow
```
1. User registers/logs in → Receives JWT access token + refresh token
2. Access token: 1 hour validity
3. Refresh token: 7 days validity
4. All protected endpoints require: Authorization: Bearer <token>
```

### User Roles (Enum)
- `PLAYER` - Can create teams, join matches, score
- `SCORER` - Can be assigned as official scorer
- `UMPIRE` - Can be assigned as umpire
- `ADMIN` - Platform admin (future)

### Match-Level Permissions
- **Match Creator**: Full control (edit, delete, assign officials)
- **Team Captain**: Manage team members, submit playing XI
- **Assigned Scorer**: Submit scoring events
- **Assigned Umpire**: Override disputes, validate events
- **Team Member**: View match details, see live scores
- **Spectator** (with match code): Read-only access to live scores

---

## API Structure

### Base URL
```
Production: https://api.kreeda.app/v1
Development: http://localhost:8000/api/v1
```

### Response Structure

#### Success Response
```json
{
  "success": true,
  "data": { /* resource or array */ },
  "meta": {
    "timestamp": "2025-10-26T10:30:00Z",
    "request_id": "req_abc123"
  },
  "pagination": {  // only for list endpoints
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5,
    "next_cursor": "eyJpZCI6MTIzfQ==",
    "prev_cursor": null
  }
}
```

#### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "overs_per_side",
        "message": "Must be between 5 and 50"
      }
    ]
  },
  "meta": {
    "timestamp": "2025-10-26T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

---

## Endpoint Categories

### 1. User & Profile Management
- User authentication (existing)
- User profiles (existing)
- Sport profile management (NEW)
- Cricket player profiles (NEW)

### 2. Team Management
- Create/manage teams
- Team member management
- Team rosters
- Team statistics

### 3. Match Management
- Match lifecycle (create, schedule, start, complete)
- Match configuration & rules
- Official assignment (scorers, umpires)
- Playing XI selection

### 4. Live Scoring
- Ball-by-ball scoring
- Wicket recording
- Innings management
- Over completion

### 5. Scoring Integrity
- Event submission (dual/triple validation)
- Dispute management
- Consensus resolution
- Event log access

### 6. Statistics & Analytics
- Player statistics
- Match summaries
- Team performance
- Leaderboards

### 7. Match Discovery & Spectator
- Public match listing
- Match join (via code)
- Live scorecard access

---

## Detailed Endpoint Specifications

---

## 📁 CATEGORY 1: SPORT PROFILES

### 1.1 Create Sport Profile
```http
POST /api/v1/profiles/sports
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "sport_type": "CRICKET",  // ENUM: CRICKET, FOOTBALL, HOCKEY, BASKETBALL
  "visibility": "PUBLIC"     // ENUM: PUBLIC, FRIENDS, PRIVATE
}

Response: 201 Created
{
  "success": true,
  "data": {
    "id": "uuid-123",
    "user_id": "uuid-456",
    "sport_type": "CRICKET",
    "is_verified": false,
    "verification_proof": null,
    "visibility": "PUBLIC",
    "created_at": "2025-10-26T10:30:00Z"
  }
}
```

### 1.2 Get My Sport Profiles
```http
GET /api/v1/profiles/sports
Authorization: Bearer <token>

Query Params:
- sport_type (optional): Filter by sport

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": "uuid-123",
      "sport_type": "CRICKET",
      "cricket_profile": {
        "id": "uuid-789",
        "playing_role": "BATSMAN",
        "batting_style": "RIGHT_HAND",
        "career_stats": { /* ... */ }
      }
    }
  ]
}
```

### 1.3 Create/Update Cricket Player Profile
```http
POST /api/v1/profiles/cricket
Authorization: Bearer <token>

Request Body:
{
  "sport_profile_id": "uuid-123",  // required
  "playing_role": "ALL_ROUNDER",   // ENUM: BATSMAN, BOWLER, ALL_ROUNDER, WICKET_KEEPER
  "batting_style": "RIGHT_HAND",   // ENUM: RIGHT_HAND, LEFT_HAND
  "bowling_style": "RIGHT_ARM_MEDIUM"  // ENUM or null
}

Response: 201 Created
{
  "success": true,
  "data": {
    "id": "uuid-789",
    "sport_profile_id": "uuid-123",
    "playing_role": "ALL_ROUNDER",
    "batting_style": "RIGHT_HAND",
    "bowling_style": "RIGHT_ARM_MEDIUM",
    "career_stats": {
      "matches_played": 0,
      "total_runs": 0,
      "wickets_taken": 0,
      // ... initialized to 0
    }
  }
}
```

### 1.4 Get Cricket Player Profile
```http
GET /api/v1/profiles/cricket/{cricket_profile_id}
Authorization: Bearer <token> (optional - public profiles)

Response: 200 OK
{
  "success": true,
  "data": {
    "id": "uuid-789",
    "user": {
      "id": "uuid-456",
      "full_name": "Virat Kohli",
      "avatar_url": "https://..."
    },
    "playing_role": "BATSMAN",
    "batting_style": "RIGHT_HAND",
    "career_stats": {
      "matches_played": 150,
      "total_runs": 5420,
      "highest_score": 183,
      "batting_average": 52.15,
      "strike_rate": 138.5,
      "centuries": 12,
      "half_centuries": 28,
      "wickets_taken": 5,
      "best_bowling": "2/15"
    }
  }
}
```

---

## 📁 CATEGORY 2: TEAM MANAGEMENT

### 2.1 Create Team
```http
POST /api/v1/teams
Authorization: Bearer <token>

Request Body:
{
  "name": "Mumbai Indians",
  "short_name": "MI",
  "sport_type": "CRICKET",
  "team_type": "CLUB",  // ENUM: CASUAL, CLUB, TOURNAMENT_REGISTERED, FRANCHISE
  "home_ground": {
    "name": "Wankhede Stadium",
    "city": "Mumbai",
    "latitude": 18.9389,
    "longitude": 72.8258
  },
  "logo_url": "https://...",
  "description": "IPL franchise team"
}

Response: 201 Created
{
  "success": true,
  "data": {
    "id": "uuid-team-1",
    "name": "Mumbai Indians",
    "short_name": "MI",
    "sport_type": "CRICKET",
    "team_type": "CLUB",
    "creator_user_id": "uuid-456",
    "home_ground": { /* ... */ },
    "logo_url": "https://...",
    "member_count": 1,
    "created_at": "2025-10-26T10:30:00Z"
  }
}
```

### 2.2 Add Team Member
```http
POST /api/v1/teams/{team_id}/members
Authorization: Bearer <token>

Request Body:
{
  "user_id": "uuid-789",
  "cricket_profile_id": "uuid-cricket-123",
  "roles": ["PLAYER"],  // ARRAY: PLAYER, CAPTAIN, VICE_CAPTAIN, COACH
  "jersey_number": 18,
  "is_captain": false
}

Response: 201 Created
{
  "success": true,
  "data": {
    "id": "uuid-membership-1",
    "team_id": "uuid-team-1",
    "user_id": "uuid-789",
    "cricket_profile_id": "uuid-cricket-123",
    "roles": ["PLAYER"],
    "jersey_number": 18,
    "status": "ACTIVE",
    "joined_at": "2025-10-26T10:30:00Z"
  }
}
```

### 2.3 Get Team Details
```http
GET /api/v1/teams/{team_id}
Authorization: Bearer <token> (optional)

Query Params:
- include_members: true/false (default: false)

Response: 200 OK
{
  "success": true,
  "data": {
    "id": "uuid-team-1",
    "name": "Mumbai Indians",
    "short_name": "MI",
    "sport_type": "CRICKET",
    "creator": {
      "id": "uuid-456",
      "full_name": "Rohit Sharma"
    },
    "statistics": {
      "matches_played": 45,
      "matches_won": 28,
      "matches_lost": 15,
      "matches_tied": 2,
      "win_percentage": 62.22
    },
    "members": [  // if include_members=true
      {
        "user_id": "uuid-789",
        "full_name": "Jasprit Bumrah",
        "jersey_number": 93,
        "roles": ["PLAYER"],
        "cricket_profile": {
          "playing_role": "BOWLER",
          "career_stats": { /* ... */ }
        }
      }
    ]
  }
}
```

### 2.4 Update Team Member Status
```http
PATCH /api/v1/teams/{team_id}/members/{membership_id}
Authorization: Bearer <token>

Request Body:
{
  "status": "BENCHED",  // ENUM: ACTIVE, BENCHED, INJURED, SUSPENDED, LEFT
  "jersey_number": 99,
  "roles": ["PLAYER", "VICE_CAPTAIN"]
}

Response: 200 OK
```

### 2.5 List My Teams
```http
GET /api/v1/teams/my
Authorization: Bearer <token>

Query Params:
- sport_type: CRICKET
- role: PLAYER, CAPTAIN
- status: ACTIVE, BENCHED

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "team": { /* team details */ },
      "membership": {
        "roles": ["PLAYER", "CAPTAIN"],
        "jersey_number": 45,
        "status": "ACTIVE"
      }
    }
  ]
}
```

---

## 📁 CATEGORY 3: MATCH MANAGEMENT

### 3.1 Create Match
```http
POST /api/v1/matches
Authorization: Bearer <token>

Request Body:
{
  "team_a_id": "uuid-team-1",
  "team_b_id": "uuid-team-2",
  "match_type": "T20",  // ENUM: T20, ODI, TEST, ONE_DAY, THE_HUNDRED, CUSTOM
  "match_category": "TOURNAMENT",  // ENUM: CASUAL, TOURNAMENT, LEAGUE, FRIENDLY, PRACTICE
  "scheduled_at": "2025-10-27T14:00:00Z",
  "venue": {
    "name": "Eden Gardens",
    "city": "Kolkata",
    "latitude": 22.5645,
    "longitude": 88.3433
  },
  "match_rules": {
    "players_per_team": 11,
    "overs_per_side": 20,
    "balls_per_over": 6,
    "wickets_to_fall": 10,
    "powerplay_overs": 6,
    "free_hit_on_no_ball": true,
    "drs_available": false
  },
  "visibility": "PUBLIC",  // ENUM: PUBLIC, PRIVATE, FRIENDS_ONLY
  "scoring_validation_tier": "DUAL"  // ENUM: TRIPLE, DUAL, SINGLE, HONOR
}

Response: 201 Created
{
  "success": true,
  "data": {
    "id": "uuid-match-1",
    "match_code": "KRD-A3B9C2",  // 6-char spectator code
    "team_a": { /* team details */ },
    "team_b": { /* team details */ },
    "match_type": "T20",
    "status": "SCHEDULED",
    "scheduled_at": "2025-10-27T14:00:00Z",
    "venue": { /* ... */ },
    "match_rules": { /* ... */ },
    "creator_user_id": "uuid-456"
  }
}
```

### 3.2 Assign Match Officials
```http
POST /api/v1/matches/{match_id}/officials
Authorization: Bearer <token>

Request Body:
{
  "user_id": "uuid-scorer-1",
  "role": "SCORER",  // ENUM: SCORER, UMPIRE, THIRD_UMPIRE, MATCH_REFEREE
  "assignment": "TEAM_A"  // ENUM: TEAM_A, TEAM_B, NEUTRAL
}

Response: 201 Created
{
  "success": true,
  "data": {
    "id": "uuid-official-1",
    "match_id": "uuid-match-1",
    "user_id": "uuid-scorer-1",
    "role": "SCORER",
    "assignment": "TEAM_A",
    "assigned_at": "2025-10-26T10:30:00Z"
  }
}

Permissions: Only match creator or admin
```

### 3.3 Submit Playing XI
```http
POST /api/v1/matches/{match_id}/playing-xi
Authorization: Bearer <token>

Request Body:
{
  "team_id": "uuid-team-1",
  "players": [
    {
      "cricket_profile_id": "uuid-cricket-1",
      "batting_order": 1,
      "can_bat": true,
      "can_bowl": true,
      "is_wicket_keeper": false,
      "is_captain": true
    },
    // ... 10 more players
  ]
}

Response: 201 Created
{
  "success": true,
  "data": {
    "match_id": "uuid-match-1",
    "team_id": "uuid-team-1",
    "playing_xi": [ /* ... */ ],
    "submitted_at": "2025-10-26T10:30:00Z"
  }
}

Permissions: Team captain or match creator
```

### 3.4 Conduct Toss
```http
POST /api/v1/matches/{match_id}/toss
Authorization: Bearer <token>

Request Body:
{
  "toss_won_by_team_id": "uuid-team-1",
  "elected_to": "BAT"  // ENUM: BAT, BOWL
}

Response: 200 OK
{
  "success": true,
  "data": {
    "match_id": "uuid-match-1",
    "toss_won_by_team_id": "uuid-team-1",
    "elected_to": "BAT",
    "status": "TOSS_PENDING" → "LIVE"
  }
}

Permissions: Match creator or assigned umpire
Side Effect: Creates first innings automatically
```

### 3.5 Get Match Details
```http
GET /api/v1/matches/{match_id}
Authorization: Bearer <token> (optional for public matches)

Query Params:
- include_playing_xi: true/false
- include_officials: true/false

Response: 200 OK
{
  "success": true,
  "data": {
    "id": "uuid-match-1",
    "match_code": "KRD-A3B9C2",
    "status": "LIVE",
    "team_a": { /* ... */ },
    "team_b": { /* ... */ },
    "toss": {
      "won_by_team_id": "uuid-team-1",
      "elected_to": "BAT"
    },
    "current_innings": {
      "innings_number": 1,
      "batting_team_id": "uuid-team-1",
      "current_score": "145/4",
      "current_over": 15.3,
      "run_rate": 9.35,
      "required_run_rate": null
    },
    "match_rules": { /* ... */ },
    "officials": [ /* if requested */ ],
    "playing_xi": { /* if requested */ }
  }
}
```

### 3.6 List Matches
```http
GET /api/v1/matches
Authorization: Bearer <token> (optional)

Query Params:
- status: SCHEDULED, LIVE, COMPLETED
- visibility: PUBLIC, PRIVATE
- team_id: Filter by team
- from_date: ISO timestamp
- to_date: ISO timestamp
- page: 1
- per_page: 20

Response: 200 OK with pagination
```

### 3.7 Join Match as Spectator
```http
POST /api/v1/matches/join
Authorization: Bearer <token> (optional - can be anonymous)

Request Body:
{
  "match_code": "KRD-A3B9C2"
}

Response: 200 OK
{
  "success": true,
  "data": {
    "match": { /* full match details */ },
    "access_level": "SPECTATOR",
    "websocket_channel": "match:uuid-match-1:live"
  }
}
```

---

## 📁 CATEGORY 4: LIVE SCORING

### 4.1 Submit Scoring Event (Ball)
```http
POST /api/v1/matches/{match_id}/scoring/events
Authorization: Bearer <token>

Request Body:
{
  "innings_id": "uuid-innings-1",
  "over_id": "uuid-over-1",
  "event_type": "BALL_BOWLED",  // ENUM: BALL_BOWLED, WICKET_FALLEN, OVER_COMPLETE, etc.
  "scorer_team_side": "TEAM_A",  // ENUM: TEAM_A, TEAM_B, UMPIRE, SYSTEM
  "event_data": {
    "ball_number": 15.4,
    "bowler_id": "uuid-cricket-bowler",
    "batsman_striker_id": "uuid-cricket-striker",
    "batsman_non_striker_id": "uuid-cricket-non-striker",
    "runs_scored": 4,
    "extras": 0,
    "extra_type": "NONE",
    "boundary_type": "FOUR",
    "is_wicket": false,
    "shot_type": "DRIVE"
  }
}

Response: 201 Created
{
  "success": true,
  "data": {
    "event_id": "uuid-event-1",
    "validation_status": "PENDING",  // PENDING, VALIDATED, DISPUTED
    "event_hash": "sha256_hash",
    "previous_event_hash": "sha256_prev_hash",
    "sequence_number": 156,
    "requires_validation": true,
    "matching_events": []  // Empty if first scorer
  }
}

Permissions: Assigned scorer only
Side Effects:
- Creates Ball record
- Updates Innings state (runs, wickets, current_over)
- Updates BattingInnings (striker's runs)
- Updates BowlingFigures (bowler's figures)
- Triggers validation check if dual/triple scoring
```

### 4.2 Submit Wicket Event
```http
POST /api/v1/matches/{match_id}/scoring/events
Authorization: Bearer <token>

Request Body:
{
  "innings_id": "uuid-innings-1",
  "over_id": "uuid-over-1",
  "event_type": "WICKET_FALLEN",
  "event_data": {
    "ball_number": 15.4,
    "bowler_id": "uuid-cricket-bowler",
    "batsman_out_id": "uuid-cricket-batsman",
    "dismissal_type": "CAUGHT",  // ENUM: BOWLED, CAUGHT, LBW, RUN_OUT, etc.
    "fielder_ids": ["uuid-cricket-fielder-1"],
    "runs_scored": 0
  }
}

Response: 201 Created
{
  "success": true,
  "data": {
    "event_id": "uuid-event-2",
    "ball_id": "uuid-ball-2",
    "wicket_id": "uuid-wicket-1",
    "validation_status": "PENDING",
    "requires_new_batsman": true
  }
}

Side Effects:
- Creates Ball + Wicket records
- Marks BattingInnings as out
- Increments wickets in Innings
- May trigger innings end
```

### 4.3 Get Current Innings State
```http
GET /api/v1/matches/{match_id}/innings/current
Authorization: Bearer <token> (optional for public)

Response: 200 OK
{
  "success": true,
  "data": {
    "innings_id": "uuid-innings-1",
    "innings_number": 1,
    "batting_team": { /* ... */ },
    "bowling_team": { /* ... */ },
    "total_runs": 145,
    "wickets_fallen": 4,
    "current_over_number": 15,
    "balls_bowled": 92,
    "run_rate": 9.35,
    "striker": {
      "player": { /* ... */ },
      "runs": 45,
      "balls_faced": 32,
      "fours": 5,
      "sixes": 2,
      "strike_rate": 140.62
    },
    "non_striker": { /* ... */ },
    "current_bowler": {
      "player": { /* ... */ },
      "overs_bowled": "3.4",
      "runs_conceded": 28,
      "wickets": 1,
      "economy": 7.63
    },
    "last_6_balls": [
      { "runs": 4, "is_wicket": false, "ball_number": 15.4 },
      // ... 5 more
    ],
    "partnership": {
      "runs": 52,
      "balls": 34,
      "batsman1_runs": 32,
      "batsman2_runs": 20
    }
  }
}
```

### 4.4 Get Ball-by-Ball Commentary
```http
GET /api/v1/matches/{match_id}/innings/{innings_id}/balls
Authorization: Bearer <token> (optional)

Query Params:
- over_number: Filter by over (e.g., 15)
- from_ball: Start from ball number
- limit: 50 (default)
- order: DESC (latest first)

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "ball_id": "uuid-ball-1",
      "ball_number": 15.4,
      "over_number": 15,
      "bowler": { "name": "Jasprit Bumrah" },
      "batsman": { "name": "Virat Kohli" },
      "runs_scored": 4,
      "extras": 0,
      "boundary_type": "FOUR",
      "is_wicket": false,
      "shot_type": "DRIVE",
      "commentary": "Beautifully driven through covers for FOUR!",
      "validation_status": "VALIDATED",
      "timestamp": "2025-10-27T15:32:45Z"
    }
  ],
  "pagination": { /* ... */ }
}
```

---

## 📁 CATEGORY 5: SCORING INTEGRITY

### 5.1 Get Pending Validations
```http
GET /api/v1/matches/{match_id}/scoring/pending
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "event_id": "uuid-event-1",
      "ball_number": 15.4,
      "scorer_a_event": {
        "scorer": { "name": "Scorer A" },
        "event_data": { "runs": 4, "boundary": "FOUR" }
      },
      "scorer_b_event": {
        "scorer": { "name": "Scorer B" },
        "event_data": { "runs": 4, "boundary": "FOUR" }
      },
      "matches": true,
      "auto_validated": true,
      "validated_at": "2025-10-27T15:32:47Z"
    }
  ]
}

Permissions: Match officials or team captains
```

### 5.2 Get Active Disputes
```http
GET /api/v1/matches/{match_id}/scoring/disputes
Authorization: Bearer <token>

Query Params:
- status: PENDING, RESOLVED, ESCALATED, ABANDONED

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "dispute_id": "uuid-dispute-1",
      "ball_number": 12.3,
      "dispute_type": "RUNS_MISMATCH",
      "scorer_a_claim": { "runs": 4 },
      "scorer_b_claim": { "runs": 6 },
      "umpire_claim": null,
      "resolution_status": "PENDING",
      "resolution_method": null,
      "created_at": "2025-10-27T15:20:15Z"
    }
  ]
}
```

### 5.3 Resolve Dispute (Umpire Override)
```http
POST /api/v1/matches/{match_id}/scoring/disputes/{dispute_id}/resolve
Authorization: Bearer <token>

Request Body:
{
  "resolution_method": "UMPIRE_OVERRIDE",
  "umpire_event_data": {
    "runs_scored": 4,
    "boundary_type": "FOUR",
    "is_wicket": false
  },
  "notes": "Video replay confirmed boundary"
}

Response: 200 OK
{
  "success": true,
  "data": {
    "dispute_id": "uuid-dispute-1",
    "resolution_status": "RESOLVED",
    "resolution_method": "UMPIRE_OVERRIDE",
    "consensus_event_id": "uuid-consensus-1",
    "resolved_at": "2025-10-27T15:25:00Z"
  }
}

Permissions: Assigned umpire only
Side Effects:
- Creates ScoringConsensus record
- Updates match state with resolved data
- Marks dispute as RESOLVED
```

### 5.4 Get Event Audit Log
```http
GET /api/v1/matches/{match_id}/scoring/audit
Authorization: Bearer <token>

Query Params:
- from_sequence: Start from sequence number
- to_sequence: End at sequence number
- event_type: Filter by type
- limit: 100

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "event_id": "uuid-event-1",
      "sequence_number": 156,
      "event_type": "BALL_BOWLED",
      "scorer": { "name": "Scorer A" },
      "event_hash": "sha256...",
      "previous_event_hash": "sha256...",
      "signature": "hmac...",
      "validation_status": "VALIDATED",
      "timestamp": "2025-10-27T15:32:45Z",
      "hash_chain_valid": true
    }
  ]
}

Purpose: Tamper detection, audit trail, replay
```

---

## 📁 CATEGORY 6: STATISTICS & ANALYTICS

### 6.1 Get Match Summary
```http
GET /api/v1/matches/{match_id}/summary
Authorization: Bearer <token> (optional for public)

Response: 200 OK
{
  "success": true,
  "data": {
    "match_id": "uuid-match-1",
    "status": "COMPLETED",
    "result": {
      "winner_team_id": "uuid-team-1",
      "result_type": "NORMAL",
      "margin": "25 runs",
      "player_of_match_id": "uuid-cricket-1"
    },
    "team_a_summary": {
      "total_runs": 180,
      "wickets": 6,
      "overs": 20.0,
      "run_rate": 9.0,
      "extras": 12,
      "top_scorer": { "name": "Virat Kohli", "runs": 75 },
      "best_bowler": { "name": "Jasprit Bumrah", "figures": "4/28" }
    },
    "team_b_summary": {
      "total_runs": 155,
      "wickets": 10,
      "overs": 19.2,
      "run_rate": 8.01
    },
    "scoring_integrity": {
      "total_events": 245,
      "validated_events": 243,
      "disputed_events": 2,
      "dispute_rate": 0.82,
      "consensus_accuracy": 99.18,
      "completeness_score": 100.0
    },
    "milestones": [
      { "type": "FIFTY", "player": "Virat Kohli", "ball": 38 },
      { "type": "CENTURY_PARTNERSHIP", "batsmen": ["Rohit", "Virat"], "ball": 82 }
    ]
  }
}
```

### 6.2 Get Player Statistics
```http
GET /api/v1/players/{cricket_profile_id}/stats
Authorization: Bearer <token> (optional)

Query Params:
- match_type: T20, ODI, TEST
- from_date, to_date
- team_id: Filter by team

Response: 200 OK
{
  "success": true,
  "data": {
    "cricket_profile_id": "uuid-cricket-1",
    "player": { "name": "Virat Kohli" },
    "batting": {
      "matches": 150,
      "innings": 145,
      "runs": 5420,
      "highest_score": 183,
      "average": 52.15,
      "strike_rate": 138.5,
      "centuries": 12,
      "fifties": 28,
      "fours": 420,
      "sixes": 98,
      "ducks": 3
    },
    "bowling": {
      "matches": 150,
      "innings": 45,
      "wickets": 5,
      "best_figures": "2/15",
      "average": 35.2,
      "economy": 8.5,
      "strike_rate": 24.8
    },
    "recent_form": [
      { "match_id": "...", "runs": 45, "balls": 32, "sr": 140.6 },
      // Last 5 matches
    ]
  }
}
```

### 6.3 Get Team Statistics
```http
GET /api/v1/teams/{team_id}/stats
Authorization: Bearer <token> (optional)

Response: 200 OK
{
  "success": true,
  "data": {
    "overall": {
      "matches_played": 45,
      "won": 28,
      "lost": 15,
      "tied": 2,
      "win_percentage": 62.22
    },
    "batting": {
      "total_runs": 6750,
      "highest_team_total": 220,
      "lowest_team_total": 95,
      "average_score": 150.0
    },
    "bowling": {
      "total_wickets": 380,
      "best_bowling_performance": "5/12"
    },
    "top_performers": {
      "batsmen": [ /* top 5 */ ],
      "bowlers": [ /* top 5 */ ]
    }
  }
}
```

### 6.4 Leaderboards
```http
GET /api/v1/leaderboards/cricket
Authorization: Bearer <token> (optional)

Query Params:
- category: RUNS, WICKETS, BATTING_AVERAGE, STRIKE_RATE, ECONOMY
- match_type: T20, ODI, ALL
- timeframe: WEEK, MONTH, SEASON, ALL_TIME
- limit: 20

Response: 200 OK
{
  "success": true,
  "data": {
    "category": "RUNS",
    "timeframe": "MONTH",
    "updated_at": "2025-10-27T00:00:00Z",
    "rankings": [
      {
        "rank": 1,
        "player": { "id": "...", "name": "Virat Kohli" },
        "value": 450,
        "matches": 8,
        "trend": "UP"  // UP, DOWN, SAME
      }
    ]
  }
}
```

---

## 📁 CATEGORY 7: MATCH DISCOVERY

### 7.1 Discover Public Matches
```http
GET /api/v1/matches/discover
Authorization: Bearer <token> (optional)

Query Params:
- status: LIVE, SCHEDULED, COMPLETED
- near_lat, near_lng: Geo-proximity search
- radius_km: 50 (default)
- match_type: T20, ODI
- match_category: TOURNAMENT, LEAGUE

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "match": { /* match details */ },
      "distance_km": 12.5,
      "spectator_count": 245,
      "can_join": true
    }
  ]
}
```

### 7.2 Search Teams
```http
GET /api/v1/teams/search
Authorization: Bearer <token> (optional)

Query Params:
- q: "Mumbai"  (search query)
- sport_type: CRICKET
- team_type: CLUB, TOURNAMENT_REGISTERED

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "team": { /* team details */ },
      "relevance_score": 0.95,
      "member_count": 15,
      "recent_matches": 5
    }
  ]
}
```

---

## Real-time Features (WebSocket)

### WebSocket Endpoints

#### Connect to Live Match
```
WS /ws/matches/{match_id}/live
Authorization: Bearer <token> (in query param or header)

On Connect:
{
  "type": "CONNECTED",
  "data": {
    "match_id": "uuid-match-1",
    "current_state": { /* full match state */ }
  }
}

Events Received:
1. BALL_BOWLED
{
  "type": "BALL_BOWLED",
  "data": {
    "ball": { /* ball details */ },
    "innings_state": { /* updated state */ }
  },
  "timestamp": "2025-10-27T15:32:45Z"
}

2. WICKET_FALLEN
3. OVER_COMPLETE
4. INNINGS_COMPLETE
5. MATCH_COMPLETE
6. SCORING_DISPUTE_RAISED
7. DISPUTE_RESOLVED
8. PLAYER_CHANGED (batsman/bowler change)
```

#### Subscribe to Multiple Matches
```
WS /ws/matches/feed
Authorization: Bearer <token>

On Connect - Send:
{
  "action": "SUBSCRIBE",
  "match_ids": ["uuid-1", "uuid-2", "uuid-3"]
}

Receive updates from all subscribed matches
```

---

## Error Handling

### Error Codes
```
400 - VALIDATION_ERROR: Invalid input data
401 - UNAUTHORIZED: Missing or invalid token
403 - FORBIDDEN: Insufficient permissions
404 - NOT_FOUND: Resource doesn't exist
409 - CONFLICT: State conflict (e.g., match already started)
422 - UNPROCESSABLE_ENTITY: Business logic violation
429 - RATE_LIMIT_EXCEEDED: Too many requests
500 - INTERNAL_SERVER_ERROR: Server error
503 - SERVICE_UNAVAILABLE: Database/Redis down
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid match configuration",
    "details": [
      {
        "field": "overs_per_side",
        "message": "Must be between 5 and 50 for T20 format",
        "value": 100
      }
    ],
    "doc_url": "https://docs.kreeda.app/errors/validation-error"
  },
  "meta": {
    "timestamp": "2025-10-27T15:32:45Z",
    "request_id": "req_abc123",
    "path": "/api/v1/matches",
    "method": "POST"
  }
}
```

---

## Rate Limiting & Performance

### Rate Limits (Per User)
- Authentication endpoints: 5 req/min
- Read endpoints (GET): 100 req/min
- Write endpoints (POST/PUT): 30 req/min
- Scoring events: 60 req/min (1 per second)
- WebSocket connections: 10 concurrent

### Response Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1698412800
```

### Caching Strategy
- Match summaries: 5 minutes (for completed matches: 1 hour)
- Player stats: 15 minutes
- Team details: 10 minutes
- Live match state: No cache (real-time)
- Leaderboards: 1 hour

### Performance Targets
- P50: < 100ms
- P95: < 500ms
- P99: < 1000ms
- WebSocket latency: < 50ms

---

## Implementation Priority

### Phase 1 (MVP - Week 1-2)
1. ✅ Auth endpoints (existing)
2. Sport profiles + Cricket profiles
3. Team CRUD + Member management
4. Basic match creation + Playing XI

### Phase 2 (Core Scoring - Week 3-4)
5. Live scoring (ball-by-ball)
6. Innings management
7. Basic statistics (current state)
8. WebSocket for live updates

### Phase 3 (Integrity - Week 5-6)
9. Dual/triple validation
10. Dispute management
11. Consensus resolution
12. Audit log

### Phase 4 (Analytics - Week 7-8)
13. Match summaries
14. Player/team statistics
15. Leaderboards
16. Advanced analytics

### Phase 5 (Discovery - Week 9-10)
17. Public match discovery
18. Team search
19. Spectator features
20. Match recommendations

---

## API Documentation

### Tools
- **Swagger/OpenAPI**: Auto-generated from FastAPI
- **ReDoc**: Alternative UI
- **Postman Collection**: For testing
- **Code Examples**: Python, JavaScript, Dart (Flutter)

### Documentation URLs
- Swagger: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`
- API Guide: `https://docs.kreeda.app`

---

## Security Considerations

### Authentication
- JWT with RS256 signing (production)
- Refresh token rotation
- Token blacklist for logout
- Password: bcrypt with 12 rounds

### Authorization
- Resource-based access control
- Match-level permissions
- Team-level roles
- Scorer validation

### Data Protection
- HTTPS only in production
- Sensitive data encryption at rest
- PII anonymization for analytics
- GDPR compliance ready

### Input Validation
- Pydantic schema validation
- SQL injection prevention (SQLAlchemy ORM)
- XSS prevention
- CSRF protection for web clients

---

## Next Steps

1. **Review & Approve Design** ✅ (You're here!)
2. **Create Pydantic Schemas** (request/response models)
3. **Implement Service Layer** (business logic)
4. **Build API Routers** (endpoints)
5. **Add WebSocket Support** (real-time)
6. **Write Tests** (unit + integration)
7. **Deploy & Monitor** (staging → production)

---

**Ready to proceed with implementation?** Let me know if you'd like to modify any endpoint design or add new features!
