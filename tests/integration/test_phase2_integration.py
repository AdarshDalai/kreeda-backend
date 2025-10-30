"""
Integration Tests for Phase 2: Teams & Match Management

Simplified integration tests focusing on:
1. Service interaction validation
2. State transition verification
3. Error propagation across services
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.services.cricket.team import TeamService
from src.services.cricket.match import MatchService
from src.schemas.cricket.team import TeamCreateRequest
from src.schemas.cricket.match import MatchCreateRequest, TossRequest, VenueSchema
from src.models.enums import SportType, MatchType, MatchCategory, MatchStatus, ElectedTo
from src.core.exceptions import NotFoundError, ValidationError


@pytest.fixture
def mock_db():
    """Mock database session"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_team_to_match_workflow(mock_db):
    """
    Integration: Create 2 teams → Create match
    
    Validates:
    - Teams can be created
    - Match can reference created teams
    
    Note: Toss testing moved to unit tests due to complexity of mocking
    """
    user_id = uuid4()
    team_a_id = uuid4()
    team_b_id = uuid4()
    match_id = uuid4()
    
    # ========================================================================
    # STEP 1: CREATE TEAM A
    # ========================================================================
    
    user_result = MagicMock()
    user_result.scalar_one_or_none = MagicMock(return_value=MagicMock(user_id=user_id))
    
    duplicate_result = MagicMock()
    duplicate_result.scalar_one_or_none = MagicMock(return_value=None)
    
    sport_profile = MagicMock()
    sport_profile.id = uuid4()
    sport_profile_result = MagicMock()
    sport_profile_result.scalar_one_or_none = MagicMock(return_value=sport_profile)
    
    user_profile = MagicMock()
    user_profile.full_name = "Test User A"
    user_profile.name = "Test User A"  # Fix: Pydantic needs actual string, not MagicMock
    user_profile_result = MagicMock()
    user_profile_result.scalar_one_or_none = MagicMock(return_value=user_profile)
    
    mock_db.execute = AsyncMock(side_effect=[
        user_result, duplicate_result, sport_profile_result, user_profile_result
    ])
    
    def refresh_team_a(obj):
        obj.id = team_a_id
        obj.short_name = "TA"
        obj.created_at = datetime.utcnow()
        obj.updated_at = datetime.utcnow()
    
    mock_db.refresh.side_effect = refresh_team_a
    
    team_a = await TeamService.create_team(
        user_id,
        TeamCreateRequest(name="Team A", sport_type=SportType.CRICKET),
        mock_db
    )
    
    assert team_a.id == team_a_id
    assert team_a.name == "Team A"
    
    # ========================================================================
    # STEP 2: CREATE TEAM B
    # ========================================================================
    
    # Re-mock for Team B creation (need fresh user_profile with correct name field)
    user_profile_b = MagicMock()
    user_profile_b.full_name = "Test User B"
    user_profile_b.name = "Test User B"  # Fix: Pydantic needs actual string
    user_profile_b_result = MagicMock()
    user_profile_b_result.scalar_one_or_none = MagicMock(return_value=user_profile_b)
    
    mock_db.execute = AsyncMock(side_effect=[
        user_result, duplicate_result, sport_profile_result, user_profile_b_result
    ])
    
    def refresh_team_b(obj):
        obj.id = team_b_id
        obj.short_name = "TB"
        obj.created_at = datetime.utcnow()
        obj.updated_at = datetime.utcnow()
    
    mock_db.refresh.side_effect = refresh_team_b
    
    team_b = await TeamService.create_team(
        user_id,
        TeamCreateRequest(name="Team B", sport_type=SportType.CRICKET),
        mock_db
    )
    
    assert team_b.id == team_b_id
    
    # ========================================================================
    # STEP 3: CREATE MATCH
    # ========================================================================
    
    user_match_result = MagicMock()
    user_match_result.scalar_one_or_none = MagicMock(return_value=MagicMock(user_id=user_id))
    
    team_a_mock = MagicMock()
    team_a_mock.id = team_a_id
    team_a_mock.sport_type = SportType.CRICKET
    team_a_mock.is_active = True
    team_a_result = MagicMock()
    team_a_result.scalar_one_or_none = MagicMock(return_value=team_a_mock)
    
    team_b_mock = MagicMock()
    team_b_mock.id = team_b_id
    team_b_mock.sport_type = SportType.CRICKET
    team_b_mock.is_active = True
    team_b_result = MagicMock()
    team_b_result.scalar_one_or_none = MagicMock(return_value=team_b_mock)
    
    match_code_result = MagicMock()
    match_code_result.scalar_one_or_none = MagicMock(return_value=None)
    
    mock_db.execute = AsyncMock(side_effect=[
        user_match_result, team_a_result, team_b_result, match_code_result
    ])
    
    def refresh_match(obj):
        obj.id = match_id
        obj.match_code = "KRD-TEST"
        obj.match_status = MatchStatus.SCHEDULED
        obj.is_featured = False  # Fix: Must be boolean, not None
        obj.created_at = datetime.utcnow()
        obj.updated_at = datetime.utcnow()
    
    mock_db.refresh.side_effect = refresh_match
    
    match = await MatchService.create_match(
        user_id,
        MatchCreateRequest(
            team_a_id=team_a_id,
            team_b_id=team_b_id,
            match_type=MatchType.T20,
            venue=VenueSchema(name="Test Stadium"),
            scheduled_start_time=datetime.utcnow() + timedelta(days=1)
        ),
        mock_db
    )
    
    # Verify integration success
    assert match.id == match_id
    assert match.team_a_id == team_a_id
    assert match.team_b_id == team_b_id
    assert match.match_status == MatchStatus.SCHEDULED
    assert team_a.id == team_a_id  # Team A still accessible
    assert team_b.id == team_b_id  # Team B still accessible


