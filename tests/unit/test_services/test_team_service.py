"""
Unit Tests for Team Service
Tests TeamService methods with properly mocked database calls

Focus: Core CRUD operations, permission checks, JSONB validation
Pattern: AAA (Arrange-Act-Assert) with AsyncMock for DB
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.services.cricket.team import TeamService
from src.schemas.cricket.team import (
    TeamCreateRequest, TeamUpdateRequest, TeamMembershipCreateRequest,
    TeamColorsSchema, HomeGroundSchema
)
from src.models.enums import SportType, TeamType, TeamMemberRole, MembershipStatus
from src.core.exceptions import ConflictError, ForbiddenError, NotFoundError


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
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.fixture
def sample_team_id():
    return uuid4()


@pytest.fixture
def mock_user(sample_user_id):
    """Mock UserAuth object"""
    user = MagicMock()
    user.user_id = sample_user_id
    user.email = "test@test.com"
    return user


@pytest.fixture
def mock_user_profile(sample_user_id):
    """Mock UserProfile object"""
    profile = MagicMock()
    profile.user_id = sample_user_id
    profile.name = "Test User"
    return profile


@pytest.fixture
def mock_sport_profile(sample_user_id):
    """Mock SportProfile object"""
    profile = MagicMock()
    profile.id = uuid4()
    profile.user_id = sample_user_id
    profile.sport_type = SportType.CRICKET
    return profile


@pytest.fixture
def mock_team(sample_user_id, sample_team_id):
    """Mock Team object"""
    team = MagicMock()
    team.id = sample_team_id
    team.name = "Test Team"
    team.short_name = "TT"
    team.sport_type = SportType.CRICKET
    team.team_type = TeamType.CLUB
    team.is_active = True
    team.created_by_user_id = sample_user_id
    team.team_colors = {"primary": "#FF0000"}
    team.home_ground = {"name": "Test Ground"}
    team.created_at = datetime.utcnow()
    team.updated_at = datetime.utcnow()
    team.logo_url = None
    
    # Add created_by property for Pydantic model_validate compatibility
    # (TeamResponse expects created_by but Team model has created_by_user_id)
    team.created_by = sample_user_id
    
    # Set creator_name and member_count to None (optional fields)
    team.creator_name = None
    team.member_count = None
    
    return team


# ============================================================================
# CREATE TEAM TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_team_success(mock_db_session, sample_user_id, mock_user, mock_sport_profile, mock_user_profile):
    """Test successful team creation"""
    # Arrange
    request = TeamCreateRequest(
        name="Mumbai Challengers",
        sport_type=SportType.CRICKET,
        team_type=TeamType.CLUB
    )
    
    # Mock DB queries in order they're called:
    # 1. User exists check
    user_result = MagicMock()
    user_result.scalar_one_or_none = MagicMock(return_value=mock_user)
    
    # 2. Duplicate team name check
    duplicate_result = MagicMock()
    duplicate_result.scalar_one_or_none = MagicMock(return_value=None)
    
    # 3. Sport profile query
    sport_profile_result = MagicMock()
    sport_profile_result.scalar_one_or_none = MagicMock(return_value=mock_sport_profile)
    
    # 4. User profile query (for creator name)
    user_profile_result = MagicMock()
    user_profile_result.scalar_one_or_none = MagicMock(return_value=mock_user_profile)
    
    mock_db_session.execute = AsyncMock(side_effect=[
        user_result, duplicate_result, sport_profile_result, user_profile_result
    ])
    
    # Mock refresh to set IDs
    def mock_refresh_side_effect(obj):
        if not hasattr(obj, 'id') or obj.id is None:
            obj.id = uuid4()
        obj.created_at = datetime.utcnow()
        obj.updated_at = datetime.utcnow()
    
    mock_db_session.refresh.side_effect = mock_refresh_side_effect
    
    # Act
    result = await TeamService.create_team(sample_user_id, request, mock_db_session)
    
    # Assert
    assert result.name == "Mumbai Challengers"
    assert result.short_name == "MC"  # Auto-generated from first letters
    assert result.sport_type == SportType.CRICKET
    assert mock_db_session.add.call_count == 2  # Team + creator membership
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_team_user_not_found(mock_db_session, sample_user_id):
    """Test team creation fails when user doesn't exist"""
    # Arrange
    request = TeamCreateRequest(
        name="Test Team",
        sport_type=SportType.CRICKET,
        team_type=TeamType.CLUB
    )
    
    # Mock user not found
    user_result = MagicMock()
    user_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=user_result)
    
    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await TeamService.create_team(sample_user_id, request, mock_db_session)
    
    assert "User not found" in str(exc_info.value)
    mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_team_duplicate_name(mock_db_session, sample_user_id, mock_user, mock_team):
    """Test team creation fails with duplicate name"""
    # Arrange
    request = TeamCreateRequest(
        name="Test Team",
        sport_type=SportType.CRICKET,
        team_type=TeamType.CLUB
    )
    
    # Mock user exists
    user_result = MagicMock()
    user_result.scalar_one_or_none = MagicMock(return_value=mock_user)
    
    # Mock duplicate team found
    duplicate_result = MagicMock()
    duplicate_result.scalar_one_or_none = MagicMock(return_value=mock_team)
    
    mock_db_session.execute = AsyncMock(side_effect=[user_result, duplicate_result])
    
    # Act & Assert
    with pytest.raises(ConflictError) as exc_info:
        await TeamService.create_team(sample_user_id, request, mock_db_session)
    
    assert "already exists" in str(exc_info.value)
    mock_db_session.add.assert_not_called()


