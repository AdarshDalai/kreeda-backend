"""
Comprehensive tests for utility modules
"""
import json
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any

from fastapi import HTTPException, WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.commentary import CricketCommentaryGenerator, commentary_generator
from app.utils.database import get_db, get_engine, get_session_local, init_db
from app.utils.error_handler import (
    APIError, TeamNotFoundError, MatchNotFoundError, PermissionDeniedError,
    AlreadyExistsError, ValidationError, InternalServerError, handle_database_error
)
from app.utils.file_upload import FileUploadService, file_service
from app.utils.websocket import MatchWebSocketManager, websocket_manager
from app.models.cricket import CricketBall


class TestCricketCommentaryGenerator:
    """Test cricket commentary generation functionality"""

    @pytest.fixture
    def generator(self):
        """Create commentary generator instance"""
        return CricketCommentaryGenerator()

    @pytest.fixture
    def mock_ball(self):
        """Create mock cricket ball"""
        ball = Mock(spec=CricketBall)
        ball.runs_scored = 0
        ball.extras = 0
        ball.is_wicket = False
        ball.is_boundary = False
        ball.ball_type = "legal"
        ball.wicket_type = ""
        ball.over_number = 1
        return ball

    @pytest.fixture
    def match_context(self):
        """Sample match context data"""
        return {
            "current_score": 120,
            "current_wickets": 3,
            "required_run_rate": 8.5,
            "current_run_rate": 6.2,
            "overs_remaining": 5,
            "wickets_remaining": 7
        }

    def test_init_commentary_templates(self, generator):
        """Test commentary generator initialization"""
        assert hasattr(generator, 'commentary_templates')
        assert hasattr(generator, 'milestone_templates')
        assert hasattr(generator, 'pressure_comments')
        
        # Verify essential templates exist
        assert 'four' in generator.commentary_templates
        assert 'six' in generator.commentary_templates
        assert 'wicket_bowled' in generator.commentary_templates
        assert 'dot_ball' in generator.commentary_templates
        assert 'fifty' in generator.milestone_templates
        assert 'century' in generator.milestone_templates

    def test_dot_ball_commentary(self, generator, mock_ball, match_context):
        """Test commentary for dot ball"""
        mock_ball.runs_scored = 0
        mock_ball.is_wicket = False
        
        commentary = generator.generate_ball_commentary(mock_ball, match_context)
        
        assert isinstance(commentary, str)
        assert len(commentary) > 0
        # Should be one of the dot ball templates
        assert any(template in commentary for template in 
                  generator.commentary_templates['dot_ball'])

    def test_single_run_commentary(self, generator, mock_ball, match_context):
        """Test commentary for single run"""
        mock_ball.runs_scored = 1
        
        commentary = generator.generate_ball_commentary(mock_ball, match_context)
        
        assert isinstance(commentary, str)
        assert any(template in commentary for template in 
                  generator.commentary_templates['single'])

    def test_boundary_commentary(self, generator, mock_ball, match_context):
        """Test commentary for boundaries"""
        # Test four
        mock_ball.runs_scored = 4
        mock_ball.is_boundary = True
        
        commentary = generator.generate_ball_commentary(mock_ball, match_context)
        assert any(template in commentary for template in 
                  generator.commentary_templates['four'])
        
        # Test six
        mock_ball.runs_scored = 6
        mock_ball.is_boundary = True
        
        commentary = generator.generate_ball_commentary(mock_ball, match_context)
        assert any(template in commentary for template in 
                  generator.commentary_templates['six'])

    def test_wicket_commentary(self, generator, mock_ball, match_context):
        """Test commentary for wickets"""
        mock_ball.is_wicket = True
        mock_ball.wicket_type = "bowled"
        
        commentary = generator.generate_ball_commentary(mock_ball, match_context)
        
        assert isinstance(commentary, str)
        assert any(template in commentary for template in 
                  generator.commentary_templates['wicket_bowled'])

    def test_wide_ball_commentary(self, generator, mock_ball, match_context):
        """Test commentary for wide ball"""
        mock_ball.ball_type = "wide"
        
        commentary = generator.generate_ball_commentary(mock_ball, match_context)
        
        assert any(template in commentary for template in 
                  generator.commentary_templates['wide'])

    def test_no_ball_commentary(self, generator, mock_ball, match_context):
        """Test commentary for no ball"""
        mock_ball.ball_type = "no_ball"
        
        commentary = generator.generate_ball_commentary(mock_ball, match_context)
        
        assert any(template in commentary for template in 
                  generator.commentary_templates['no_ball'])

    def test_milestone_commentary_fifty(self, generator):
        """Test fifty milestone commentary"""
        commentary = generator.generate_milestone_commentary(50, "fifty")
        
        assert isinstance(commentary, str)
        assert any(template in commentary for template in 
                  generator.milestone_templates['fifty'])

    def test_milestone_commentary_century(self, generator):
        """Test century milestone commentary"""
        commentary = generator.generate_milestone_commentary(100, "century")
        
        assert isinstance(commentary, str)
        assert any(template in commentary for template in 
                  generator.milestone_templates['century'])

    def test_milestone_commentary_unknown(self, generator):
        """Test unknown milestone commentary"""
        commentary = generator.generate_milestone_commentary(75, "unknown")
        
        assert commentary == "Milestone reached! 75 runs!"

    def test_match_situation_commentary_death_overs(self, generator):
        """Test commentary for death overs"""
        context = {
            "overs_remaining": 2,
            "required_run_rate": 12.0,
            "current_run_rate": 8.0,
            "wickets_remaining": 5
        }
        
        commentary = generator.generate_match_situation_commentary(context)
        
        assert any(template in commentary for template in 
                  generator.pressure_comments['death_overs'])

    def test_match_situation_commentary_high_pressure(self, generator):
        """Test commentary for high pressure situation"""
        context = {
            "overs_remaining": 8,
            "required_run_rate": 12.0,
            "current_run_rate": 6.0,
            "wickets_remaining": 8
        }
        
        commentary = generator.generate_match_situation_commentary(context)
        
        assert any(template in commentary for template in 
                  generator.pressure_comments['high_pressure'])

    def test_match_situation_commentary_few_wickets(self, generator):
        """Test commentary for few wickets remaining"""
        context = {
            "overs_remaining": 10,
            "required_run_rate": 8.0,
            "current_run_rate": 7.0,
            "wickets_remaining": 2
        }
        
        commentary = generator.generate_match_situation_commentary(context)
        
        assert "lower order" in commentary or "wickets" in commentary

    def test_over_summary_maiden(self, generator):
        """Test over summary for maiden over"""
        mock_balls = [Mock(spec=CricketBall) for _ in range(6)]
        for ball in mock_balls:
            ball.over_number = 5
            ball.is_wicket = False
            ball.is_boundary = False
        
        summary = generator.generate_over_summary(mock_balls, 0)
        
        assert "maiden over" in summary.lower()
        assert "End of over 5: 0 runs" in summary

    def test_over_summary_expensive(self, generator):
        """Test over summary for expensive over"""
        mock_balls = [Mock(spec=CricketBall) for _ in range(6)]
        for ball in mock_balls:
            ball.over_number = 8
            ball.is_wicket = False
            ball.is_boundary = True
        
        summary = generator.generate_over_summary(mock_balls, 18)
        
        assert "expensive" in summary.lower()
        assert "End of over 8: 18 runs" in summary

    def test_over_summary_with_wickets(self, generator):
        """Test over summary with wickets"""
        mock_balls = [Mock(spec=CricketBall) for _ in range(6)]
        for i, ball in enumerate(mock_balls):
            ball.over_number = 3
            ball.is_wicket = i < 2  # First 2 balls are wickets
            ball.is_boundary = False
        
        summary = generator.generate_over_summary(mock_balls, 5)
        
        assert "2 wickets" in summary
        assert "End of over 3: 5 runs" in summary

    def test_global_commentary_generator_instance(self):
        """Test global commentary generator instance exists"""
        assert commentary_generator is not None
        assert isinstance(commentary_generator, CricketCommentaryGenerator)


