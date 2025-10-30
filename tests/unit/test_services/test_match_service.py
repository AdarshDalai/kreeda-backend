"""
Unit Tests for Match Service
Tests MatchService core methods with mocked database calls

Focus: Match creation, toss, retrieval, and listing
Pattern: AAA (Arrange-Act-Assert) with AsyncMock
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.services.cricket.match import MatchService
from src.schemas.cricket.match import MatchCreateRequest, TossRequest, VenueSchema
from src.models.enums import (
    SportType, MatchType, MatchCategory, MatchStatus, ElectedTo, MatchVisibility
)
from src.core.exceptions import NotFoundError, ValidationError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock AsyncSession"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.fixture
def sample_team_a_id():
    return uuid4()


@pytest.fixture
def sample_team_b_id():
    return uuid4()


@pytest.fixture
def sample_match_id():
    return uuid4()


@pytest.fixture
def mock_user(sample_user_id):
    user = MagicMock()
    user.user_id = sample_user_id
    return user


@pytest.fixture
def mock_team_a(sample_team_a_id):
    team = MagicMock()
    team.id = sample_team_a_id
    team.sport_type = SportType.CRICKET
    team.is_active = True
    return team


@pytest.fixture
def mock_team_b(sample_team_b_id):
    team = MagicMock()
    team.id = sample_team_b_id
    team.sport_type = SportType.CRICKET
    team.is_active = True
    return team


@pytest.fixture
def mock_match(sample_match_id, sample_user_id, sample_team_a_id, sample_team_b_id):
    match = MagicMock()
    match.id = sample_match_id
    match.match_code = "KRD-1234"
    match.sport_type = SportType.CRICKET
    match.match_type = MatchType.T20
    match.match_category = MatchCategory.PRACTICE
    match.team_a_id = sample_team_a_id
    match.team_b_id = sample_team_b_id
    match.match_status = MatchStatus.SCHEDULED
    match.toss_won_by_team_id = None
    match.elected_to = None
    match.toss_completed_at = None
    match.match_rules = {"players_per_team": 11, "overs_per_side": 20}
    match.venue = {"name": "Test Ground"}
    match.scheduled_start_time = datetime.utcnow()
    match.actual_start_time = None
    match.estimated_end_time = None
    match.actual_end_time = None
    match.visibility = MatchVisibility.PUBLIC
    match.is_featured = False
    match.winning_team_id = None
    match.result_type = None
    match.result_margin = None
    match.player_of_match_user_id = None
    match.created_by_user_id = sample_user_id  # Match creator
    match.created_at = datetime.utcnow()
    match.updated_at = datetime.utcnow()
    match.team_a_name = None
    match.team_b_name = None
    return match


# ============================================================================
# CREATE MATCH TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_match_user_not_found(mock_db_session, sample_user_id, sample_team_a_id, sample_team_b_id):
    """Test match creation fails when user doesn't exist"""
    request = MatchCreateRequest(
        team_a_id=sample_team_a_id,
        team_b_id=sample_team_b_id,
        match_type=MatchType.T20,
        venue=VenueSchema(name="Test Ground"),
        scheduled_start_time=datetime.utcnow()
    )
    
    user_result = MagicMock()
    user_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=user_result)
    
    with pytest.raises(NotFoundError) as exc_info:
        await MatchService.create_match(sample_user_id, request, mock_db_session)
    
    assert "User not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_match_team_not_found(
    mock_db_session, sample_user_id, sample_team_a_id, sample_team_b_id, mock_user
):
    """Test match creation fails when team doesn't exist"""
    request = MatchCreateRequest(
        team_a_id=sample_team_a_id,
        team_b_id=sample_team_b_id,
        match_type=MatchType.T20,
        venue=VenueSchema(name="Test Ground"),
        scheduled_start_time=datetime.utcnow()
    )
    
    user_result = MagicMock()
    user_result.scalar_one_or_none = MagicMock(return_value=mock_user)
    
    team_a_result = MagicMock()
    team_a_result.scalar_one_or_none = MagicMock(return_value=None)
    
    mock_db_session.execute = AsyncMock(side_effect=[user_result, team_a_result])
    
    with pytest.raises(NotFoundError) as exc_info:
        await MatchService.create_match(sample_user_id, request, mock_db_session)
    
    assert "Team A not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_match_team_not_active(
    mock_db_session, sample_user_id, sample_team_a_id, sample_team_b_id,
    mock_user, mock_team_a
):
    """Test match creation fails when team is inactive"""
    request = MatchCreateRequest(
        team_a_id=sample_team_a_id,
        team_b_id=sample_team_b_id,
        match_type=MatchType.T20,
        venue=VenueSchema(name="Test Ground"),
        scheduled_start_time=datetime.utcnow()
    )
    
    mock_team_a.is_active = False
    
    user_result = MagicMock()
    user_result.scalar_one_or_none = MagicMock(return_value=mock_user)
    
    team_a_result = MagicMock()
    team_a_result.scalar_one_or_none = MagicMock(return_value=mock_team_a)
    
    mock_db_session.execute = AsyncMock(side_effect=[user_result, team_a_result])
    
    with pytest.raises(ValidationError) as exc_info:
        await MatchService.create_match(sample_user_id, request, mock_db_session)
    
    assert "not active" in str(exc_info.value).lower()


