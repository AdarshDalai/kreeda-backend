"""
Cricket API Routes - Version 1
Complete DynamoDB Implementation with API versioning
"""
from typing import List, Annotated
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.cricket import (
    TeamCreate, TeamResponse, TeamWithPlayers,
    PlayerCreate, PlayerResponse, PlayerUpdate,
    MatchCreate, MatchResponse, TossResult,
    BallCreate, LiveScore
)
from app.services.dynamodb_cricket_scoring import DynamoDBService
from app.core.exceptions import (
    KreedaBaseException, convert_to_http_exception,
    TeamNotFoundException, SameTeamException, MatchNotFoundException,
    MatchNotInProgressException, InningsNotFoundException
)
from app.core.validation import validator

router = APIRouter(tags=["cricket-v1"])

# Global DynamoDB service instance for all operations
db_service = DynamoDBService()


# Team Management
@router.post("/teams", response_model=TeamResponse)
def create_team(
    team_data: TeamCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Create a new cricket team with input validation - Version 1"""
    try:
        # Validate and sanitize input
        validated_name = validator.validate_team_name(team_data.name)
        validated_short_name = validator.validate_team_name(team_data.short_name)

        # Validate optional fields
        validated_city = None
        if team_data.city:
            validated_city = validator.validate_team_name(team_data.city)

        validated_coach = None
        if team_data.coach:
            validated_coach = validator.validate_name(team_data.coach)

        validated_home_ground = None
        if team_data.home_ground:
            validated_home_ground = validator.validate_venue(team_data.home_ground)

        team_dict = {
            "name": validated_name,
            "short_name": validated_short_name,
            "city": validated_city,
            "coach": validated_coach,
            "home_ground": validated_home_ground
        }

        team = db_service.create_team(team_dict, str(current_user.id))

        return TeamResponse(
            id=team["id"],
            name=team["name"],
            short_name=team["short_name"],
            created_by=team["created_by"],
            created_at=team["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team: {str(e)}"
        )


@router.get("/teams/{team_id}", response_model=TeamWithPlayers)
def get_team(team_id: str):
    """Get team with players - Version 1"""
    try:
        # Validate team_id format
        validator.validate_uuid(team_id, "Team ID")

        team = db_service.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Get players for this team
        players_data = db_service.get_team_players(team_id)

        # Convert to PlayerResponse objects
        players = []
        for player_data in players_data:
            players.append(PlayerResponse(
                id=player_data.get("id", ""),
                team_id=player_data.get("team_id", ""),
                name=player_data.get("name", ""),
                jersey_number=player_data.get("jersey_number"),
                batting_order=player_data.get("batting_order"),
                is_captain=player_data.get("is_captain", False),
                is_wicket_keeper=player_data.get("is_wicket_keeper", False),
                created_at=player_data.get("created_at", "")
            ))

        return TeamWithPlayers(
            id=team["id"],
            name=team["name"],
            short_name=team["short_name"],
            created_by=team["created_by"],
            created_at=team["created_at"],
            players=players
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team: {str(e)}"
        )


@router.get("/teams", response_model=List[TeamResponse])
def list_teams(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100
):
    """List all teams for the current user - Version 1"""
    try:
        teams = db_service.get_user_teams(str(current_user.id))
        return teams
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list teams: {str(e)}"
        )


# Player Management
@router.post("/teams/{team_id}/players", response_model=PlayerResponse)
def add_player(team_id: str, player_data: PlayerCreate):
    """Add player to team - Version 1"""
    try:
        # Verify team exists
        team = db_service.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        player_dict = {
            "name": player_data.name,
            "jersey_number": player_data.jersey_number
        }

        player = db_service.add_player_to_team(team_id, player_dict)

        return PlayerResponse(
            id=player["id"],
            team_id=player["team_id"],
            name=player["name"],
            jersey_number=player["jersey_number"],
            created_at=player["created_at"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add player: {str(e)}"
        )


@router.put("/players/{player_id}", response_model=PlayerResponse)
def update_player(player_id: str, player_data: PlayerUpdate):
    """Update player details - Version 1"""
    try:
        # Convert Pydantic model to dict, excluding None values
        update_data = player_data.model_dump(exclude_unset=True, exclude_none=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update"
            )

        updated_player = db_service.update_player(player_id, update_data)

        if not updated_player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )

        return PlayerResponse(
            id=updated_player["id"],
            team_id=updated_player["team_id"],
            name=updated_player["name"],
            jersey_number=updated_player.get("jersey_number"),
            batting_order=updated_player.get("batting_order"),
            is_captain=updated_player.get("is_captain", False),
            is_wicket_keeper=updated_player.get("is_wicket_keeper", False),
            created_at=updated_player["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update player: {str(e)}"
        )


# Match Management
@router.post("/matches", response_model=MatchResponse)
def create_match(match_data: MatchCreate):
    """Create a new cricket match - Version 1"""
    try:
        # Verify teams exist
        team_a = db_service.get_team(str(match_data.team_a_id))
        team_b = db_service.get_team(str(match_data.team_b_id))

        if not team_a or not team_b:
            raise HTTPException(status_code=404, detail="One or both teams not found")

        if str(match_data.team_a_id) == str(match_data.team_b_id):
            raise HTTPException(status_code=400, detail="Teams cannot play against themselves")

        match_dict = {
            "team_a_id": str(match_data.team_a_id),
            "team_b_id": str(match_data.team_b_id),
            "overs_per_side": match_data.overs_per_side,
            "venue": match_data.venue
        }

        match = db_service.create_match(match_dict)

        return MatchResponse(
            id=match["id"],
            team_a_id=match["team_a_id"],
            team_b_id=match["team_b_id"],
            overs_per_side=match["overs_per_side"],
            venue=match["venue"],
            status=match["status"],
            created_at=match["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create match: {str(e)}"
        )


@router.post("/matches/{match_id}/toss", response_model=MatchResponse)
def set_toss_result(match_id: str, toss_data: TossResult):
    """Set toss result and batting order - Version 1"""
    try:
        match = db_service.get_match(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        # Update match with toss result
        updated_match = db_service.update_match_toss(match_id, toss_data.dict())

        return MatchResponse(
            id=updated_match["id"],
            team_a_id=updated_match["team_a_id"],
            team_b_id=updated_match["team_b_id"],
            overs_per_side=updated_match["overs_per_side"],
            venue=updated_match["venue"],
            status=updated_match["status"],
            toss_winner=updated_match.get("toss_winner"),
            batting_first=updated_match.get("batting_first"),
            created_at=updated_match["created_at"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set toss result: {str(e)}"
        )


@router.post("/matches/{match_id}/start", response_model=MatchResponse)
def start_match(match_id: str):
    """Start the match - Version 1"""
    try:
        match = db_service.get_match(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        if match.get('status') != 'scheduled':
            raise HTTPException(status_code=400, detail="Match already started")

        # For MVP, we'll implement a simple start mechanism
        # Update match status to in_progress
        updated_match = db_service.update_match_status(match_id, 'in_progress')

        return MatchResponse(
            id=updated_match["id"],
            team_a_id=updated_match["team_a_id"],
            team_b_id=updated_match["team_b_id"],
            overs_per_side=updated_match["overs_per_side"],
            venue=updated_match.get("venue"),
            status=updated_match["status"],
            toss_winner=updated_match.get("toss_winner_id"),
            batting_first=updated_match.get("batting_first_id"),
            created_at=updated_match["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start match: {str(e)}"
        )


@router.get("/matches/{match_id}", response_model=MatchResponse)
def get_match(match_id: str):
    """Get match details - Version 1"""
    try:
        match = db_service.get_match(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        return MatchResponse(
            id=match["id"],
            team_a_id=match["team_a_id"],
            team_b_id=match["team_b_id"],
            overs_per_side=match["overs_per_side"],
            venue=match["venue"],
            status=match["status"],
            toss_winner=match.get("toss_winner"),
            batting_first=match.get("batting_first"),
            created_at=match["created_at"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get match: {str(e)}"
        )


# Live Scoring - The core functionality!
@router.post("/matches/{match_id}/ball")
def record_ball(
    match_id: str,
    ball_data: BallCreate
):
    """Record a cricket ball - The heart of the app! - Version 1"""
    try:
        match = db_service.get_match(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        if match.get('status') not in ['in_progress']:
            raise HTTPException(status_code=400, detail="Match not in progress")

        # Record ball using DynamoDB service
        ball_response = db_service.record_ball(
            match_id,
            1,  # innings_number - simplified for MVP
            ball_data.dict()
        )

        return {
            "ball": ball_response,
            "message": "Ball recorded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record ball: {str(e)}"
        )


@router.get("/matches/{match_id}/live", response_model=LiveScore)
def get_live_score(match_id: str):
    """Get live score - Must be fast for real-time updates! - Version 1"""
    try:
        return db_service.get_live_score(match_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get live score: {str(e)}"
        )


@router.delete("/matches/{match_id}/last-ball")
def undo_last_ball(
    match_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Undo last ball - Essential for fixing mistakes - Version 1"""
    try:
        # Verify match exists and is in progress
        match = db_service.get_match(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        if match.get('status') not in ['in_progress']:
            raise HTTPException(status_code=400, detail="Match not in progress")

        # Undo the last ball
        success = db_service.undo_last_ball(match_id, 1)  # First innings for MVP

        if not success:
            raise HTTPException(status_code=400, detail="No balls to undo")

        return {
            "message": "Last ball undone successfully",
            "match_id": match_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to undo last ball: {str(e)}"
        )

# Quick health check
@router.get("/health")
def health_check():
    """Health check endpoint - Version 1"""
    return {"status": "healthy", "service": "cricket-api", "version": "v1"}