class TestDatabaseUtils:
    """Test database utility functions"""

    @patch('app.utils.database.create_async_engine')
    def test_get_engine_creation(self, mock_create_engine):
        """Test engine creation"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Clear global engine first
        import app.utils.database as db_module
        db_module.engine = None
        
        engine = db_module.get_engine()
        
        assert engine == mock_engine
        mock_create_engine.assert_called_once()

    @patch('app.utils.database.async_sessionmaker')
    @patch('app.utils.database.get_engine')
    def test_get_session_local_creation(self, mock_get_engine, mock_sessionmaker):
        """Test session local creation"""
        mock_engine = Mock()
        mock_session_local = Mock()
        mock_get_engine.return_value = mock_engine
        mock_sessionmaker.return_value = mock_session_local
        
        # Clear global session first
        import app.utils.database as db_module
        db_module.AsyncSessionLocal = None
        
        session_local = db_module.get_session_local()
        
        assert session_local == mock_session_local
        mock_sessionmaker.assert_called_once_with(
            mock_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @pytest.mark.asyncio
    @patch('app.utils.database.get_session_local')
    async def test_get_db_session(self, mock_get_session_local):
        """Test database session dependency"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        
        mock_session_local = Mock()
        mock_session_local.return_value = mock_session_context
        mock_get_session_local.return_value = mock_session_local
        
        # Test that we get the expected session
        async for session in get_db():
            assert session == mock_session
            break
        
        # Verify that the session local was called
        mock_get_session_local.assert_called_once()
        mock_session_local.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.utils.database.get_engine')
    async def test_init_db_success(self, mock_get_engine):
        """Test successful database initialization"""
        mock_engine = Mock()
        mock_conn = AsyncMock()
        mock_begin_context = AsyncMock()
        mock_begin_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_begin_context.__aexit__ = AsyncMock(return_value=None)
        
        mock_engine.begin.return_value = mock_begin_context
        mock_get_engine.return_value = mock_engine
        
        await init_db()
        
        mock_engine.begin.assert_called_once()
        mock_conn.run_sync.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.utils.database.get_engine')
    async def test_init_db_failure(self, mock_get_engine):
        """Test database initialization failure"""
        mock_get_engine.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception, match="Database connection failed"):
            await init_db()


