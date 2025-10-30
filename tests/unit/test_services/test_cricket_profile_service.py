"""
Unit Tests for Cricket Profile Service
Tests all 6 service methods with mocked database

Test Coverage:
- create_sport_profile: Happy path + duplicate error + user not found
- get_sport_profile: Happy path + not found error
- list_user_sport_profiles: Happy path + empty list + filtered by sport
- create_cricket_profile: Happy path + sport profile not found + invalid sport type + duplicate
- get_cricket_profile: Happy path + with user info + not found
- update_cricket_profile: Happy path + partial update + not found

Mocking Strategy:
- Mock AsyncSession for database operations
- Mock execute() results with ScalarResult
- Use MagicMock for ORM objects
"""
import pytest
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.cricket.profile import CricketProfileService
from src.schemas.cricket.profile import (
    SportProfileCreate, CricketPlayerProfileCreate, CricketPlayerProfileUpdate
)
from src.models.enums import SportType, ProfileVisibility, PlayingRole, BattingStyle, BowlingStyle
from src.core.exceptions import (
    DuplicateSportProfileError, SportProfileNotFoundError,
    CricketProfileNotFoundError, DuplicateCricketProfileError,
    InvalidSportTypeError, NotFoundError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock AsyncSession for database operations"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def sample_user_id():
    """Sample user UUID"""
    return uuid4()


@pytest.fixture
def sample_sport_profile_id():
    """Sample sport profile UUID"""
    return uuid4()


@pytest.fixture
def sample_cricket_profile_id():
    """Sample cricket profile UUID"""
    return uuid4()


@pytest.fixture
def mock_user(sample_user_id):
    """Mock UserAuth object"""
    user = MagicMock()
    user.user_id = sample_user_id
    user.email = "test@test.com"
    return user


@pytest.fixture
def mock_sport_profile(sample_user_id, sample_sport_profile_id):
    """Mock SportProfile object"""
    profile = MagicMock()
    profile.id = sample_sport_profile_id
    profile.user_id = sample_user_id
    profile.sport_type = SportType.CRICKET
    profile.visibility = ProfileVisibility.PUBLIC
    profile.is_verified = False
    profile.verification_proof = None
    profile.verified_at = None
    profile.created_at = datetime.utcnow()
    profile.updated_at = datetime.utcnow()
    return profile


@pytest.fixture
def mock_cricket_profile(sample_sport_profile_id, sample_cricket_profile_id):
    """Mock CricketPlayerProfile object"""
    profile = MagicMock()
    profile.id = sample_cricket_profile_id
    profile.sport_profile_id = sample_sport_profile_id
    profile.playing_role = PlayingRole.ALL_ROUNDER
    profile.batting_style = BattingStyle.RIGHT_HAND
    profile.bowling_style = BowlingStyle.RIGHT_ARM_MEDIUM
    profile.jersey_number = 7
    # Stats
    profile.matches_played = 0
    profile.total_runs = 0
    profile.total_wickets = 0
    profile.catches = 0
    profile.stumpings = 0
    profile.run_outs = 0
    profile.batting_avg = None
    profile.strike_rate = None
    profile.highest_score = 0
    profile.fifties = 0
    profile.hundreds = 0
    profile.balls_faced = 0
    profile.fours = 0
    profile.sixes = 0
    profile.bowling_avg = None
    profile.economy_rate = None
    profile.best_bowling = None
    profile.five_wickets = 0
    profile.ten_wickets = 0
    profile.balls_bowled = 0
    profile.runs_conceded = 0
    profile.maidens = 0
    profile.stats_last_updated = None
    profile.created_at = datetime.utcnow()
    profile.updated_at = datetime.utcnow()
    return profile


# ============================================================================
# SPORT PROFILE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_sport_profile_success(mock_db_session, sample_user_id, mock_user):
    """Test successful sport profile creation"""
    # Arrange
    request = SportProfileCreate(
        sport_type=SportType.CRICKET,
        visibility=ProfileVisibility.PUBLIC
    )
    
    # Mock user exists check
    user_result = MagicMock()
    user_result.scalar_one_or_none = MagicMock(return_value=mock_user)
    
    # Mock no existing profile
    existing_result = MagicMock()
    existing_result.scalar_one_or_none = MagicMock(return_value=None)
    
    mock_db_session.execute = AsyncMock(side_effect=[user_result, existing_result])
    
    # Mock refresh to set the ID on the created object
    def mock_refresh_side_effect(obj):
        obj.id = uuid4()
        obj.created_at = datetime.utcnow()
        obj.updated_at = datetime.utcnow()
    
    mock_db_session.refresh.side_effect = mock_refresh_side_effect
    
    # Act
    result = await CricketProfileService.create_sport_profile(sample_user_id, request, mock_db_session)
    
    # Assert
    assert result.sport_type == SportType.CRICKET
    assert result.visibility == ProfileVisibility.PUBLIC
    assert result.is_verified is False
    assert result.id is not None
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_sport_profile_user_not_found(mock_db_session, sample_user_id):
    """Test sport profile creation fails when user doesn't exist"""
    # Arrange
    request = SportProfileCreate(
        sport_type=SportType.CRICKET,
        visibility=ProfileVisibility.PUBLIC
    )
    
    # Mock user not found
    user_result = MagicMock()
    user_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=user_result)
    
    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await CricketProfileService.create_sport_profile(sample_user_id, request, mock_db_session)
    
    assert exc_info.value.error_code == "USER_NOT_FOUND"
    mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_sport_profile_duplicate(mock_db_session, sample_user_id, mock_user, mock_sport_profile):
    """Test sport profile creation fails when profile already exists"""
    # Arrange
    request = SportProfileCreate(
        sport_type=SportType.CRICKET,
        visibility=ProfileVisibility.PUBLIC
    )
    
    # Mock user exists
    user_result = MagicMock()
    user_result.scalar_one_or_none = MagicMock(return_value=mock_user)
    
    # Mock existing profile found
    existing_result = MagicMock()
    existing_result.scalar_one_or_none = MagicMock(return_value=mock_sport_profile)
    
    mock_db_session.execute = AsyncMock(side_effect=[user_result, existing_result])
    
    # Act & Assert
    with pytest.raises(DuplicateSportProfileError):
        await CricketProfileService.create_sport_profile(sample_user_id, request, mock_db_session)
    
    mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_get_sport_profile_success(mock_db_session, sample_sport_profile_id, mock_sport_profile):
    """Test successful sport profile retrieval"""
    # Arrange
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=mock_sport_profile)
    mock_db_session.execute = AsyncMock(return_value=result_mock)
    
    # Act
    result = await CricketProfileService.get_sport_profile(sample_sport_profile_id, mock_db_session)
    
    # Assert
    assert result.id == sample_sport_profile_id
    assert result.sport_type == SportType.CRICKET


