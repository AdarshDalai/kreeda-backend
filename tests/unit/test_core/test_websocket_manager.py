"""
Unit Tests for WebSocket ConnectionManager

Tests:
- Connection/disconnection lifecycle
- Room-based broadcasting
- Multiple clients in same room
- Dead connection cleanup
- Error handling
- Thread safety
- Room management

Author: AI Coding Agent (Professional Standards)
Date: November 1, 2025
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket

from src.core.websocket_manager import ConnectionManager


@pytest.fixture
def connection_manager():
    """Create fresh ConnectionManager for each test"""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket"""
    ws = AsyncMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


@pytest.fixture
def mock_websockets():
    """Create multiple mock WebSockets"""
    return [AsyncMock(spec=WebSocket) for _ in range(3)]


class TestConnectionLifecycle:
    """Test connection and disconnection operations"""
    
    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, connection_manager, mock_websocket):
        """Test that connect accepts WebSocket connection"""
        match_id = "match-123"
        
        await connection_manager.connect(mock_websocket, match_id)
        
        # Verify websocket was accepted
        mock_websocket.accept.assert_called_once()
        
        # Verify connection added to room
        assert match_id in connection_manager.active_connections
        assert mock_websocket in connection_manager.active_connections[match_id]
    
    @pytest.mark.asyncio
    async def test_connect_creates_room_if_not_exists(self, connection_manager, mock_websocket):
        """Test that connect creates room implicitly"""
        match_id = "new-match"
        
        # Room doesn't exist initially
        assert match_id not in connection_manager.active_connections
        
        await connection_manager.connect(mock_websocket, match_id)
        
        # Room created
        assert match_id in connection_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, connection_manager, mock_websockets):
        """Test that disconnect removes connection from room"""
        match_id = "match-123"
        
        # Connect two clients
        await connection_manager.connect(mock_websockets[0], match_id)
        await connection_manager.connect(mock_websockets[1], match_id)
        assert mock_websockets[0] in connection_manager.active_connections[match_id]
        
        # Disconnect first client
        await connection_manager.disconnect(mock_websockets[0], match_id)
        
        # First connection removed, second still there
        assert mock_websockets[0] not in connection_manager.active_connections[match_id]
        assert mock_websockets[1] in connection_manager.active_connections[match_id]
    
    @pytest.mark.asyncio
    async def test_disconnect_removes_empty_room(self, connection_manager, mock_websocket):
        """Test that disconnect removes room when empty"""
        match_id = "match-123"
        
        await connection_manager.connect(mock_websocket, match_id)
        await connection_manager.disconnect(mock_websocket, match_id)
        
        # Room removed completely
        assert match_id not in connection_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_disconnect_safe_for_nonexistent_connection(
        self, 
        connection_manager, 
        mock_websocket
    ):
        """Test that disconnect handles nonexistent connection gracefully"""
        match_id = "match-123"
        
        # Disconnect without connecting (should not raise error)
        await connection_manager.disconnect(mock_websocket, match_id)
        
        # No error raised
        assert True