class TestErrorHandler:
    """Test error handling utilities"""

    def test_api_error_basic(self):
        """Test basic APIError creation"""
        error = APIError("TEST_ERROR", "Test message")
        
        assert error.code == "TEST_ERROR"
        assert error.status_code == 400
        assert isinstance(error.correlation_id, str)
        assert len(error.correlation_id) > 0

    def test_api_error_with_details(self):
        """Test APIError with details"""
        details = {"field": "email", "value": "invalid"}
        error = APIError("VALIDATION_ERROR", "Invalid email", 422, details)
        
        assert error.details == details
        assert error.status_code == 422

    def test_api_error_with_correlation_id(self):
        """Test APIError with custom correlation ID"""
        correlation_id = "test-123"
        error = APIError("TEST_ERROR", "Test", correlation_id=correlation_id)
        
        assert error.correlation_id == correlation_id

    def test_team_not_found_error(self):
        """Test TeamNotFoundError"""
        team_id = "team-123"
        error = TeamNotFoundError(team_id)
        
        assert error.code == "TEAM_NOT_FOUND"
        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert error.details["team_id"] == team_id

    def test_team_not_found_error_no_id(self):
        """Test TeamNotFoundError without ID"""
        error = TeamNotFoundError()
        
        assert error.code == "TEAM_NOT_FOUND"
        # When no team_id provided, details should be an empty dict, not None
        assert error.details == {}

    def test_match_not_found_error(self):
        """Test MatchNotFoundError"""
        match_id = "match-456"
        error = MatchNotFoundError(match_id)
        
        assert error.code == "MATCH_NOT_FOUND"
        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert error.details["match_id"] == match_id

    def test_permission_denied_error(self):
        """Test PermissionDeniedError"""
        action = "delete this match"
        error = PermissionDeniedError(action)
        
        assert error.code == "PERMISSION_DENIED"
        assert error.status_code == status.HTTP_403_FORBIDDEN

    def test_already_exists_error(self):
        """Test AlreadyExistsError"""
        resource = "Team"
        identifier = "team-789"
        error = AlreadyExistsError(resource, identifier)
        
        assert error.code == "ALREADY_EXISTS"
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.details["resource"] == resource
        assert error.details["identifier"] == identifier

    def test_validation_error(self):
        """Test ValidationError"""
        field = "email"
        message = "must be a valid email address"
        error = ValidationError(field, message)
        
        assert error.code == "VALIDATION_ERROR"
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.details["field"] == field

    def test_internal_server_error(self):
        """Test InternalServerError"""
        operation = "saving user data"
        error = InternalServerError(operation)
        
        assert error.code == "INTERNAL_ERROR"
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_handle_database_error(self):
        """Test database error handling"""
        original_error = Exception("Connection timeout")
        operation = "updating match score"
        
        api_error = handle_database_error(original_error, operation)
        
        assert isinstance(api_error, InternalServerError)
        assert api_error.code == "INTERNAL_ERROR"


