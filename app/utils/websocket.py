from typing import Dict, Set, Any
from fastapi import WebSocket
import json
import logging
import uuid

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Store connections by match_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, match_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        if match_id not in self.active_connections:
            self.active_connections[match_id] = set()
        
        self.active_connections[match_id].add(websocket)
        logger.info(f"WebSocket connected to match {match_id}")
    
    def disconnect(self, websocket: WebSocket, match_id: str):
        """Remove WebSocket connection"""
        if match_id in self.active_connections:
            self.active_connections[match_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[match_id]:
                del self.active_connections[match_id]
        
        logger.info(f"WebSocket disconnected from match {match_id}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast_to_match(self, match_id: str, data: Dict[str, Any]):
        """Broadcast message to all connections for a specific match"""
        if match_id not in self.active_connections:
            return
        
        message = json.dumps(data)
        connections_to_remove = []
        
        for connection in self.active_connections[match_id].copy():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                connections_to_remove.append(connection)
        
        # Remove dead connections
        for connection in connections_to_remove:
            self.disconnect(connection, match_id)
    
    async def send_ball_update(self, match_id: str, ball_data: Dict[str, Any], scorecard: Dict[str, Any]):
        """Send ball update to all match subscribers"""
        await self.broadcast_to_match(match_id, {
            "type": "ball_update",
            "match_id": match_id,
            "data": {
                "ball_details": ball_data,
                "updated_scorecard": scorecard,
                "timestamp": str(uuid.uuid4())  # Simple timestamp alternative
            }
        })
    
    async def send_wicket_update(self, match_id: str, wicket_data: Dict[str, Any]):
        """Send wicket update to all match subscribers"""
        await self.broadcast_to_match(match_id, {
            "type": "wicket",
            "match_id": match_id,
            "data": wicket_data
        })
    
    async def send_innings_complete(self, match_id: str, innings_data: Dict[str, Any]):
        """Send innings completion update"""
        await self.broadcast_to_match(match_id, {
            "type": "innings_complete", 
            "match_id": match_id,
            "data": innings_data
        })
    
    async def send_match_complete(self, match_id: str, result_data: Dict[str, Any]):
        """Send match completion update"""
        await self.broadcast_to_match(match_id, {
            "type": "match_complete",
            "match_id": match_id,
            "data": result_data
        })


# Global WebSocket manager instance
manager = WebSocketManager()
