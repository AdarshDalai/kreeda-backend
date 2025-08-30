"""
Kreeda Cricket DynamoDB Schema Reference
Single Table Design for optimal NoSQL performance
This file documents the DynamoDB schema structure - NOT SQLAlchemy models
"""
from typing import Dict, Any, List
from app.core.database import Base  # For backward compatibility


# DynamoDB Single Table Schema Reference
# This is for documentation purposes only

DYNAMODB_SCHEMA = {
    "TableName": "kreeda-cricket-data",
    "KeySchema": [
        {"AttributeName": "PK", "KeyType": "HASH"},   # Partition Key
        {"AttributeName": "SK", "KeyType": "RANGE"}   # Sort Key
    ],
    "GlobalSecondaryIndexes": [
        {
            "IndexName": "GSI1",
            "KeySchema": [
                {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                {"AttributeName": "GSI1SK", "KeyType": "RANGE"}
            ]
        }
    ]
}

# Entity Key Patterns
KEY_PATTERNS = {
    "USER": {
        "PK": "USER#{user_id}",
        "SK": "USER#{user_id}",
        "GSI1PK": "USER",
        "GSI1SK": "USER#{username}"
    },
    "TEAM": {
        "PK": "TEAM#{team_id}",
        "SK": "TEAM#{team_id}",
        "GSI1PK": "USER#{created_by}",
        "GSI1SK": "TEAM#{team_id}"
    },
    "PLAYER": {
        "PK": "TEAM#{team_id}",
        "SK": "PLAYER#{player_id}",
        "GSI1PK": "TEAM#{team_id}",
        "GSI1SK": "PLAYER#{player_id}"
    },
    "MATCH": {
        "PK": "MATCH#{match_id}",
        "SK": "MATCH#{match_id}",
        "GSI1PK": "TEAM#{team_a_id}",
        "GSI1SK": "MATCH#{match_id}"
    },
    "INNINGS": {
        "PK": "MATCH#{match_id}",
        "SK": "INNINGS#{innings_number}",
        "GSI1PK": "MATCH#{match_id}",
        "GSI1SK": "INNINGS#{innings_number}"
    },
    "BALL": {
        "PK": "MATCH#{match_id}",
        "SK": "BALL#{innings_number}#{ball_number}",
        "GSI1PK": "INNINGS#{match_id}#{innings_number}",
        "GSI1SK": "BALL#{ball_number}"
    }
}

# Entity Attribute Patterns
USER_ATTRIBUTES = {
    "id": "string",           # UUID
    "username": "string",     # Unique username
    "email": "string",        # Unique email
    "hashed_password": "string", # Bcrypt hash
    "full_name": "string",    # Display name
    "created_at": "string"    # ISO datetime
}

TEAM_ATTRIBUTES = {
    "id": "string",           # UUID
    "name": "string",         # Team name
    "short_name": "string",   # Short name for scoreboard
    "created_by": "string",   # User ID who created the team
    "created_at": "string"    # ISO datetime
}

PLAYER_ATTRIBUTES = {
    "id": "string",           # UUID
    "name": "string",         # Player name
    "jersey_number": "number", # Jersey number
    "team_id": "string",      # Team ID
    "created_at": "string"    # ISO datetime
}

MATCH_ATTRIBUTES = {
    "id": "string",           # UUID
    "team_a_id": "string",    # Team A ID
    "team_b_id": "string",    # Team B ID
    "overs_per_side": "number", # Overs per innings
    "venue": "string",        # Match venue
    "status": "string",       # scheduled, in_progress, completed
    "toss_winner": "string",  # Team ID who won toss
    "batting_first": "string", # Team ID batting first
    "current_innings": "number", # Current innings number
    "created_at": "string"    # ISO datetime
}

INNINGS_ATTRIBUTES = {
    "match_id": "string",     # Match ID
    "innings_number": "number", # 1 or 2
    "batting_team_id": "string", # Team ID batting
    "bowling_team_id": "string", # Team ID bowling
    "total_runs": "number",   # Total runs scored
    "total_wickets": "number", # Total wickets fallen
    "total_overs": "number",  # Total overs bowled
    "is_completed": "boolean" # Whether innings is complete
}

BALL_ATTRIBUTES = {
    "match_id": "string",     # Match ID
    "innings_number": "number", # Innings number
    "ball_number": "number",  # Ball number in innings
    "batsman_id": "string",   # Batsman player ID
    "bowler_id": "string",    # Bowler player ID
    "runs_scored": "number",  # Runs scored on this ball
    "is_wicket": "boolean",   # Whether wicket fell
    "wicket_type": "string",  # Type of wicket (bowled, caught, etc.)
    "extras": "number",       # Extra runs
    "extra_type": "string"    # Type of extra (wide, no-ball, etc.)
}


# Mock classes for backward compatibility with tests
class User:
    """Mock User class for test compatibility"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class Team:
    """Mock Team class for test compatibility"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class Player:
    """Mock Player class for test compatibility"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class Match:
    """Mock Match class for test compatibility"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class Innings:
    """Mock Innings class for test compatibility"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class Ball:
    """Mock Ball class for test compatibility"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