@pytest.mark.asyncio
async def test_get_sport_profile_not_found(mock_db_session, sample_sport_profile_id):
    """Test sport profile retrieval fails when not found"""
    # Arrange
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=result_mock)
    
    # Act & Assert
    with pytest.raises(SportProfileNotFoundError):
        await CricketProfileService.get_sport_profile(sample_sport_profile_id, mock_db_session)


@pytest.mark.asyncio
async def test_list_user_sport_profiles_success(mock_db_session, sample_user_id, mock_sport_profile):
    """Test listing user's sport profiles"""
    # Arrange
    result_mock = MagicMock()
    result_mock.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_sport_profile])))
    mock_db_session.execute = AsyncMock(return_value=result_mock)
    
    # Act
    result = await CricketProfileService.list_user_sport_profiles(sample_user_id, None, mock_db_session)
    
    # Assert
    assert len(result) == 1
    assert result[0].id == mock_sport_profile.id


@pytest.mark.asyncio
async def test_list_user_sport_profiles_empty(mock_db_session, sample_user_id):
    """Test listing returns empty when no profiles exist"""
    # Arrange
    result_mock = MagicMock()
    result_mock.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_db_session.execute = AsyncMock(return_value=result_mock)
    
    # Act
    result = await CricketProfileService.list_user_sport_profiles(sample_user_id, None, mock_db_session)
    
    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_list_user_sport_profiles_filtered(mock_db_session, sample_user_id, mock_sport_profile):
    """Test listing with sport type filter"""
    # Arrange
    result_mock = MagicMock()
    result_mock.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_sport_profile])))
    mock_db_session.execute = AsyncMock(return_value=result_mock)
    
    # Act
    result = await CricketProfileService.list_user_sport_profiles(
        sample_user_id, SportType.CRICKET, mock_db_session
    )
    
    # Assert
    assert len(result) == 1
    assert result[0].sport_type == SportType.CRICKET