class TestFileUploadService:
    """Test file upload service functionality"""

    @pytest.fixture
    def upload_service(self):
        """Create file upload service instance"""
        return FileUploadService()

    @pytest.fixture
    def mock_s3_client(self):
        """Create mock S3 client"""
        return Mock()

    @patch('app.utils.file_upload.settings')
    @patch('app.utils.file_upload.boto3.client')
    def test_init_with_valid_config(self, mock_boto_client, mock_settings):
        """Test service initialization with valid configuration"""
        mock_settings.r2_access_key_id = "access_key"
        mock_settings.r2_secret_access_key = "secret_key"
        mock_settings.r2_account_id = "account_id"
        mock_settings.r2_endpoint_url = "https://endpoint.com"
        
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        service = FileUploadService()
        
        assert service.s3_client == mock_client
        mock_boto_client.assert_called_once()

    @patch('app.utils.file_upload.settings')
    def test_init_with_missing_config(self, mock_settings):
        """Test service initialization with missing configuration"""
        mock_settings.r2_access_key_id = None
        
        service = FileUploadService()
        
        assert service.s3_client is None

    @pytest.mark.asyncio
    async def test_upload_file_no_client(self, upload_service):
        """Test file upload without S3 client"""
        upload_service.s3_client = None
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.upload_file(b"test content", "test.txt")
        
        assert exc_info.value.status_code == 500
        assert "not available" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch('app.utils.file_upload.settings')
    async def test_upload_file_success(self, mock_settings, upload_service, mock_s3_client):
        """Test successful file upload"""
        mock_settings.r2_bucket_name = "test-bucket"
        mock_settings.r2_endpoint_url = "https://endpoint.com"
        upload_service.s3_client = mock_s3_client
        
        file_content = b"test file content"
        filename = "test.txt"
        
        result = await upload_service.upload_file(file_content, filename)
        
        assert result.startswith("https://endpoint.com/test-bucket/uploads/")
        assert result.endswith(".txt")
        mock_s3_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.utils.file_upload.settings')
    async def test_upload_file_with_folder(self, mock_settings, upload_service, mock_s3_client):
        """Test file upload with custom folder"""
        mock_settings.r2_bucket_name = "test-bucket"
        mock_settings.r2_endpoint_url = "https://endpoint.com"
        upload_service.s3_client = mock_s3_client
        
        result = await upload_service.upload_file(
            b"content", "test.txt", folder="images"
        )
        
        assert "/images/" in result
        mock_s3_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_client_error(self, upload_service, mock_s3_client):
        """Test file upload with client error"""
        from botocore.exceptions import ClientError
        
        upload_service.s3_client = mock_s3_client
        mock_s3_client.put_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}}, "PutObject"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.upload_file(b"content", "test.txt")
        
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    @patch('app.utils.file_upload.settings')
    async def test_delete_file_success(self, mock_settings, upload_service, mock_s3_client):
        """Test successful file deletion"""
        mock_settings.r2_bucket_name = "test-bucket"
        upload_service.s3_client = mock_s3_client
        
        file_url = "https://endpoint.com/test-bucket/uploads/file.txt"
        result = await upload_service.delete_file(file_url)
        
        assert result is True
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="uploads/file.txt"
        )

    @pytest.mark.asyncio
    async def test_delete_file_no_client(self, upload_service):
        """Test file deletion without S3 client"""
        upload_service.s3_client = None
        
        result = await upload_service.delete_file("http://example.com/file.txt")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_file_invalid_url(self, upload_service, mock_s3_client):
        """Test file deletion with invalid URL"""
        upload_service.s3_client = mock_s3_client
        
        result = await upload_service.delete_file("invalid-url")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_file_exception(self, upload_service, mock_s3_client):
        """Test file deletion with exception"""
        upload_service.s3_client = mock_s3_client
        mock_s3_client.delete_object.side_effect = Exception("Delete failed")
        
        result = await upload_service.delete_file("https://example.com/bucket/file.txt")
        
        assert result is False

    def test_global_file_service_instance(self):
        """Test global file service instance exists"""
        assert file_service is not None
        assert isinstance(file_service, FileUploadService)