# ============================================================================
# UPDATE TEAM TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_update_team_success(mock_db_session, sample_user_id, sample_team_id, mock_team):
    """Test successful team update"""
    # Arrange
    request = TeamUpdateRequest(
        logo_url="https://example.com/logo.png"
    )
    
    # Ensure mock_team has proper typed values for Pydantic validation
    mock_team.created_by_user_id = sample_user_id  # UUID type
    mock_team.member_count = 1
    mock_team.creator_name = "Test User"
    
    # Mock team exists
    team_result = MagicMock()
    team_result.scalar_one_or_none = MagicMock(return_value=mock_team)
    
    # Mock user is admin (creator check)
    admin_check_result = MagicMock()
    admin_check_result.scalar_one_or_none = MagicMock(return_value=mock_team)
    
    # Mock member count query
    count_result = MagicMock()
    count_result.scalar = MagicMock(return_value=1)
    
    # Mock user profile query
    user_profile_result = MagicMock()
    user_profile = MagicMock()
    user_profile.name = "Test User"
    user_profile_result.scalar_one_or_none = MagicMock(return_value=user_profile)
    
    mock_db_session.execute = AsyncMock(side_effect=[
        team_result, admin_check_result, count_result, user_profile_result
    ])
    
    # Act
    result = await TeamService.update_team(sample_team_id, sample_user_id, request, mock_db_session)
    
    # Assert
    assert mock_team.logo_url == "https://example.com/logo.png"
    assert result.name == "Test Team"  # Verify response was created
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_team_not_found(mock_db_session, sample_user_id, sample_team_id):
    """Test update fails when team doesn't exist"""
    # Arrange
    request = TeamUpdateRequest(logo_url="https://example.com/logo.png")
    
    # Mock team not found
    team_result = MagicMock()
    team_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=team_result)
    
    # Act & Assert
    with pytest.raises(NotFoundError):
        await TeamService.update_team(sample_team_id, sample_user_id, request, mock_db_session)


@pytest.mark.asyncio
async def test_update_team_forbidden(mock_db_session, sample_team_id, mock_team):
    """Test update fails when user is not admin"""
    # Arrange
    unauthorized_user_id = uuid4()
    request = TeamUpdateRequest(logo_url="https://example.com/logo.png")
    
    # Mock team exists
    team_result = MagicMock()
    team_result.scalar_one_or_none = MagicMock(return_value=mock_team)
    
    # Mock user is NOT admin (both checks return None)
    admin_check_result = MagicMock()
    admin_check_result.scalar_one_or_none = MagicMock(return_value=None)
    
    mock_db_session.execute = AsyncMock(side_effect=[team_result, admin_check_result, admin_check_result])
    
    # Act & Assert
    with pytest.raises(ForbiddenError):
        await TeamService.update_team(sample_team_id, unauthorized_user_id, request, mock_db_session)


