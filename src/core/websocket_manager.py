"""
WebSocket Connection Manager for Live Match Broadcasting

Manages WebSocket connections with room-based broadcasting for real-time
cricket match updates. Each match has its own room, and events are broadcast
to all spectators in that room.

Author: AI Coding Agent (Professional Standards)
Date: November 1, 2025
"""

import asyncio
import logging
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections with room-based broadcasting.
    
    Features:
    - Room-based connections (one room per match_id)
    - Thread-safe operations using asyncio locks
    - Auto-cleanup on disconnect
    - Broadcast to all clients in a room
    - Individual client messaging
    - Graceful error handling
    
    Usage:
        manager = ConnectionManager()
        await manager.connect(websocket, match_id)
        await manager.broadcast_to_match(match_id, event_data)
        await manager.disconnect(websocket, match_id)
    """
    
    def __init__(self):
        """Initialize connection manager with empty room dictionary."""
        # Dictionary mapping match_id to set of WebSocket connections
        # {match_id: {websocket1, websocket2, ...}}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        logger.info("ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket, match_id: str) -> None:
        """
        Add a WebSocket connection to a match room.
        
        Args:
            websocket: The WebSocket connection to add
            match_id: The match ID (room identifier)
            
        Note:
            - Creates room implicitly if it doesn't exist
            - Thread-safe operation
        """
        await websocket.accept()
        
        async with self._lock:
            if match_id not in self.active_connections:
                self.active_connections[match_id] = set()
            
            self.active_connections[match_id].add(websocket)
        
        room_size = len(self.active_connections[match_id])
        logger.info(
            f"Client connected to match {match_id}. "
            f"Room size: {room_size}"
        )
    
    async def disconnect(self, websocket: WebSocket, match_id: str) -> None:
        """
        Remove a WebSocket connection from a match room.
        
        Args:
            websocket: The WebSocket connection to remove
            match_id: The match ID (room identifier)
            
        Note:
            - Removes empty rooms automatically
            - Thread-safe operation
            - Safe to call even if connection not in room
        """
        async with self._lock:
            if match_id in self.active_connections:
                self.active_connections[match_id].discard(websocket)
                
                # Clean up empty rooms
                if not self.active_connections[match_id]:
                    del self.active_connections[match_id]
                    logger.info(f"Match room {match_id} closed (no spectators)")
                else:
                    room_size = len(self.active_connections[match_id])
                    logger.info(
                        f"Client disconnected from match {match_id}. "
                        f"Remaining: {room_size}"
                    )
    
    async def broadcast_to_match(self, match_id: str, message: dict) -> None:
        """
        Broadcast a message to all spectators watching a match.
        
        Args:
            match_id: The match ID (room identifier)
            message: The message dictionary to send (will be JSON serialized)
            
        Note:
            - Skips dead connections gracefully
            - Continues broadcasting even if some clients fail
            - Logs errors but doesn't raise exceptions
        """
        if match_id not in self.active_connections:
            logger.debug(f"No spectators for match {match_id}, skipping broadcast")
            return
        
        # Get snapshot of connections to avoid modification during iteration
        connections = list(self.active_connections[match_id])
        
        # Add server timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Serialize message once
        try:
            message_json = json.dumps(message)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize message: {e}")
            return
        
        # Broadcast to all connections
        dead_connections = []
        successful_sends = 0
        
        for connection in connections:
            try:
                await connection.send_text(message_json)
                successful_sends += 1
            except Exception as e:
                logger.warning(
                    f"Failed to send to client in match {match_id}: {e}"
                )
                dead_connections.append(connection)
        
        # Clean up dead connections
        if dead_connections:
            async with self._lock:
                if match_id in self.active_connections:
                    for connection in dead_connections:
                        self.active_connections[match_id].discard(connection)
                    
                    # Remove empty room
                    if not self.active_connections[match_id]:
                        del self.active_connections[match_id]
        
        logger.debug(
            f"Broadcast to match {match_id}: {message.get('type', 'UNKNOWN')} "
            f"- {successful_sends} clients, {len(dead_connections)} failed"
        )
    
    async def send_personal_message(
        self, 
        websocket: WebSocket, 
        message: dict
    ) -> None:
        """
        Send a message to a specific client.
        
        Args:
            websocket: The WebSocket connection to send to
            message: The message dictionary to send (will be JSON serialized)
            
        Raises:
            Exception: If message cannot be sent (connection lost, etc.)
        """
        # Add server timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        try:
            message_json = json.dumps(message)
            await websocket.send_text(message_json)
            logger.debug(f"Sent personal message: {message.get('type', 'UNKNOWN')}")
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize personal message: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            raise
    
    def get_room_size(self, match_id: str) -> int:
        """
        Get the number of spectators watching a match.
        
        Args:
            match_id: The match ID (room identifier)
            
        Returns:
            Number of active connections in the room (0 if room doesn't exist)
        """
        return len(self.active_connections.get(match_id, set()))
    
    def get_total_connections(self) -> int:
        """
        Get the total number of active connections across all matches.
        
        Returns:
            Total number of active WebSocket connections
        """
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_active_matches(self) -> list:
        """
        Get list of match IDs with active spectators.
        
        Returns:
            List of match IDs (strings)
        """
        return list(self.active_connections.keys())


# Global instance (singleton pattern)
connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """
    Dependency injection function for FastAPI.
    
    Returns:
        The global ConnectionManager instance
        
    Usage:
        @router.post("/endpoint")
        async def endpoint(
            manager: ConnectionManager = Depends(get_connection_manager)
        ):
            await manager.broadcast_to_match(...)
    """
    return connection_manager
