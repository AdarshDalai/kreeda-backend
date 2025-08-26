"""
Cricket API Routes - Fast and focused on MVP functionality
Team management, match creation, and live scoring endpoints
Now with proper authentication!
"""
from typing import List, Annotated
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models.cricket import Team, Player, Match, Innings, User, Ball
from app.schemas.cricket import (
    TeamCreate, TeamResponse, TeamWithPlayers,
    PlayerCreate, PlayerResponse, PlayerUpdate,
    MatchCreate, MatchResponse, TossResult,
    BallCreate, LiveScore
)
from app.services.cricket_scoring import CricketScoringService
from app.core.exceptions import (
    KreedaBaseException, convert_to_http_exception,
    TeamNotFoundException, SameTeamException, MatchNotFoundException,
    MatchNotInProgressException, InningsNotFoundException
)

router = APIRouter(prefix="/api/cricket", tags=["cricket"])


# Team Management
@router.post("/teams", response_model=TeamResponse)
def create_team(
    team_data: TeamCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Create a new cricket team"""
    team = Team(
        name=team_data.name,
        short_name=team_data.short_name,
        created_by=current_user.id  # Now using authenticated user
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("/teams/{team_id}", response_model=TeamWithPlayers)
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Get team with players"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.get("/teams", response_model=List[TeamResponse])
def list_teams(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all teams"""
    teams = db.query(Team).offset(skip).limit(limit).all()
    return teams


# Player Management
@router.post("/teams/{team_id}/players", response_model=PlayerResponse)
def add_player(
    team_id: int,
    player_data: PlayerCreate,
    db: Session = Depends(get_db)
):
    """Add player to team"""
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    player = Player(
        team_id=team_id,
        name=player_data.name,
        jersey_number=player_data.jersey_number
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@router.put("/players/{player_id}", response_model=PlayerResponse)
def update_player(
    player_id: int,
    player_data: PlayerUpdate,
    db: Session = Depends(get_db)
):
    """Update player details"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    for field, value in player_data.dict(exclude_unset=True).items():
        setattr(player, field, value)
    
    db.commit()
    db.refresh(player)
    return player


# Match Management
@router.post("/matches", response_model=MatchResponse)
def create_match(
    match_data: MatchCreate,
    db: Session = Depends(get_db)
):
    """Create a new cricket match"""
    # Verify teams exist
    team_a = db.query(Team).filter(Team.id == match_data.team_a_id).first()
    team_b = db.query(Team).filter(Team.id == match_data.team_b_id).first()
    
    if not team_a or not team_b:
        raise HTTPException(status_code=404, detail="One or both teams not found")
    
    if match_data.team_a_id == match_data.team_b_id:
        raise HTTPException(status_code=400, detail="Teams cannot play against themselves")
    
    # Create match with only the fields that exist in the model
    match = Match(
        team_a_id=match_data.team_a_id,
        team_b_id=match_data.team_b_id,
        overs_per_side=match_data.overs_per_side,
        venue=match_data.venue
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.post("/matches/{match_id}/toss", response_model=MatchResponse)
def set_toss_result(
    match_id: int,
    toss_data: TossResult,
    db: Session = Depends(get_db)
):
    """Set toss result and batting order"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if match.status != 'not_started':
        raise HTTPException(status_code=400, detail="Toss already completed")
    
    match.toss_winner_id = toss_data.toss_winner_id
    match.batting_first_id = toss_data.batting_first_id
    
    db.commit()
    db.refresh(match)
    return match


@router.post("/matches/{match_id}/start", response_model=MatchResponse)
def start_match(match_id: int, db: Session = Depends(get_db)):
    """Start the match and create first innings"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if match.status != 'not_started':
        raise HTTPException(status_code=400, detail="Match already started")
    
    if not match.batting_first_id:
        raise HTTPException(status_code=400, detail="Toss not completed")
    
    # Create first innings
    bowling_first_id = (match.team_b_id if match.batting_first_id == match.team_a_id 
                       else match.team_a_id)
    
    innings = Innings(
        match_id=match_id,
        innings_number=1,
        batting_team_id=match.batting_first_id,
        bowling_team_id=bowling_first_id
    )
    
    match.status = 'innings_1'
    match.current_innings = 1
    
    db.add(innings)
    db.commit()
    db.refresh(match)
    return match


@router.get("/matches/{match_id}", response_model=MatchResponse)
def get_match(match_id: int, db: Session = Depends(get_db)):
    """Get match details"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


# Live Scoring - The core functionality!
@router.post("/matches/{match_id}/ball")
def record_ball(
    match_id: int,
    ball_data: BallCreate,
    db: Session = Depends(get_db)
):
    """Record a cricket ball - The heart of the app!"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if match.status not in ['innings_1', 'innings_2']:
        raise HTTPException(status_code=400, detail="Match not in progress")
    
    # Get current innings
    current_innings = (db.query(Innings)
                      .filter(Innings.match_id == match_id, 
                             Innings.innings_number == match.current_innings)
                      .first())
    
    if not current_innings:
        raise HTTPException(status_code=400, detail="No active innings found")
    
    if current_innings.is_completed:
        raise HTTPException(status_code=400, detail="Innings already completed")
    
    # Use scoring service
    scoring_service = CricketScoringService(db)
    try:
        ball, live_score = scoring_service.record_ball(current_innings.id, ball_data)
        return {
            "ball": ball,
            "live_score": live_score,
            "message": "Ball recorded successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/matches/{match_id}/live", response_model=LiveScore)
def get_live_score(match_id: int, db: Session = Depends(get_db)):
    """Get live score - Must be fast for real-time updates!"""
    scoring_service = CricketScoringService(db)
    try:
        return scoring_service.get_live_score(match_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/matches/{match_id}/last-ball")
def undo_last_ball(
    match_id: int, 
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Undo last ball - Essential for fixing mistakes"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Get current innings
    current_innings = (db.query(Innings)
                      .filter(Innings.match_id == match_id, 
                             Innings.innings_number == match.current_innings)
                      .first())
    
    if not current_innings:
        raise HTTPException(status_code=400, detail="No active innings found")
    
    # Get last ball
    last_ball = (db.query(Ball)
                .filter(Ball.innings_id == current_innings.id)
                .order_by(desc(Ball.id))
                .first())
    
    if not last_ball:
        raise HTTPException(status_code=400, detail="No balls to undo")
    
    # Store ball data for response
    ball_data = {
        "id": last_ball.id,
        "over_number": last_ball.over_number,
        "ball_number": last_ball.ball_number,
        "runs": last_ball.runs,
        "extras": last_ball.extras,
        "is_wicket": last_ball.is_wicket
    }
    
    # Update innings statistics (reverse the ball)
    current_innings.total_runs -= (last_ball.runs + last_ball.extras)
    current_innings.extras -= last_ball.extras
    
    if last_ball.is_wicket:
        current_innings.wickets_lost -= 1
    
    if last_ball.is_valid_ball:
        # Recalculate overs completed
        total_balls = (db.query(Ball)
                      .filter(Ball.innings_id == current_innings.id, 
                             Ball.is_valid_ball == True,
                             Ball.id != last_ball.id)
                      .count())
        current_innings.overs_completed = Decimal(total_balls // 6) + Decimal((total_balls % 6) / 10)
    
    # Delete the ball
    db.delete(last_ball)
    db.commit()
    
    return {
        "message": "Last ball undone successfully",
        "undone_ball": ball_data,
        "innings_stats": {
            "total_runs": current_innings.total_runs,
            "wickets_lost": current_innings.wickets_lost,
            "overs_completed": str(current_innings.overs_completed)
        }
    }


# Quick health check
@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "cricket-api"}
