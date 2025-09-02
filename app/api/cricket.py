from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging
import uuid
import json

from app.utils.database import get_db
from app.models.user import User
from app.models.cricket import CricketMatch, CricketBall, MatchPlayerStats
from app.schemas.cricket import (
    CricketMatchCreate, CricketMatchResponse, BallRecord, BallResponse,
    Scorecard
)
from app.auth.middleware import get_current_active_user
from app.services.cricket_service import CricketService
from app.utils.websocket import WebSocketManager

logger = logging.getLogger(__name__)

router = APIRouter()
websocket_manager = WebSocketManager()


@router.get("/health")
async def cricket_health():
    return {"success": True, "message": "Cricket service healthy"}


@router.post("/matches", response_model=CricketMatchResponse)
async def create_match(
    match_data: CricketMatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new cricket match"""
    try:
        cricket_service = CricketService(db)
        match = await cricket_service.create_match(match_data, current_user.id)
        
        logger.info(f"Match created: {match.id} by {current_user.username}")
        return match
        
    except Exception as e:
        logger.error(f"Failed to create match: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create match"
        )


@router.get("/matches", response_model=List[CricketMatchResponse])
async def get_matches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all matches for current user's teams"""
    try:
        cricket_service = CricketService(db)
        matches = await cricket_service.get_user_matches(current_user.id)
        
        return matches
        
    except Exception as e:
        logger.error(f"Failed to get matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve matches"
        )


@router.get("/matches/{match_id}", response_model=CricketMatchResponse)
async def get_match(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific match details"""
    try:
        result = await db.execute(
            select(CricketMatch).where(CricketMatch.id == match_id)
        )
        match = result.scalar_one_or_none()
        
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found"
            )
        
        return match
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get match: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve match"
        )


@router.post("/matches/{match_id}/start")
async def start_match(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start a cricket match"""
    try:
        cricket_service = CricketService(db)
        await cricket_service.start_match(match_id, current_user.id)
        
        # Broadcast match start
        await websocket_manager.broadcast(f"match:{match_id}", {
            "type": "match_started",
            "match_id": str(match_id)
        })
        
        logger.info(f"Match {match_id} started by {current_user.username}")
        return {"message": "Match started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start match: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start match"
        )


@router.post("/matches/{match_id}/balls", response_model=BallResponse)
async def record_ball(
    match_id: uuid.UUID,
    ball_data: BallRecord,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Record a ball in the cricket match"""
    try:
        cricket_service = CricketService(db)
        ball = await cricket_service.record_ball(match_id, ball_data, current_user.id)
        
        # Get updated scorecard
        scorecard = await cricket_service.get_scorecard(match_id)
        
        # Broadcast ball update
        await websocket_manager.broadcast(f"match:{match_id}", {
            "type": "ball_recorded",
            "ball": {
                "id": str(ball.id),
                "runs_scored": ball.runs_scored,
                "is_wicket": ball.is_wicket,
                "is_extra": ball.is_extra,
                "extra_type": ball.extra_type
            },
            "scorecard": scorecard.dict() if scorecard else None
        })
        
        logger.info(f"Ball recorded in match {match_id}")
        return ball
        
    except Exception as e:
        logger.error(f"Failed to record ball: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record ball"
        )


@router.get("/matches/{match_id}/scorecard", response_model=Scorecard)
async def get_scorecard(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get live scorecard for a match"""
    try:
        cricket_service = CricketService(db)
        scorecard = await cricket_service.get_scorecard(match_id)
        
        if not scorecard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scorecard not found"
            )
        
        return scorecard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scorecard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scorecard"
        )


@router.websocket("/matches/{match_id}/live")
async def live_match_updates(websocket: WebSocket, match_id: uuid.UUID):
    """WebSocket endpoint for live match updates"""
    await websocket_manager.connect(websocket, f"match:{match_id}")
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            logger.info(f"Received message from client: {data}")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, f"match:{match_id}")
        logger.info(f"Client disconnected from match {match_id}")


@router.post("/matches/{match_id}/complete")
async def complete_match(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Complete a cricket match"""
    try:
        cricket_service = CricketService(db)
        await cricket_service.complete_match(match_id, current_user.id)
        
        # Broadcast match completion
        await websocket_manager.broadcast(f"match:{match_id}", {
            "type": "match_completed",
            "match_id": str(match_id)
        })
        
        logger.info(f"Match {match_id} completed by {current_user.username}")
        return {"message": "Match completed successfully"}
        
    except Exception as e:
        logger.error(f"Failed to complete match: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete match"
        )
