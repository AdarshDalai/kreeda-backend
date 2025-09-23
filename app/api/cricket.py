import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.middleware import get_current_active_user
from app.auth.permissions import require_match_permission
from app.models.cricket import CricketBall, CricketMatch
from app.models.user import MatchPlayingXI, User
from app.schemas.cricket import (
    BallRecord,
    BallResponse,
    CricketMatchCreate,
    CricketMatchUpdate,
    MatchResponseBasic,
    PlayingXIResponse,
    PlayingXISelection,
    TossResult,
)
from app.services.cricket_service import CricketService
from app.utils.database import get_db
from app.utils.error_handler import (
    APIError,
    InternalServerError,
    MatchNotFoundError,
    PermissionDeniedError,
    ValidationError
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def cricket_health():
    return {"success": True, "message": "Cricket service healthy"}


@router.post("/", response_model=MatchResponseBasic)
async def create_match(
    match_data: CricketMatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new cricket match"""
    try:
        # Create new match
        new_match = CricketMatch(
            team_a_id=match_data.team_a_id,
            team_b_id=match_data.team_b_id,
            overs_per_innings=match_data.overs_per_innings,
            venue=match_data.venue,
            match_date=match_data.match_date,
            created_by_id=current_user.id,
        )

        db.add(new_match)
        await db.commit()
        await db.refresh(new_match)

        logger.info(f"Match created: {new_match.id} by {current_user.username}")
        return new_match

    except Exception as e:
        logger.error(f"Failed to create match: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create match",
        )


@router.get("/", response_model=List[MatchResponseBasic])
async def get_matches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all matches"""
    try:
        result = await db.execute(
            select(CricketMatch).order_by(CricketMatch.created_at.desc())
        )
        matches = result.scalars().all()

        return matches

    except Exception as e:
        logger.error(f"Failed to get matches: {e}")
        raise InternalServerError("retrieve matches")


@router.get("/{match_id}", response_model=MatchResponseBasic)
async def get_match(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get specific match details"""
    try:
        # Check permission to view match
        match = await require_match_permission(current_user, str(match_id), "view", db)
        return match

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to get match: {e}")
        raise InternalServerError("retrieve match")


@router.post("/{match_id}/balls", response_model=BallResponse)
async def record_ball(
    match_id: uuid.UUID,
    ball_data: BallRecord,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Record a ball in the cricket match"""
    try:
        # Check permission to manage match
        match = await require_match_permission(current_user, str(match_id), "manage", db)

        # Use cricket service to record ball
        cricket_service = CricketService(db)
        ball, scorecard = await cricket_service.record_ball(str(match_id), ball_data)

        logger.info(f"Ball recorded in match {match_id}")
        return ball

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to record ball: {e}")
        raise InternalServerError("record ball")


@router.get("/{match_id}/scorecard")
async def get_scorecard(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get live scorecard for a match"""
    try:
        # Get match
        result = await db.execute(
            select(CricketMatch).where(CricketMatch.id == match_id)
        )
        match = result.scalar_one_or_none()

        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Match not found"
            )

        # Generate scorecard
        cricket_service = CricketService(db)
        scorecard = await cricket_service.get_match_scorecard(str(match_id))

        return scorecard

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scorecard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scorecard",
        )


# Match Management Endpoints
@router.post("/{match_id}/toss")
async def record_toss(
    match_id: uuid.UUID,
    toss_data: TossResult,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Record toss result (only match creator or captains can record)"""
    try:
        # Check permission using helper
        match = await require_match_permission(current_user, str(match_id), "manage", db)
        
        # Validate toss winner is one of the teams
        if toss_data.toss_winner_id not in [match.team_a_id, match.team_b_id]:
            raise ValidationError("toss_winner_id", "Toss winner must be one of the playing teams")
        
        # Update match with toss result
        await db.execute(
            update(CricketMatch)
            .where(CricketMatch.id == match_id)
            .values(
                toss_winner_id=toss_data.toss_winner_id,
                toss_decision=toss_data.toss_decision,
                updated_at=datetime.utcnow()
            )
        )
        
        await db.commit()
        
        logger.info(f"Toss recorded for match {match_id}: {toss_data.toss_winner_id} chose to {toss_data.toss_decision}")
        
        return {
            "success": True,
            "message": "Toss recorded successfully",
            "toss_winner_id": toss_data.toss_winner_id,
            "toss_decision": toss_data.toss_decision
        }
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to record toss: {e}")
        await db.rollback()
        raise InternalServerError("record toss")


@router.put("/{match_id}")
async def update_match(
    match_id: uuid.UUID,
    match_data: CricketMatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update match details (only creator can update)"""
    try:
        # Get match and check permission
        match = await require_match_permission(current_user, str(match_id), "manage", db)
        
        # Can't update if match has started
        if str(match.status) != "upcoming":
            raise ValidationError("match_status", "Cannot update match that has started")
        
        # Build update values
        update_values = {}
        
        if match_data.venue is not None:
            update_values["venue"] = match_data.venue
        if match_data.match_date is not None:
            update_values["match_date"] = match_data.match_date
        if match_data.overs_per_innings is not None:
            update_values["overs_per_innings"] = match_data.overs_per_innings
        
        # Add updated_at to all updates
        update_values["updated_at"] = datetime.utcnow()
        
        # Update match
        await db.execute(
            update(CricketMatch)
            .where(CricketMatch.id == match_id)
            .values(**update_values)
        )
        
        await db.commit()
        
        # Get updated match
        updated_result = await db.execute(
            select(CricketMatch).where(CricketMatch.id == match_id)
        )
        updated_match = updated_result.scalar_one()
        
        logger.info(f"Match {match_id} updated by {current_user.username}")
        
        return updated_match
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to update match: {e}")
        await db.rollback()
        raise InternalServerError("update match")


@router.delete("/{match_id}")
async def cancel_match(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel match (only creator can cancel)"""
    try:
        # Get match and check permission
        match = await require_match_permission(current_user, str(match_id), "manage", db)
        
        # Can't cancel completed matches
        if str(match.status) == "completed":
            raise ValidationError("match_status", "Cannot cancel completed match")
        
        # Update status to cancelled
        await db.execute(
            update(CricketMatch)
            .where(CricketMatch.id == match_id)
            .values(
                status="cancelled",
                updated_at=datetime.utcnow()
            )
        )
        
        await db.commit()
        
        logger.info(f"Match {match_id} cancelled by {current_user.username}")
        
        return {
            "success": True,
            "message": "Match cancelled successfully"
        }
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel match: {e}")
        await db.rollback()
        raise InternalServerError("cancel match")


# Playing XI Management
@router.post("/{match_id}/playing-xi")
async def set_playing_xi(
    match_id: uuid.UUID,
    playing_xi: PlayingXISelection,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Set playing XI for a team (only captain can set)"""
    try:
        # Validate match exists and get it
        match = await require_match_permission(current_user, str(match_id), "view", db)
        
        # Validate team is part of match
        if playing_xi.team_id not in [match.team_a_id, match.team_b_id]:
            raise ValidationError("team_id", "Team is not part of this match")
        
        # Check if user is captain of the team or match creator
        from app.auth.permissions import TeamPermissions
        from app.models.user import Team
        
        team_result = await db.execute(
            select(Team).where(Team.id == playing_xi.team_id)
        )
        team = team_result.scalar_one_or_none()
        
        if not team:
            raise ValidationError("team_id", "Team not found")
        
        # Check permission - captain or match creator
        is_captain = str(team.captain_id) == str(current_user.id)
        is_match_creator = str(match.created_by_id) == str(current_user.id)
        
        if not (is_captain or is_match_creator):
            raise PermissionDeniedError("set playing XI for this team")
        
        # Validate exactly one captain and one wicket keeper
        captains = [p for p in playing_xi.players if p.is_captain]
        wicket_keepers = [p for p in playing_xi.players if p.is_wicket_keeper]
        
        if len(captains) != 1:
            raise ValidationError("captains", "Exactly one captain must be selected")
        
        if len(wicket_keepers) != 1:
            raise ValidationError("wicket_keepers", "Exactly one wicket keeper must be selected")
        
        # Clear existing playing XI for this team
        await db.execute(
            delete(MatchPlayingXI)
            .where(MatchPlayingXI.match_id == match_id)
            .where(MatchPlayingXI.team_id == playing_xi.team_id)
        )
        
        # Add new playing XI
        playing_xi_records = []
        for player in playing_xi.players:
            playing_xi_records.append(
                MatchPlayingXI(
                    match_id=match_id,
                    team_id=playing_xi.team_id,
                    player_id=player.player_id,
                    batting_order=player.batting_order,
                    is_captain=player.is_captain,
                    is_wicket_keeper=player.is_wicket_keeper
                )
            )
        
        db.add_all(playing_xi_records)
        await db.commit()
        
        logger.info(f"Playing XI set for team {playing_xi.team_id} in match {match_id}")
        
        return {
            "success": True,
            "message": "Playing XI set successfully",
            "players_count": len(playing_xi.players)
        }
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to set playing XI: {e}")
        await db.rollback()
        raise InternalServerError("set playing XI")


@router.get("/{match_id}/playing-xi/{team_id}", response_model=List[PlayingXIResponse])
async def get_playing_xi(
    match_id: uuid.UUID,
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get playing XI for a team in a match"""
    try:
        # Check permission to view match
        await require_match_permission(current_user, str(match_id), "view", db)
        
        # Get playing XI
        result = await db.execute(
            select(MatchPlayingXI)
            .where(MatchPlayingXI.match_id == match_id)
            .where(MatchPlayingXI.team_id == team_id)
            .options(selectinload(MatchPlayingXI.player))
            .order_by(MatchPlayingXI.batting_order)
        )
        playing_xi = result.scalars().all()
        
        return playing_xi
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to get playing XI: {e}")
        raise InternalServerError("retrieve playing XI")
