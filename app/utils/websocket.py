import json
import logging
import random
import uuid
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class MatchWebSocketManager:
    """WebSocket manager for real-time match updates"""

    def __init__(self):
        # Active connections per match
        self.match_connections: Dict[str, Set[WebSocket]] = {}
        # User connections for notifications
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect_to_match(
        self, websocket: WebSocket, match_id: str, user_id: Optional[str] = None
    ):
        """Connect user to match updates"""
        await websocket.accept()

        if match_id not in self.match_connections:
            self.match_connections[match_id] = set()

        self.match_connections[match_id].add(websocket)

        if user_id:
            self.user_connections[user_id] = websocket

        logger.info(f"User {user_id} connected to match {match_id}")

    def disconnect_from_match(
        self, websocket: WebSocket, match_id: str, user_id: Optional[str] = None
    ):
        """Disconnect user from match updates"""
        if match_id in self.match_connections:
            self.match_connections[match_id].discard(websocket)
            if not self.match_connections[match_id]:
                del self.match_connections[match_id]

        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]

        logger.info(f"User {user_id} disconnected from match {match_id}")

    async def broadcast_ball_update(
        self, match_id: str, ball_data: dict, scorecard: dict
    ):
        """Broadcast ball update to all match watchers"""
        if match_id not in self.match_connections:
            return

        message = {
            "type": "ball_update",
            "match_id": match_id,
            "ball": ball_data,
            "scorecard": scorecard,
            "timestamp": str(uuid.uuid4()),  # Simple timestamp alternative
        }

        connections_to_remove = []
        for websocket in self.match_connections[match_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to websocket: {e}")
                connections_to_remove.append(websocket)

        # Remove failed connections
        for websocket in connections_to_remove:
            self.match_connections[match_id].discard(websocket)

    async def broadcast_wicket_alert(self, match_id: str, wicket_data: dict):
        """Special broadcast for wicket events"""
        if match_id not in self.match_connections:
            return

        message = {
            "type": "wicket_alert",
            "match_id": match_id,
            "wicket": wicket_data,
            "commentary": self._generate_wicket_commentary(wicket_data),
        }

        await self._broadcast_to_match(match_id, message)

    async def broadcast_boundary_alert(self, match_id: str, boundary_data: dict):
        """Special broadcast for boundary events"""
        if match_id not in self.match_connections:
            return

        message = {
            "type": "boundary_alert",
            "match_id": match_id,
            "boundary": boundary_data,
            "commentary": self._generate_boundary_commentary(boundary_data),
        }

        await self._broadcast_to_match(match_id, message)

    async def broadcast_match_completed(self, match_id: str, result_data: dict):
        """Broadcast match completion"""
        message = {
            "type": "match_completed",
            "match_id": match_id,
            "result": result_data,
        }

        await self._broadcast_to_match(match_id, message)

    async def _broadcast_to_match(self, match_id: str, message: dict):
        """Internal method to broadcast message to all match watchers"""
        if match_id not in self.match_connections:
            return

        connections_to_remove = []
        for websocket in self.match_connections[match_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                connections_to_remove.append(websocket)

        # Remove failed connections
        for websocket in connections_to_remove:
            self.match_connections[match_id].discard(websocket)

    def _generate_wicket_commentary(self, wicket_data: dict) -> str:
        """Generate commentary for wicket events"""
        wicket_type = wicket_data.get("wicket_type", "").replace("_", " ").title()
        player_name = wicket_data.get("dismissed_player_name", "Batsman")

        comments = {
            "Bowled": [
                f"BOWLED! {player_name} has been cleaned up!",
                f"Timber! {wicket_type} dismissal!",
            ],
            "Caught": [
                f"CAUGHT! Excellent fielding!",
                f"What a catch! {player_name} has to go!",
            ],
            "Lbw": [
                f"LBW! That looked plumb!",
                f"Up goes the finger! {player_name} is out LBW!",
            ],
            "Run Out": [
                f"RUN OUT! Mix-up in the middle!",
                f"Direct hit! {player_name} is well short!",
            ],
            "Stumped": [
                f"STUMPED! Lightning quick work from the keeper!",
                f"Brilliant stumping! {player_name} is out!",
            ],
        }

        return random.choice(
            comments.get(wicket_type, [f"WICKET! {player_name} is out!"])
        )

    def _generate_boundary_commentary(self, boundary_data: dict) -> str:
        """Generate commentary for boundary events"""
        runs = boundary_data.get("runs_scored", 4)

        if runs == 6:
            comments = [
                "SIX! What a massive hit!",
                "Maximum! That's gone out of the park!",
                "SIX! Absolutely smashed!",
                "Into the stands! Fantastic shot!",
            ]
        else:
            comments = [
                "FOUR! Beautiful stroke!",
                "Boundary! Perfect timing!",
                "FOUR! Races away to the fence!",
                "What a shot! Four runs!",
            ]

        return random.choice(comments)


# Global WebSocket manager instance
websocket_manager = MatchWebSocketManager()