# ============================================================================
# GET TEAM TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_team_success(mock_db_session, sample_team_id, mock_team):
    """Test successful team retrieval"""
    # Arrange
    # Ensure mock_team has proper typed values
    mock_team.created_by_user_id = uuid4()
    mock_team.member_count = 1
    mock_team.creator_name = "Test User"
    
    # Mock team exists
    team_result = MagicMock()
    team_result.scalar_one_or_none = MagicMock(return_value=mock_team)
    
    # Mock creator profile
    creator_result = MagicMock()
    creator_profile = MagicMock()
    creator_profile.name = "Test User"
    creator_result.scalar_one_or_none = MagicMock(return_value=creator_profile)
    
    # Mock member count
    count_result = MagicMock()
    count_result.scalar = MagicMock(return_value=1)
    
    mock_db_session.execute = AsyncMock(side_effect=[team_result, count_result, creator_result])
    
    # Act
    result = await TeamService.get_team(sample_team_id, include_members=False, db=mock_db_session)
    
    # Assert
    assert result.id == sample_team_id
    assert result.name == "Test Team"


@pytest.mark.asyncio
async def test_get_team_not_found(mock_db_session, sample_team_id):
    """Test get team fails when team doesn't exist"""
    # Arrange
    team_result = MagicMock()
    team_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=team_result)
    
    # Act & Assert
    with pytest.raises(NotFoundError):
        await TeamService.get_team(sample_team_id, db=mock_db_session)


# ============================================================================
# LIST TEAMS TESTS  
# ============================================================================

@pytest.mark.asyncio
async def test_list_teams_success(mock_db_session, mock_team):
    """Test successful team listing with pagination"""
    # Arrange
    # Mock count query
    count_result = MagicMock()
    count_result.scalar = MagicMock(return_value=5)
    
    # Mock teams query (scalars().all())
    teams_result = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all = MagicMock(return_value=[mock_team, mock_team])
    teams_result.scalars = MagicMock(return_value=scalars_mock)
    
    # Mock member count queries (one for each team)
    member_count_result1 = MagicMock()
    member_count_result1.scalar = MagicMock(return_value=5)
    
    member_count_result2 = MagicMock()
    member_count_result2.scalar = MagicMock(return_value=3)
    
    mock_db_session.execute = AsyncMock(side_effect=[
        count_result, teams_result, member_count_result1, member_count_result2
    ])
    
    # Act
    result = await TeamService.list_teams(
        db=mock_db_session,
        page=1,
        page_size=10
    )
    
    # Assert
    assert result.total == 5
    assert len(result.teams) == 2  # It's "teams" not "items"


@pytest.mark.asyncio
async def test_list_teams_empty(mock_db_session):
    """Test team listing returns empty when no teams"""
    # Arrange
    count_result = MagicMock()
    count_result.scalar = MagicMock(return_value=0)
    
    teams_result = MagicMock()
    teams_result.all = MagicMock(return_value=[])
    
    mock_db_session.execute = AsyncMock(side_effect=[count_result, teams_result])
    
    # Act
    result = await TeamService.list_teams(db=mock_db_session, page=1, page_size=10)
    
    # Assert
    assert result.total == 0
    assert len(result.teams) == 0  # It's "teams" not "items"