class TestRoomManagement:
    """Test room-based connection management"""
    
    @pytest.mark.asyncio
    async def test_multiple_clients_same_room(
        self, 
        connection_manager, 
        mock_websockets
    ):
        """Test multiple clients can join same match room"""
        match_id = "match-123"
        
        # Connect 3 clients
        for ws in mock_websockets:
            await connection_manager.connect(ws, match_id)
        
        # All in same room
        assert len(connection_manager.active_connections[match_id]) == 3
        for ws in mock_websockets:
            assert ws in connection_manager.active_connections[match_id]
    
    @pytest.mark.asyncio
    async def test_clients_in_different_rooms(
        self, 
        connection_manager, 
        mock_websockets
    ):
        """Test clients in different match rooms are isolated"""
        match_ids = ["match-1", "match-2", "match-3"]
        
        # Connect each client to different match
        for ws, match_id in zip(mock_websockets, match_ids):
            await connection_manager.connect(ws, match_id)
        
        # Each room has 1 client
        for match_id in match_ids:
            assert len(connection_manager.active_connections[match_id]) == 1
    
    @pytest.mark.asyncio
    async def test_get_room_size(self, connection_manager, mock_websockets):
        """Test get_room_size returns correct count"""
        match_id = "match-123"
        
        # Empty room
        assert connection_manager.get_room_size(match_id) == 0
        
        # Add clients
        for ws in mock_websockets:
            await connection_manager.connect(ws, match_id)
        
        # Correct size
        assert connection_manager.get_room_size(match_id) == 3
    
    @pytest.mark.asyncio
    async def test_get_total_connections(self, connection_manager, mock_websockets):
        """Test get_total_connections across all rooms"""
        await connection_manager.connect(mock_websockets[0], "match-1")
        await connection_manager.connect(mock_websockets[1], "match-1")
        await connection_manager.connect(mock_websockets[2], "match-2")
        
        assert connection_manager.get_total_connections() == 3
    
    @pytest.mark.asyncio
    async def test_get_active_matches(self, connection_manager, mock_websockets):
        """Test get_active_matches returns all room IDs"""
        match_ids = ["match-1", "match-2", "match-3"]
        
        for ws, match_id in zip(mock_websockets, match_ids):
            await connection_manager.connect(ws, match_id)
        
        active_matches = connection_manager.get_active_matches()
        assert set(active_matches) == set(match_ids)


class TestBroadcasting:
    """Test message broadcasting to rooms"""
    
    @pytest.mark.asyncio
    async def test_broadcast_to_match_sends_to_all_clients(
        self, 
        connection_manager, 
        mock_websockets
    ):
        """Test broadcast sends message to all clients in room"""
        match_id = "match-123"
        
        # Connect all clients
        for ws in mock_websockets:
            await connection_manager.connect(ws, match_id)
        
        # Broadcast message
        message = {"type": "BALL_BOWLED", "data": {"runs": 4}}
        await connection_manager.broadcast_to_match(match_id, message)
        
        # All clients received message
        for ws in mock_websockets:
            ws.send_text.assert_called_once()
            sent_data = ws.send_text.call_args[0][0]
            parsed = json.loads(sent_data)
            assert parsed["type"] == "BALL_BOWLED"
            assert parsed["data"]["runs"] == 4
            assert "timestamp" in parsed  # Auto-added
    
    @pytest.mark.asyncio
    async def test_broadcast_adds_timestamp(self, connection_manager, mock_websocket):
        """Test broadcast adds timestamp if not present"""
        match_id = "match-123"
        await connection_manager.connect(mock_websocket, match_id)
        
        message = {"type": "TEST"}
        await connection_manager.broadcast_to_match(match_id, message)
        
        sent_data = mock_websocket.send_text.call_args[0][0]
        parsed = json.loads(sent_data)
        assert "timestamp" in parsed
        assert parsed["timestamp"].endswith("Z")
    
    @pytest.mark.asyncio
    async def test_broadcast_preserves_existing_timestamp(
        self, 
        connection_manager, 
        mock_websocket
    ):
        """Test broadcast keeps provided timestamp"""
        match_id = "match-123"
        await connection_manager.connect(mock_websocket, match_id)
        
        custom_time = "2025-11-01T12:00:00Z"
        message = {"type": "TEST", "timestamp": custom_time}
        await connection_manager.broadcast_to_match(match_id, message)
        
        sent_data = mock_websocket.send_text.call_args[0][0]
        parsed = json.loads(sent_data)
        assert parsed["timestamp"] == custom_time
    
    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_room_no_error(
        self, 
        connection_manager
    ):
        """Test broadcast to nonexistent room doesn't raise error"""
        message = {"type": "TEST"}
        
        # Should not raise error
        await connection_manager.broadcast_to_match("nonexistent", message)
        assert True
    
    @pytest.mark.asyncio
    async def test_broadcast_handles_dead_connection(
        self, 
        connection_manager, 
        mock_websockets
    ):
        """Test broadcast continues when one connection fails"""
        match_id = "match-123"
        
        # Connect 3 clients, make middle one fail
        for ws in mock_websockets:
            await connection_manager.connect(ws, match_id)
        
        # Middle client will fail to send
        mock_websockets[1].send_text.side_effect = Exception("Connection lost")
        
        message = {"type": "TEST"}
        await connection_manager.broadcast_to_match(match_id, message)
        
        # First and third clients still received message
        assert mock_websockets[0].send_text.called
        assert mock_websockets[2].send_text.called
        
        # Dead connection removed from room
        assert mock_websockets[1] not in connection_manager.active_connections[match_id]
    
    @pytest.mark.asyncio
    async def test_broadcast_serialization_error(
        self, 
        connection_manager, 
        mock_websocket
    ):
        """Test broadcast handles JSON serialization errors"""
        match_id = "match-123"
        await connection_manager.connect(mock_websocket, match_id)
        
        # Invalid JSON (circular reference, etc.)
        class UnserializableClass:
            pass
        
        message = {"type": "TEST", "data": UnserializableClass()}
        
        # Should not raise error
        await connection_manager.broadcast_to_match(match_id, message)
        
        # Message not sent
        mock_websocket.send_text.assert_not_called()