class TestMatchWebSocketManager:
    """Test WebSocket manager functionality"""

    @pytest.fixture
    def ws_manager(self):
        """Create WebSocket manager instance"""
        return MatchWebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket"""
        websocket = AsyncMock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_connect_to_match(self, ws_manager, mock_websocket):
        """Test connecting to match updates"""
        match_id = "match-123"
        user_id = "user-456"
        
        await ws_manager.connect_to_match(mock_websocket, match_id, user_id)
        
        assert match_id in ws_manager.match_connections
        assert mock_websocket in ws_manager.match_connections[match_id]
        assert user_id in ws_manager.user_connections
        assert ws_manager.user_connections[user_id] == mock_websocket
        mock_websocket.accept.assert_called_once()

    def test_disconnect_from_match(self, ws_manager, mock_websocket):
        """Test disconnecting from match updates"""
        match_id = "match-123"
        user_id = "user-456"
        
        # Setup connection first
        ws_manager.match_connections[match_id] = {mock_websocket}
        ws_manager.user_connections[user_id] = mock_websocket
        
        ws_manager.disconnect_from_match(mock_websocket, match_id, user_id)
        
        assert match_id not in ws_manager.match_connections
        assert user_id not in ws_manager.user_connections

    def test_disconnect_partial_cleanup(self, ws_manager, mock_websocket):
        """Test disconnecting with partial cleanup"""
        match_id = "match-123"
        user_id = "user-456"
        other_websocket = Mock()
        
        # Setup multiple connections
        ws_manager.match_connections[match_id] = {mock_websocket, other_websocket}
        ws_manager.user_connections[user_id] = mock_websocket
        
        ws_manager.disconnect_from_match(mock_websocket, match_id, user_id)
        
        # Match connections should still exist with other websocket
        assert match_id in ws_manager.match_connections
        assert mock_websocket not in ws_manager.match_connections[match_id]
        assert other_websocket in ws_manager.match_connections[match_id]
        assert user_id not in ws_manager.user_connections

    @pytest.mark.asyncio
    async def test_broadcast_ball_update(self, ws_manager, mock_websocket):
        """Test broadcasting ball update"""
        match_id = "match-123"
        ws_manager.match_connections[match_id] = {mock_websocket}
        
        ball_data = {"runs": 4, "is_boundary": True}
        scorecard = {"total_runs": 150, "wickets": 3}
        
        await ws_manager.broadcast_ball_update(match_id, ball_data, scorecard)
        
        mock_websocket.send_text.assert_called_once()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        
        assert sent_message["type"] == "ball_update"
        assert sent_message["match_id"] == match_id
        assert sent_message["ball"] == ball_data
        assert sent_message["scorecard"] == scorecard

    @pytest.mark.asyncio
    async def test_broadcast_ball_update_no_connections(self, ws_manager):
        """Test broadcasting ball update with no connections"""
        match_id = "nonexistent-match"
        
        # Should not raise any exceptions
        await ws_manager.broadcast_ball_update(match_id, {}, {})

    @pytest.mark.asyncio
    async def test_broadcast_ball_update_failed_connection(self, ws_manager):
        """Test broadcasting with failed WebSocket connection"""
        match_id = "match-123"
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.send_text.side_effect = Exception("Connection closed")
        
        ws_manager.match_connections[match_id] = {mock_websocket}
        
        await ws_manager.broadcast_ball_update(match_id, {}, {})
        
        # Failed connection should be removed
        assert len(ws_manager.match_connections[match_id]) == 0

    @pytest.mark.asyncio
    async def test_broadcast_wicket_alert(self, ws_manager, mock_websocket):
        """Test broadcasting wicket alert"""
        match_id = "match-123"
        ws_manager.match_connections[match_id] = {mock_websocket}
        
        wicket_data = {
            "wicket_type": "bowled",
            "dismissed_player_name": "John Doe"
        }
        
        await ws_manager.broadcast_wicket_alert(match_id, wicket_data)
        
        mock_websocket.send_text.assert_called_once()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        
        assert sent_message["type"] == "wicket_alert"
        assert sent_message["wicket"] == wicket_data
        assert "commentary" in sent_message

    @pytest.mark.asyncio
    async def test_broadcast_boundary_alert(self, ws_manager, mock_websocket):
        """Test broadcasting boundary alert"""
        match_id = "match-123"
        ws_manager.match_connections[match_id] = {mock_websocket}
        
        boundary_data = {"runs_scored": 6, "player_name": "Jane Smith"}
        
        await ws_manager.broadcast_boundary_alert(match_id, boundary_data)
        
        mock_websocket.send_text.assert_called_once()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        
        assert sent_message["type"] == "boundary_alert"
        assert sent_message["boundary"] == boundary_data
        assert "commentary" in sent_message

    @pytest.mark.asyncio
    async def test_broadcast_match_completed(self, ws_manager, mock_websocket):
        """Test broadcasting match completion"""
        match_id = "match-123"
        ws_manager.match_connections[match_id] = {mock_websocket}
        
        result_data = {
            "winner": "Team A",
            "margin": "5 wickets",
            "man_of_match": "Player X"
        }
        
        await ws_manager.broadcast_match_completed(match_id, result_data)
        
        mock_websocket.send_text.assert_called_once()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        
        assert sent_message["type"] == "match_completed"
        assert sent_message["result"] == result_data

    def test_generate_wicket_commentary_bowled(self, ws_manager):
        """Test wicket commentary generation for bowled"""
        wicket_data = {
            "wicket_type": "bowled",
            "dismissed_player_name": "John Doe"
        }
        
        commentary = ws_manager._generate_wicket_commentary(wicket_data)
        
        assert isinstance(commentary, str)
        # Commentary should contain either BOWLED or the player name (case insensitive)
        commentary_upper = commentary.upper()
        assert "BOWLED" in commentary_upper or "JOHN DOE" in commentary_upper or "TIMBER" in commentary_upper

    def test_generate_wicket_commentary_caught(self, ws_manager):
        """Test wicket commentary generation for caught"""
        wicket_data = {
            "wicket_type": "caught",
            "dismissed_player_name": "Jane Smith"
        }
        
        commentary = ws_manager._generate_wicket_commentary(wicket_data)
        
        assert isinstance(commentary, str)
        commentary_upper = commentary.upper()
        assert "CAUGHT" in commentary_upper or "JANE SMITH" in commentary_upper

    def test_generate_wicket_commentary_unknown_type(self, ws_manager):
        """Test wicket commentary for unknown wicket type"""
        wicket_data = {
            "wicket_type": "unknown",
            "dismissed_player_name": "Test Player"
        }
        
        commentary = ws_manager._generate_wicket_commentary(wicket_data)
        
        assert "WICKET! Test Player is out!" in commentary

    def test_generate_boundary_commentary_six(self, ws_manager):
        """Test boundary commentary for six"""
        boundary_data = {"runs_scored": 6}
        
        commentary = ws_manager._generate_boundary_commentary(boundary_data)
        
        assert isinstance(commentary, str)
        # Commentary should be related to sixes - check for key six-related words
        commentary_upper = commentary.upper()
        six_keywords = ["SIX", "MAXIMUM", "STANDS", "MASSIVE", "SMASHED", "SHOT"]
        assert any(keyword in commentary_upper for keyword in six_keywords)

    def test_generate_boundary_commentary_four(self, ws_manager):
        """Test boundary commentary for four"""
        boundary_data = {"runs_scored": 4}
        
        commentary = ws_manager._generate_boundary_commentary(boundary_data)
        
        assert isinstance(commentary, str)
        # Commentary should be related to boundaries - check for key boundary words
        commentary_upper = commentary.upper()
        boundary_keywords = ["FOUR", "BOUNDARY", "SHOT", "RUNS", "FENCE"]
        assert any(keyword in commentary_upper for keyword in boundary_keywords)

    def test_global_websocket_manager_instance(self):
        """Test global WebSocket manager instance exists"""
        assert websocket_manager is not None
        assert isinstance(websocket_manager, MatchWebSocketManager)


@pytest.mark.integration
class TestUtilsIntegration:
    """Integration tests for utility modules working together"""

    @pytest.mark.asyncio
    async def test_error_handling_in_file_upload(self):
        """Test error handling integration with file upload"""
        service = FileUploadService()
        service.s3_client = None
        
        try:
            await service.upload_file(b"test", "test.txt")
        except HTTPException as e:
            assert e.status_code == 500
            assert "not available" in str(e.detail)

    @pytest.mark.asyncio
    async def test_websocket_commentary_integration(self):
        """Test WebSocket integration with commentary generator"""
        ws_manager = MatchWebSocketManager()
        mock_websocket = AsyncMock(spec=WebSocket)
        
        # Connect to match
        match_id = "match-integration"
        await ws_manager.connect_to_match(mock_websocket, match_id, "user-123")
        
        # Broadcast with commentary
        wicket_data = {
            "wicket_type": "bowled",
            "dismissed_player_name": "Integration Test"
        }
        
        await ws_manager.broadcast_wicket_alert(match_id, wicket_data)
        
        # Verify message was sent with commentary
        mock_websocket.send_text.assert_called_once()
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert "commentary" in sent_data
        assert isinstance(sent_data["commentary"], str)

    def test_commentary_with_mock_ball_integration(self):
        """Test commentary generation with mock cricket ball"""
        generator = CricketCommentaryGenerator()
        
        # Create a realistic ball scenario
        ball = Mock(spec=CricketBall)
        ball.runs_scored = 6
        ball.is_boundary = True
        ball.is_wicket = False
        ball.ball_type = "legal"
        ball.wicket_type = ""
        
        match_context = {
            "current_score": 180,
            "current_wickets": 4,
            "overs_remaining": 2
        }
        
        commentary = generator.generate_ball_commentary(ball, match_context)
        
        # Should generate six commentary
        assert isinstance(commentary, str)
        assert len(commentary) > 0
        
        # Test milestone commentary
        milestone_commentary = generator.generate_milestone_commentary(100, "century")
        assert "CENTURY" in milestone_commentary or "hundred" in milestone_commentary.lower()