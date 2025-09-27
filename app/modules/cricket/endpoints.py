"""
Cricket API Endpoints

API routes for cricket match management and live scoring
"""

import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, asc, func
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from .models import CricketTeam as Team, Player, Match, Innings, MatchStatus, MatchFormat, InningsStatus
from .schemas import (
    # Team schemas
    Team as TeamSchema, TeamCreate, TeamUpdate, TeamSummary, TeamListResponse,
    # Player schemas  
    Player as PlayerSchema, PlayerCreate, PlayerUpdate, PlayerSummary, PlayerListResponse,
    # Match schemas
    Match as MatchSchema, MatchCreate, MatchUpdate, MatchWithTeams, MatchSummary, MatchListResponse,
    # Innings schemas
    Innings as InningsSchema, InningsCreate, InningsUpdate, InningsWithTeams,
    # Scorecard schemas
    Scorecard, LiveScore
)

router = APIRouter(prefix="/cricket", tags=["cricket"])


# Team endpoints
@router.post("/teams", response_model=TeamSchema, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new cricket team"""
    
    # Check if team name already exists
    existing_team = await db.execute(
        select(Team).where(Team.name == team_data.name)
    )
    if existing_team.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team with this name already exists"
        )
    
    # Validate captain exists if provided
    if team_data.captain_id:
        captain = await db.execute(
            select(Player).where(Player.id == team_data.captain_id)
        )
        if not captain.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Captain player not found"
            )
    
    team = Team(**team_data.model_dump())
    db.add(team)
    await db.commit()
    await db.refresh(team)
    
    return team


@router.get("/teams", response_model=TeamListResponse)
async def list_teams(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """List all cricket teams with pagination"""
    
    query = select(Team)
    
    # Add search filter
    if search:
        query = query.where(Team.name.ilike(f"%{search}%"))
        
    # Get total count
    count_query = select(func.count(Team.id))
    if search:
        count_query = count_query.where(Team.name.ilike(f"%{search}%"))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page).order_by(Team.name)
    
    result = await db.execute(query)
    teams = list(result.scalars().all())
    
    return {
        "items": teams,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total > 0 else 1
    }


@router.get("/teams/{team_id}", response_model=TeamSchema)
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific team by ID"""
    
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    return team


@router.put("/teams/{team_id}", response_model=TeamSchema)
async def update_team(
    team_id: int,
    team_data: TeamUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a team"""
    
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Validate captain exists if provided
    if team_data.captain_id:
        captain = await db.execute(
            select(Player).where(Player.id == team_data.captain_id)
        )
        if not captain.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Captain player not found"
            )
    
    # Update team fields
    update_data = team_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)
    
    await db.commit()
    await db.refresh(team)
    
    return team


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a team"""
    
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    await db.delete(team)
    await db.commit()


# Player endpoints
@router.post("/players", response_model=PlayerSchema, status_code=status.HTTP_201_CREATED)
async def create_player(
    player_data: PlayerCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new cricket player"""
    
    # Validate team exists if provided
    if player_data.team_id:
        team = await db.execute(
            select(Team).where(Team.id == player_data.team_id)
        )
        if not team.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team not found"
            )
    
    player = Player(**player_data.model_dump())
    db.add(player)
    await db.commit()
    await db.refresh(player)
    
    return player


@router.get("/players", response_model=PlayerListResponse)
async def list_players(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    team_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """List cricket players with pagination and filtering"""
    
    query = select(Player).options(selectinload(Player.team))
    
    # Add filters
    if team_id:
        query = query.where(Player.team_id == team_id)
    if search:
        query = query.where(Player.name.ilike(f"%{search}%"))
    
    # Get total count
    count_query = select(func.count(Player.id))
    if team_id:
        count_query = count_query.where(Player.team_id == team_id)
    if search:
        count_query = count_query.where(Player.name.ilike(f"%{search}%"))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page).order_by(Player.name)
    
    result = await db.execute(query)
    players = list(result.scalars().all())
    
    return {
        "items": players,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total > 0 else 1
    }


@router.get("/players/{player_id}", response_model=PlayerSchema)
async def get_player(
    player_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific player by ID"""
    
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    return player


@router.put("/players/{player_id}", response_model=PlayerSchema)
async def update_player(
    player_id: int,
    player_data: PlayerUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a player"""
    
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    # Validate team exists if provided
    if player_data.team_id:
        team = await db.execute(
            select(Team).where(Team.id == player_data.team_id)
        )
        if not team.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team not found"
            )
    
    # Update player fields
    update_data = player_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(player, field, value)
    
    await db.commit()
    await db.refresh(player)
    
    return player


# Match endpoints
@router.post("/matches", response_model=MatchSchema, status_code=status.HTTP_201_CREATED)
async def create_match(
    match_data: MatchCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new cricket match"""
    
    # Validate both teams exist and are different
    if match_data.home_team_id == match_data.away_team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Home and away teams must be different"
        )
    
    # Check both teams exist
    teams_result = await db.execute(
        select(Team).where(Team.id.in_([match_data.home_team_id, match_data.away_team_id]))
    )
    teams = teams_result.scalars().all()
    
    if len(teams) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or both teams not found"
        )
    
    match = Match(**match_data.model_dump())
    db.add(match)
    await db.commit()
    await db.refresh(match)
    
    return match


@router.get("/matches", response_model=MatchListResponse)
async def list_matches(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[MatchStatus] = Query(None),
    format: Optional[MatchFormat] = Query(None),
    team_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """List cricket matches with pagination and filtering"""
    
    query = select(Match).options(
        selectinload(Match.home_team),
        selectinload(Match.away_team)
    )
    
    # Add filters
    if status:
        query = query.where(Match.status == status)
    if format:
        query = query.where(Match.match_format == format)
    if team_id:
        query = query.where(
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        )
    
    # Get total count
    count_query = select(func.count(Match.id))
    if status:
        count_query = count_query.where(Match.status == status)
    if format:
        count_query = count_query.where(Match.match_format == format)
    if team_id:
        count_query = count_query.where(
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page).order_by(desc(Match.scheduled_start))
    
    result = await db.execute(query)
    matches = list(result.scalars().all())
    
    return {
        "items": matches,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total > 0 else 1
    }


@router.get("/matches/{match_id}", response_model=MatchWithTeams)
async def get_match(
    match_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific match by ID with team details"""
    
    result = await db.execute(
        select(Match)
        .options(
            selectinload(Match.home_team),
            selectinload(Match.away_team),
            selectinload(Match.toss_winner),
            selectinload(Match.winner)
        )
        .where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    return match


@router.put("/matches/{match_id}", response_model=MatchSchema)
async def update_match(
    match_id: int,
    match_data: MatchUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a match"""
    
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    # Validate toss winner and match winner if provided
    if match_data.toss_winner_id and match_data.toss_winner_id not in [match.home_team_id, match.away_team_id]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Toss winner must be one of the playing teams"
        )
    
    if match_data.winner_id and match_data.winner_id not in [match.home_team_id, match.away_team_id]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Match winner must be one of the playing teams"
        )
    
    # Update match fields
    update_data = match_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(match, field, value)
    
    await db.commit()
    await db.refresh(match)
    
    return match


# Innings endpoints
@router.post("/matches/{match_id}/innings", response_model=InningsSchema, status_code=status.HTTP_201_CREATED)
async def create_innings(
    match_id: int,
    innings_data: InningsCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new innings for a match"""
    
    # Validate match exists
    match_result = await db.execute(select(Match).where(Match.id == match_id))
    match = match_result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    # Validate teams are part of the match
    if innings_data.batting_team_id not in [match.home_team_id, match.away_team_id]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batting team must be one of the playing teams"
        )
    
    if innings_data.bowling_team_id not in [match.home_team_id, match.away_team_id]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bowling team must be one of the playing teams"
        )
    
    if innings_data.batting_team_id == innings_data.bowling_team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batting and bowling teams must be different"
        )
    
    # Check if innings already exists
    existing_innings = await db.execute(
        select(Innings).where(
            and_(
                Innings.match_id == match_id,
                Innings.innings_number == innings_data.innings_number
            )
        )
    )
    
    if existing_innings.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Innings with this number already exists for this match"
        )
    
    innings_data.match_id = match_id
    innings = Innings(**innings_data.model_dump())
    db.add(innings)
    await db.commit()
    await db.refresh(innings)
    
    return innings


@router.get("/matches/{match_id}/innings", response_model=List[InningsWithTeams])
async def list_match_innings(
    match_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """List all innings for a match"""
    
    # Validate match exists
    match_result = await db.execute(select(Match).where(Match.id == match_id))
    if not match_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    result = await db.execute(
        select(Innings)
        .options(
            selectinload(Innings.batting_team),
            selectinload(Innings.bowling_team)
        )
        .where(Innings.match_id == match_id)
        .order_by(Innings.innings_number)
    )
    
    return result.scalars().all()


# Live scoring endpoint (basic implementation)
@router.get("/matches/{match_id}/live", response_model=LiveScore)
async def get_live_score(
    match_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get live score for a match"""
    
    # Validate match exists
    match_result = await db.execute(select(Match).where(Match.id == match_id))
    match = match_result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    # Get current innings (latest in-progress innings)
    current_innings_result = await db.execute(
        select(Innings)
        .options(
            selectinload(Innings.batting_team),
            selectinload(Innings.bowling_team)
        )
        .where(
            and_(
                Innings.match_id == match_id,
                Innings.status == InningsStatus.IN_PROGRESS
            )
        )
        .order_by(desc(Innings.innings_number))
        .limit(1)
    )
    current_innings = current_innings_result.scalar_one_or_none()
    
    return {
        "match_id": match_id,
        "current_innings": current_innings,
        "last_ball": None,  # TODO: Implement when ball-by-ball data is available
        "recent_balls": [],  # TODO: Implement when ball-by-ball data is available
        "current_partnership": None,  # TODO: Implement partnership calculation
        "required_run_rate": None,  # TODO: Calculate required run rate
        "current_run_rate": None  # TODO: Calculate current run rate
    }