@pytest.mark.asyncio
async def test_match_requires_valid_teams(mock_db):
    """
    Integration: Match creation should fail if team doesn't exist
    
    Validates error propagation from MatchService to caller
    """
    user_id = uuid4()
    fake_team_id = uuid4()
    
    user_result = MagicMock()
    user_result.scalar_one_or_none = MagicMock(return_value=MagicMock(user_id=user_id))
    
    team_result = MagicMock()
    team_result.scalar_one_or_none = MagicMock(return_value=None)  # Team not found
    
    mock_db.execute = AsyncMock(side_effect=[user_result, team_result])
    
    with pytest.raises(NotFoundError) as exc:
        await MatchService.create_match(
            user_id,
            MatchCreateRequest(
                team_a_id=fake_team_id,
                team_b_id=uuid4(),
                match_type=MatchType.T20,
                venue=VenueSchema(name="Test"),
                scheduled_start_time=datetime.utcnow()
            ),
            mock_db
        )
    
    assert "Team A not found" in str(exc.value)


@pytest.mark.asyncio
async def test_toss_requires_scheduled_match(mock_db):
    """
    Integration: Toss should fail if match already started
    
    Validates state machine enforcement
    """
    user_id = uuid4()
    match_id = uuid4()
    team_id = uuid4()
    
    match_mock = MagicMock()
    match_mock.id = match_id
    match_mock.match_status = MatchStatus.LIVE  # Already started
    match_mock.created_by_user_id = user_id
    match_mock.team_a_id = team_id
    match_mock.team_b_id = uuid4()
    
    match_result = MagicMock()
    match_result.scalar_one_or_none = MagicMock(return_value=match_mock)
    mock_db.execute = AsyncMock(return_value=match_result)
    
    with pytest.raises(ValidationError) as exc:
        await MatchService.conduct_toss(
            match_id,
            user_id,
            TossRequest(toss_won_by_team_id=team_id, elected_to=ElectedTo.BAT),
            mock_db
        )
    
    assert "live" in str(exc.value).lower()