# ============================================================================
# TOSS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_conduct_toss_match_not_found(
    mock_db_session, sample_user_id, sample_match_id, sample_team_a_id
):
    """Test toss fails when match doesn't exist"""
    request = TossRequest(
        toss_won_by_team_id=sample_team_a_id,
        elected_to=ElectedTo.BAT
    )
    
    match_result = MagicMock()
    match_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=match_result)
    
    with pytest.raises(NotFoundError):
        await MatchService.conduct_toss(sample_match_id, sample_user_id, request, mock_db_session)


@pytest.mark.asyncio
async def test_conduct_toss_invalid_status(
    mock_db_session, sample_user_id, sample_match_id, sample_team_a_id, mock_match
):
    """Test toss fails when match not in SCHEDULED status"""
    request = TossRequest(
        toss_won_by_team_id=sample_team_a_id,
        elected_to=ElectedTo.BAT
    )
    
    mock_match.match_status = MatchStatus.LIVE
    
    match_result = MagicMock()
    match_result.scalar_one_or_none = MagicMock(return_value=mock_match)
    mock_db_session.execute = AsyncMock(return_value=match_result)
    
    with pytest.raises(ValidationError) as exc_info:
        await MatchService.conduct_toss(sample_match_id, sample_user_id, request, mock_db_session)
    
    assert "live" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_conduct_toss_invalid_team(
    mock_db_session, sample_user_id, sample_match_id, mock_match
):
    """Test toss fails when winner team not in match"""
    invalid_team_id = uuid4()
    request = TossRequest(
        toss_won_by_team_id=invalid_team_id,
        elected_to=ElectedTo.BAT
    )
    
    match_result = MagicMock()
    match_result.scalar_one_or_none = MagicMock(return_value=mock_match)
    mock_db_session.execute = AsyncMock(return_value=match_result)
    
    with pytest.raises(ValidationError) as exc_info:
        await MatchService.conduct_toss(sample_match_id, sample_user_id, request, mock_db_session)
    
    assert "match teams" in str(exc_info.value).lower()


# ============================================================================
# GET/LIST MATCH TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_match_not_found(mock_db_session, sample_match_id):
    """Test get match fails when match doesn't exist"""
    match_result = MagicMock()
    match_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=match_result)
    
    with pytest.raises(NotFoundError):
        await MatchService.get_match(sample_match_id, db=mock_db_session)


@pytest.mark.asyncio
async def test_list_matches_empty(mock_db_session):
    """Test match listing returns empty when no matches"""
    count_result = MagicMock()
    count_result.scalar = MagicMock(return_value=0)
    
    matches_result = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all = MagicMock(return_value=[])
    matches_result.scalars = MagicMock(return_value=scalars_mock)
    
    mock_db_session.execute = AsyncMock(side_effect=[count_result, matches_result])
    
    result = await MatchService.list_matches(db=mock_db_session, page=1, page_size=10)
    
    assert result.total == 0
    assert len(result.matches) == 0


# ============================================================================
# MATCH CODE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_generate_match_code_unique(mock_db_session):
    """Test match code generation creates unique codes"""
    existing_result = MagicMock()
    existing_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=existing_result)
    
    code = await MatchService._generate_match_code(mock_db_session)
    
    assert code.startswith("KRD-")
    assert len(code) == 8  # KRD-XXXX format
