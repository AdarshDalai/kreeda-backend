"""
WebSocket Router for Live Cricket Match Updates

Provides real-time WebSocket connections for spectators to receive live
ball-by-ball updates during cricket matches.

Endpoint: ws://localhost:8000/api/v1/cricket/ws/matches/{match_id}/live?token=<jwt>

Author: AI Coding Agent (Professional Standards)
Date: November 1, 2025
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from src.core.websocket_manager import get_connection_manager, ConnectionManager
from src.core.security import decode_access_token
from src.database.connection import get_db
from src.models.cricket.match import Match
from src.models.cricket.innings import Innings
from src.schemas.cricket.websocket import (
    WebSocketEventType,
    ConnectionEstablishedData,
    CurrentInningsData,
    BatsmanStatsSchema,
    BowlerStatsSchema
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_current_match_state(
    match_id: UUID,
    db: AsyncSession
) -> dict:
    """
    Get current match state for initial connection message.
    
    Args:
        match_id: Match UUID
        db: Database session
        
    Returns:
        Dictionary with current match state (or minimal state if match not started)
    """
    # Get match with relationships
    query = (
        select(Match)
        .where(Match.id == match_id)
        .options(
            selectinload(Match.team_a),
            selectinload(Match.team_b)
        )
    )
    result = await db.execute(query)
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Get current innings if match is in progress
    current_innings_data = None
    striker_data = None
    non_striker_data = None
    bowler_data = None
    
    if match.match_status in ["IN_PROGRESS", "INNINGS_BREAK"]:
        # Get current innings
        innings_query = (
            select(Innings)
            .where(Innings.match_id == match_id)
            .where(Innings.is_completed == False)
            .options(
                selectinload(Innings.batting_team),
                selectinload(Innings.bowling_team)
            )
        )
        innings_result = await db.execute(innings_query)
        current_innings = innings_result.scalar_one_or_none()
        
        if current_innings:
            # TODO: Get actual batsman/bowler stats from BallService aggregations
            # For now, return basic innings data
            current_innings_data = CurrentInningsData(
                innings_number=current_innings.innings_number,
                batting_team_id=current_innings.batting_team_id,
                batting_team_name=current_innings.batting_team.name,
                bowling_team_id=current_innings.bowling_team_id,
                bowling_team_name=current_innings.bowling_team.name,
                score=f"{current_innings.total_runs}/{current_innings.total_wickets}",
                overs=float(current_innings.total_overs),
                run_rate=current_innings.run_rate,
                required_rate=current_innings.required_run_rate
            )
    
    return {
        "type": WebSocketEventType.CONNECTION_ESTABLISHED,
        "data": {
            "match_id": str(match.id),
            "match_code": match.match_code,
            "match_status": match.match_status,
            "current_innings": current_innings_data.dict() if current_innings_data else None,
            "striker": striker_data.dict() if striker_data else None,
            "non_striker": non_striker_data.dict() if non_striker_data else None,
            "bowler": bowler_data.dict() if bowler_data else None
        }
    }


@router.websocket("/matches/{match_id}/live")
async def websocket_live_match(
    websocket: WebSocket,
    match_id: UUID,
    token: str = Query(..., description="JWT authentication token"),
    db: AsyncSession = Depends(get_db),
    manager: ConnectionManager = Depends(get_connection_manager)
):
    """
    WebSocket endpoint for live match updates.
    
    **Authentication**: JWT token required via query parameter
    
    **Events Received by Client**:
    - CONNECTION_ESTABLISHED: Initial state on connect
    - BALL_BOWLED: Every legal delivery
    - WICKET_FALLEN: Dismissals
    - OVER_COMPLETE: End of over
    - INNINGS_COMPLETE: Innings finished
    - MATCH_COMPLETE: Match finished
    - SCORING_DISPUTE_RAISED: Scorer disagreement
    - DISPUTE_RESOLVED: Consensus reached
    - PLAYER_CHANGED: Batsman/bowler rotation
    - MILESTONE_ACHIEVED: Fifties, centuries, etc.
    - ERROR: Authentication/system errors
    
    **Usage**:
    ```javascript
    const ws = new WebSocket(
        'ws://localhost:8000/api/v1/cricket/ws/matches/{match_id}/live?token=<jwt>'
    );
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Event:', data.type, data.data);
    };
    ```
    
    **Connection Flow**:
    1. Client connects with JWT token
    2. Server validates token
    3. If valid: Accept connection, send initial state
    4. Client receives real-time events as match progresses
    5. Connection auto-closed on token expiry or client disconnect
    """
    # Validate JWT token
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid or expired token")
        logger.warning(f"WebSocket connection rejected: invalid token for match {match_id}")
        return
    
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008, reason="Invalid token payload")
        logger.warning(f"WebSocket connection rejected: invalid payload for match {match_id}")
        return
    
    # Accept connection and add to room
    await manager.connect(websocket, str(match_id))
    
    logger.info(
        f"WebSocket connected: user={user_id}, match={match_id}, "
        f"room_size={manager.get_room_size(str(match_id))}"
    )
    
    try:
        # Send initial match state
        initial_state = await _get_current_match_state(match_id, db)
        await manager.send_personal_message(websocket, initial_state)
        
        logger.debug(f"Sent initial state to user {user_id} for match {match_id}")
        
        # Keep connection alive and listen for heartbeat
        # (Actual match events are broadcast via ConnectionManager from services)
        while True:
            # Wait for client messages (e.g., ping/pong for heartbeat)
            data = await websocket.receive_text()
            
            # Handle client messages
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "close":
                logger.info(f"Client requested connection close: user={user_id}, match={match_id}")
                break
            else:
                logger.debug(f"Received message from client: {data}")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user={user_id}, match={match_id}")
    
    except Exception as e:
        logger.error(
            f"WebSocket error: user={user_id}, match={match_id}, error={str(e)}"
        )
        # Send error message to client
        try:
            await manager.send_personal_message(
                websocket,
                {
                    "type": WebSocketEventType.ERROR,
                    "data": {
                        "error_code": "INTERNAL_ERROR",
                        "message": "An error occurred. Connection will be closed."
                    }
                }
            )
        except:
            pass  # Connection might already be dead
    
    finally:
        # Remove from room
        await manager.disconnect(websocket, str(match_id))
        logger.info(
            f"WebSocket cleanup complete: user={user_id}, match={match_id}, "
            f"remaining={manager.get_room_size(str(match_id))}"
        )