class TestPersonalMessaging:
    """Test personal message sending"""
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self, connection_manager, mock_websocket):
        """Test sending message to specific client"""
        message = {"type": "CONNECTION_ESTABLISHED"}
        
        await connection_manager.send_personal_message(mock_websocket, message)
        
        mock_websocket.send_text.assert_called_once()
        sent_data = mock_websocket.send_text.call_args[0][0]
        parsed = json.loads(sent_data)
        assert parsed["type"] == "CONNECTION_ESTABLISHED"
        assert "timestamp" in parsed
    
    @pytest.mark.asyncio
    async def test_send_personal_message_failure_raises(
        self, 
        connection_manager, 
        mock_websocket
    ):
        """Test personal message failure raises exception"""
        mock_websocket.send_text.side_effect = Exception("Connection lost")
        
        message = {"type": "TEST"}
        
        with pytest.raises(Exception):
            await connection_manager.send_personal_message(mock_websocket, message)


class TestThreadSafety:
    """Test concurrent operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_connects(self, connection_manager, mock_websockets):
        """Test concurrent connections are handled safely"""
        match_id = "match-123"
        
        # Connect all clients concurrently
        tasks = [
            connection_manager.connect(ws, match_id)
            for ws in mock_websockets
        ]
        await asyncio.gather(*tasks)
        
        # All connections added
        assert len(connection_manager.active_connections[match_id]) == 3
    
    @pytest.mark.asyncio
    async def test_concurrent_disconnects(self, connection_manager, mock_websockets):
        """Test concurrent disconnections are handled safely"""
        match_id = "match-123"
        
        # Connect all
        for ws in mock_websockets:
            await connection_manager.connect(ws, match_id)
        
        # Disconnect all concurrently
        tasks = [
            connection_manager.disconnect(ws, match_id)
            for ws in mock_websockets
        ]
        await asyncio.gather(*tasks)
        
        # Room removed
        assert match_id not in connection_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_concurrent_connect_disconnect(
        self, 
        connection_manager, 
        mock_websockets
    ):
        """Test concurrent connect/disconnect operations"""
        match_id = "match-123"
        
        # Mix of operations
        tasks = [
            connection_manager.connect(mock_websockets[0], match_id),
            connection_manager.connect(mock_websockets[1], match_id),
            connection_manager.disconnect(mock_websockets[0], match_id),
            connection_manager.connect(mock_websockets[2], match_id),
        ]
        await asyncio.gather(*tasks)
        
        # Only websockets[1] and websockets[2] should be in room
        # (websockets[0] was connected then disconnected)
        connections = connection_manager.active_connections[match_id]
        assert len(connections) == 2
        assert mock_websockets[1] in connections
        assert mock_websockets[2] in connections