# ============================================================================
# CRICKET PLAYER PROFILE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_cricket_profile_success(mock_db_session, sample_sport_profile_id, mock_sport_profile):
    """Test successful cricket profile creation"""
    # Arrange
    request = CricketPlayerProfileCreate(
        sport_profile_id=sample_sport_profile_id,
        playing_role=PlayingRole.BATSMAN,
        batting_style=BattingStyle.RIGHT_HAND,
        bowling_style=None,
        jersey_number=10
    )
    
    # Mock sport profile exists and is CRICKET type
    sport_result = MagicMock()
    sport_result.scalar_one_or_none = MagicMock(return_value=mock_sport_profile)
    
    # Mock no existing cricket profile
    existing_result = MagicMock()
    existing_result.scalar_one_or_none = MagicMock(return_value=None)
    
    mock_db_session.execute = AsyncMock(side_effect=[sport_result, existing_result])
    
    # Mock refresh to set the ID on the created object
    def mock_refresh_side_effect(obj):
        obj.id = uuid4()
        obj.created_at = datetime.utcnow()
        obj.updated_at = datetime.utcnow()
    
    mock_db_session.refresh.side_effect = mock_refresh_side_effect
    
    # Act
    result = await CricketProfileService.create_cricket_profile(request, mock_db_session)
    
    # Assert
    assert result.sport_profile_id == sample_sport_profile_id
    assert result.playing_role == PlayingRole.BATSMAN
    assert result.id is not None
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_cricket_profile_sport_not_found(mock_db_session, sample_sport_profile_id):
    """Test cricket profile creation fails when sport profile doesn't exist"""
    # Arrange
    request = CricketPlayerProfileCreate(
        sport_profile_id=sample_sport_profile_id,
        playing_role=PlayingRole.BATSMAN,
        batting_style=BattingStyle.RIGHT_HAND
    )
    
    # Mock sport profile not found
    sport_result = MagicMock()
    sport_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=sport_result)
    
    # Act & Assert
    with pytest.raises(SportProfileNotFoundError):
        await CricketProfileService.create_cricket_profile(request, mock_db_session)


@pytest.mark.asyncio
async def test_create_cricket_profile_invalid_sport_type(mock_db_session, sample_sport_profile_id):
    """Test cricket profile creation fails when sport profile is not CRICKET type"""
    # Arrange
    request = CricketPlayerProfileCreate(
        sport_profile_id=sample_sport_profile_id,
        playing_role=PlayingRole.BATSMAN,
        batting_style=BattingStyle.RIGHT_HAND
    )
    
    # Mock sport profile is FOOTBALL
    football_profile = MagicMock()
    football_profile.sport_type = SportType.FOOTBALL
    sport_result = MagicMock()
    sport_result.scalar_one_or_none = MagicMock(return_value=football_profile)
    mock_db_session.execute = AsyncMock(return_value=sport_result)
    
    # Act & Assert
    with pytest.raises(InvalidSportTypeError):
        await CricketProfileService.create_cricket_profile(request, mock_db_session)