# ============================================================================
# ADD MEMBER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_add_member_success(mock_db_session, sample_user_id, sample_team_id, mock_team, mock_user, mock_sport_profile):
    """Test successful member addition"""
    # Arrange
    new_member_id = uuid4()
    request = TeamMembershipCreateRequest(
        user_id=new_member_id,
        roles=[TeamMemberRole.PLAYER],
        jersey_number=10
    )
    
    # Mock cricket profile
    mock_cricket_profile = MagicMock()
    mock_cricket_profile.id = uuid4()
    
    # Mock DB queries in order:
    # 1. Team exists
    team_result = MagicMock()
    team_result.scalar_one_or_none = MagicMock(return_value=mock_team)
    
    # 2. User is admin (creator check)
    admin_check_result = MagicMock()
    admin_check_result.scalar_one_or_none = MagicMock(return_value=mock_team)
    
    # 3. New user exists
    user_result = MagicMock()
    user_result.scalar_one_or_none = MagicMock(return_value=mock_user)
    
    # 4. No existing membership
    existing_membership_result = MagicMock()
    existing_membership_result.scalar_one_or_none = MagicMock(return_value=None)
    
    # 5. Sport profile exists
    sport_profile_result = MagicMock()
    sport_profile_result.scalar_one_or_none = MagicMock(return_value=mock_sport_profile)
    
    # 6. Cricket profile exists
    cricket_profile_result = MagicMock()
    cricket_profile_result.scalar_one_or_none = MagicMock(return_value=mock_cricket_profile)
    
    # 7. No jersey conflict
    jersey_result = MagicMock()
    jersey_result.scalar_one_or_none = MagicMock(return_value=None)
    
    mock_db_session.execute = AsyncMock(side_effect=[
        team_result, admin_check_result, user_result, existing_membership_result,
        sport_profile_result, cricket_profile_result, jersey_result
    ])
    
    def mock_refresh_side_effect(obj):
        if not hasattr(obj, 'id') or obj.id is None:
            obj.id = uuid4()
    
    mock_db_session.refresh.side_effect = mock_refresh_side_effect
    
    # Act
    result = await TeamService.add_member(sample_team_id, sample_user_id, request, mock_db_session)
    
    # Assert
    assert result.roles == [TeamMemberRole.PLAYER]
    assert result.jersey_number == 10
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_add_member_duplicate(mock_db_session, sample_user_id, sample_team_id, mock_team, mock_user):
    """Test member addition fails when user already member"""
    # Arrange
    request = TeamMembershipCreateRequest(
        user_id=sample_user_id,
        roles=[TeamMemberRole.PLAYER],
        jersey_number=10
    )
    
    mock_membership = MagicMock()
    mock_membership.status = MembershipStatus.ACTIVE
    
    # Mock team exists
    team_result = MagicMock()
    team_result.scalar_one_or_none = MagicMock(return_value=mock_team)
    
    # Mock user is admin
    admin_check_result = MagicMock()
    admin_check_result.scalar_one_or_none = MagicMock(return_value=mock_team)
    
    # Mock user exists
    user_result = MagicMock()
    user_result.scalar_one_or_none = MagicMock(return_value=mock_user)
    
    # Mock existing membership found
    existing_membership_result = MagicMock()
    existing_membership_result.scalar_one_or_none = MagicMock(return_value=mock_membership)
    
    mock_db_session.execute = AsyncMock(side_effect=[
        team_result, admin_check_result, user_result, existing_membership_result
    ])
    
    # Act & Assert
    with pytest.raises(ConflictError) as exc_info:
        await TeamService.add_member(sample_team_id, sample_user_id, request, mock_db_session)
    
    assert "already" in str(exc_info.value).lower()
    mock_db_session.add.assert_not_called()


# ============================================================================
# _IS_TEAM_ADMIN TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_is_team_admin_creator(mock_db_session, sample_user_id, sample_team_id, mock_team):
    """Test _is_team_admin returns True for creator"""
    # Arrange
    # Mock team exists with user as creator
    creator_check_result = MagicMock()
    creator_check_result.scalar_one_or_none = MagicMock(return_value=mock_team)
    mock_db_session.execute = AsyncMock(return_value=creator_check_result)
    
    # Act
    result = await TeamService._is_team_admin(sample_team_id, sample_user_id, mock_db_session)
    
    # Assert
    assert result is True


@pytest.mark.asyncio
async def test_is_team_admin_admin_role(mock_db_session, sample_team_id):
    """Test _is_team_admin returns True for admin role"""
    # Arrange
    non_creator_id = uuid4()
    
    mock_membership = MagicMock()
    mock_membership.roles = [TeamMemberRole.TEAM_ADMIN.value]
    
    # Mock not creator
    creator_check_result = MagicMock()
    creator_check_result.scalar_one_or_none = MagicMock(return_value=None)
    
    # Mock has admin role
    admin_role_result = MagicMock()
    admin_role_result.scalar_one_or_none = MagicMock(return_value=mock_membership)
    
    mock_db_session.execute = AsyncMock(side_effect=[creator_check_result, admin_role_result])
    
    # Act
    result = await TeamService._is_team_admin(sample_team_id, non_creator_id, mock_db_session)
    
    # Assert
    assert result is True


@pytest.mark.asyncio
async def test_is_team_admin_non_admin(mock_db_session, sample_team_id):
    """Test _is_team_admin returns False for non-admin"""
    # Arrange
    non_admin_id = uuid4()
    
    # Mock not creator
    creator_check_result = MagicMock()
    creator_check_result.scalar_one_or_none = MagicMock(return_value=None)
    
    # Mock not admin role
    admin_role_result = MagicMock()
    admin_role_result.scalar_one_or_none = MagicMock(return_value=None)
    
    mock_db_session.execute = AsyncMock(side_effect=[creator_check_result, admin_role_result])
    
    # Act
    result = await TeamService._is_team_admin(sample_team_id, non_admin_id, mock_db_session)
    
    # Assert
    assert result is False