@pytest.mark.asyncio
async def test_create_cricket_profile_duplicate(mock_db_session, sample_sport_profile_id, mock_sport_profile, mock_cricket_profile):
    """Test cricket profile creation fails when cricket profile already exists"""
    # Arrange
    request = CricketPlayerProfileCreate(
        sport_profile_id=sample_sport_profile_id,
        playing_role=PlayingRole.BATSMAN,
        batting_style=BattingStyle.RIGHT_HAND
    )
    
    # Mock sport profile exists
    sport_result = MagicMock()
    sport_result.scalar_one_or_none = MagicMock(return_value=mock_sport_profile)
    
    # Mock cricket profile already exists
    existing_result = MagicMock()
    existing_result.scalar_one_or_none = MagicMock(return_value=mock_cricket_profile)
    
    mock_db_session.execute = AsyncMock(side_effect=[sport_result, existing_result])
    
    # Act & Assert
    with pytest.raises(DuplicateCricketProfileError):
        await CricketProfileService.create_cricket_profile(request, mock_db_session)


@pytest.mark.asyncio
async def test_get_cricket_profile_success(mock_db_session, sample_cricket_profile_id, mock_cricket_profile):
    """Test successful cricket profile retrieval"""
    # Arrange
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=mock_cricket_profile)
    mock_db_session.execute = AsyncMock(return_value=result_mock)
    
    # Act
    result = await CricketProfileService.get_cricket_profile(sample_cricket_profile_id, mock_db_session, False)
    
    # Assert
    assert result.id == sample_cricket_profile_id
    assert result.playing_role == PlayingRole.ALL_ROUNDER
    assert result.career_stats.matches_played == 0


@pytest.mark.asyncio
async def test_get_cricket_profile_not_found(mock_db_session, sample_cricket_profile_id):
    """Test cricket profile retrieval fails when not found"""
    # Arrange
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=result_mock)
    
    # Act & Assert
    with pytest.raises(CricketProfileNotFoundError):
        await CricketProfileService.get_cricket_profile(sample_cricket_profile_id, mock_db_session, False)


@pytest.mark.asyncio
async def test_update_cricket_profile_success(mock_db_session, sample_cricket_profile_id, mock_cricket_profile):
    """Test successful cricket profile update"""
    # Arrange
    request = CricketPlayerProfileUpdate(
        playing_role=PlayingRole.BOWLER,
        jersey_number=99
    )
    
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=mock_cricket_profile)
    mock_db_session.execute = AsyncMock(return_value=result_mock)
    
    # Act
    result = await CricketProfileService.update_cricket_profile(sample_cricket_profile_id, request, mock_db_session)
    
    # Assert
    assert result.id == sample_cricket_profile_id
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_cricket_profile_not_found(mock_db_session, sample_cricket_profile_id):
    """Test cricket profile update fails when not found"""
    # Arrange
    request = CricketPlayerProfileUpdate(jersey_number=99)
    
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=result_mock)
    
    # Act & Assert
    with pytest.raises(CricketProfileNotFoundError):
        await CricketProfileService.update_cricket_profile(sample_cricket_profile_id, request, mock_db_session)


@pytest.mark.asyncio
async def test_update_cricket_profile_partial(mock_db_session, sample_cricket_profile_id, mock_cricket_profile):
    """Test partial update only changes provided fields"""
    # Arrange
    request = CricketPlayerProfileUpdate(jersey_number=15)  # Only update jersey
    
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=mock_cricket_profile)
    mock_db_session.execute = AsyncMock(return_value=result_mock)
    
    # Act
    result = await CricketProfileService.update_cricket_profile(sample_cricket_profile_id, request, mock_db_session)
    
    # Assert - Other fields should remain unchanged
    assert result.playing_role == PlayingRole.ALL_ROUNDER  # Original value
    assert result.batting_style == BattingStyle.RIGHT_HAND  # Original value
    mock_db_session.commit.assert_called_once()
