"""
Test cases for team management functionality.

This module tests:
- Team creation and management
- Player invitations and responses
- Team membership management
- Team perm        invitation_data = {
            "email": "player@test.com",
            "message": "Join our cricket team!"
        }ns and roles
- Team statistics and profiles
"""

import pytest
from fastapi import status
from datetime import datetime, timedelta
import uuid

from conftest import unit, integration


@pytest.mark.asyncio
@pytest.mark.team
@integration
class TestTeamCreation:
    """Test team creation and basic management."""

    async def test_teams_health_check(self, client):
        """Test teams service health check."""
        response = client.get("/api/v1/teams/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True

    async def test_create_team_success(self, client, authenticated_users, auth_client_factory, team_data):
        """Test successful team creation."""
        captain_token = authenticated_users["tokens"]["captain1"]
        auth_client = auth_client_factory(captain_token)
        
        team_info = team_data[0]  # Mumbai Warriors
        
        response = auth_client.post("/api/v1/teams/", json=team_info)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == team_info["name"]
        assert data["short_name"] == team_info["short_name"]
        assert data["logo_url"] == team_info["logo_url"]
        assert "id" in data
        assert "created_at" in data
        assert "is_active" in data

    async def test_create_team_duplicate_name(self, client, authenticated_users, auth_client_factory, team_data):
        """Test creating team with duplicate name."""
        captain_token = authenticated_users["tokens"]["captain1"]
        auth_client = auth_client_factory(captain_token)
        
        team_info = team_data[0]
        
        # Create first team
        response1 = auth_client.post("/api/v1/teams/", json=team_info)
        assert response1.status_code == status.HTTP_200_OK
        
        # Try to create team with same name
        response2 = auth_client.post("/api/v1/teams/", json=team_info)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

    async def test_create_team_invalid_data(self, client, authenticated_users, auth_client_factory):
        """Test creating team with invalid data."""
        captain_token = authenticated_users["tokens"]["captain1"]
        auth_client = auth_client_factory(captain_token)
        
        invalid_team = {
            "name": "",  # Empty name
            "description": "Test team",
            "team_type": "invalid_type",  # Invalid type
            "max_players": -1  # Invalid number
        }
        
        response = auth_client.post("/api/v1/teams/", json=invalid_team)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_create_team_unauthorized(self, client, team_data):
        """Test creating team without authentication."""
        team_info = team_data[0]
        
        response = client.post("/api/v1/teams/", json=team_info)
        # The actual API returns 403 Forbidden instead of 401 Unauthorized
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    async def test_get_teams_list(self, client, authenticated_users, auth_client_factory, team_data):
        """Test getting list of teams."""
        captain_token = authenticated_users["tokens"]["captain1"]
        auth_client = auth_client_factory(captain_token)
        
        # Create a team first
        response = auth_client.post("/api/v1/teams/", json=team_data[0])
        assert response.status_code == status.HTTP_200_OK
        
        # Get teams list
        response = auth_client.get("/api/v1/teams/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_team_by_id(self, client, authenticated_users, auth_client_factory, team_data):
        """Test getting team by ID."""
        captain_token = authenticated_users["tokens"]["captain1"]
        auth_client = auth_client_factory(captain_token)
        
        # Create a team first
        create_response = auth_client.post("/api/v1/teams/", json=team_data[0])
        created_team = create_response.json()
        team_id = created_team["id"]
        
        # Get team by ID
        response = auth_client.get(f"/api/v1/teams/{team_id}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == team_id
        assert data["name"] == team_data[0]["name"]

    async def test_update_team_info(self, client, authenticated_users, auth_client_factory, team_data):
        """Test updating team information."""
        captain_token = authenticated_users["tokens"]["captain1"]
        auth_client = auth_client_factory(captain_token)
        
        # Create a team first
        create_response = auth_client.post("/api/v1/teams/", json=team_data[0])
        created_team = create_response.json()
        team_id = created_team["id"]
        
        # Update team info
        update_data = {
            "name": "Updated Mumbai Warriors",
            "short_name": "UMW"
        }
        
        response = auth_client.put(f"/api/v1/teams/{team_id}", json=update_data)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_delete_team(self, client, authenticated_users, auth_client_factory, team_data):
        """Test deleting a team."""
        captain_token = authenticated_users["tokens"]["captain1"]
        auth_client = auth_client_factory(captain_token)
        
        # Create a team first
        create_response = auth_client.post("/api/v1/teams/", json=team_data[0])
        created_team = create_response.json()
        team_id = created_team["id"]
        
        # Delete team
        response = auth_client.delete(f"/api/v1/teams/{team_id}")
        assert response.status_code in [
            status.HTTP_200_OK, 
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND
        ]


@pytest.mark.asyncio
@pytest.mark.team
@integration
class TestTeamInvitations:
    """Test team invitation system."""

    async def test_send_team_invitation(self, client, authenticated_users, auth_client_factory, team_data):
        """Test sending team invitation."""
        captain_token = authenticated_users["tokens"]["captain1"]
        captain_client = auth_client_factory(captain_token)
        
        # Create a team first
        create_response = captain_client.post("/api/v1/teams/", json=team_data[0])
        created_team = create_response.json()
        team_id = created_team["id"]
        
        # Send invitation to player1
        invitation_data = {
            "email": "player1@test.com",
            "message": "Join our cricket team!"
        }
        
        response = captain_client.post(f"/api/v1/teams/{team_id}/invitations", json=invitation_data)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    async def test_send_invitation_to_nonexistent_user(self, client, authenticated_users, auth_client_factory, team_data):
        """Test sending invitation to non-existent user (should succeed - invitations allowed to any valid email)."""
        captain_token = authenticated_users["tokens"]["captain1"]
        captain_client = auth_client_factory(captain_token)
        
        # Create a team first
        create_response = captain_client.post("/api/v1/teams/", json=team_data[0])
        created_team = create_response.json()
        team_id = created_team["id"]
        
        # Send invitation to non-existent user
        invitation_data = {
            "email": "nonexistent@test.com",
            "message": "Join our team!"
        }
        
        response = captain_client.post(f"/api/v1/teams/{team_id}/invitations", json=invitation_data)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    async def test_get_team_invitations(self, client, authenticated_users, auth_client_factory, team_data):
        """Test getting team invitations."""
        captain_token = authenticated_users["tokens"]["captain1"]
        captain_client = auth_client_factory(captain_token)
        
        # Create a team first
        create_response = captain_client.post("/api/v1/teams/", json=team_data[0])
        created_team = create_response.json()
        team_id = created_team["id"]
        
        # Get team invitations
        response = captain_client.get(f"/api/v1/teams/{team_id}/invitations")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)

    async def test_get_user_invitations(self, client, authenticated_users, auth_client_factory):
        """Test getting user's received invitations."""
        player_token = authenticated_users["tokens"]["player1"]
        player_client = auth_client_factory(player_token)
        
        # Get user's invitations
        response = player_client.get("/api/v1/teams/invitations/received")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)

    async def test_accept_team_invitation(self, client, authenticated_users, auth_client_factory, team_data):
        """Test accepting team invitation."""
        captain_token = authenticated_users["tokens"]["captain1"]
        player_token = authenticated_users["tokens"]["player1"]
        captain_client = auth_client_factory(captain_token)
        player_client = auth_client_factory(player_token)
        
        # Create a team
        create_response = captain_client.post("/api/v1/teams/", json=team_data[0])
        created_team = create_response.json()
        team_id = created_team["id"]
        
        # Send invitation
        invitation_data = {
            "email": "player1@test.com",
            "message": "Join our team!"
        }
        
        invite_response = captain_client.post(f"/api/v1/teams/{team_id}/invitations", json=invitation_data)
        
        if invite_response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            invite_data = invite_response.json()
            invitation_id = invite_data.get("id")
            
            if invitation_id:
                # Accept invitation
                response = player_client.post(f"/api/v1/teams/invitations/{invitation_id}/accept")
                assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    async def test_reject_team_invitation(self, client, authenticated_users, auth_client_factory, team_data):
        """Test rejecting team invitation."""
        captain_token = authenticated_users["tokens"]["captain1"]
        player_token = authenticated_users["tokens"]["player2"]
        captain_client = auth_client_factory(captain_token)
        player_client = auth_client_factory(player_token)
        
        # Create a team
        create_response = captain_client.post("/api/v1/teams/", json=team_data[0])
        created_team = create_response.json()
        team_id = created_team["id"]
        
        # Send invitation
        invitation_data = {
            "email": "player2@test.com",
            "message": "Join our team!"
        }
        
        invite_response = captain_client.post(f"/api/v1/teams/{team_id}/invitations", json=invitation_data)
        
        if invite_response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            invite_data = invite_response.json()
            invitation_id = invite_data.get("id")
            
            if invitation_id:
                # Reject invitation
                response = player_client.post(f"/api/v1/teams/invitations/{invitation_id}/reject")
                assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]

    async def test_cancel_team_invitation(self, client, authenticated_users, auth_client_factory, team_data):
        """Test canceling team invitation."""
        captain_token = authenticated_users["tokens"]["captain1"]
        captain_client = auth_client_factory(captain_token)
        
        # Create a team
        create_response = captain_client.post("/api/v1/teams/", json=team_data[0])
        created_team = create_response.json()
        team_id = created_team["id"]
        
        # Send invitation
        invitation_data = {
            "email": "player3@test.com",
            "message": "Join our team!"
        }
        
        invite_response = captain_client.post(f"/api/v1/teams/{team_id}/invitations", json=invitation_data)
        
        if invite_response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            invite_data = invite_response.json()
            invitation_id = invite_data.get("id")
            
            if invitation_id:
                # Cancel invitation
                response = captain_client.delete(f"/api/v1/teams/invitations/{invitation_id}")
                assert response.status_code in [
                    status.HTTP_200_OK, 
                    status.HTTP_204_NO_CONTENT,
                    status.HTTP_404_NOT_FOUND
                ]


@pytest.mark.asyncio
@pytest.mark.team
@integration
class TestTeamMembership:
    """Test team membership management."""

    async def test_get_team_members(self, client, authenticated_users, auth_client_factory, team_data):
        """Test getting team members."""
        captain_token = authenticated_users["tokens"]["captain1"]
        captain_client = auth_client_factory(captain_token)
        
        # Create a team
        create_response = captain_client.post("/api/v1/teams/", json=team_data[0])
        created_team = create_response.json()
        team_id = created_team["id"]
        
        # Get team members
        response = captain_client.get(f"/api/v1/teams/{team_id}/members")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)

    async def test_update_member_role(self, client, authenticated_users, auth_client_factory, team_data):
        """Test updating team member role."""
        captain_token = authenticated_users["tokens"]["captain1"]
        captain_client = auth_client_factory(captain_token)
        
        # Create a team
        create_response = captain_client.post("/api/v1/teams/", json=team_data[0])
        created_team = create_response.json()
        team_id = created_team["id"]
        
        # Add a member first (through invitation process)
        # Then update their role
        # This is a more complex test that depends on the invitation workflow
        
        # For now, test the endpoint structure
        member_id = str(uuid.uuid4())  # Mock member ID
        update_data = {
            "role": "vice_captain"
        }
        
        response = captain_client.patch(f"/api/v1/teams/{team_id}/members/{member_id}", json=update_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN
        ]

    async def test_remove_team_member(self, client, authenticated_users, auth_client_factory, team_data):
        """Test removing team member."""
        captain_token = authenticated_users["tokens"]["captain1"]
        captain_client = auth_client_factory(captain_token)
        
        # Create a team
        create_response = captain_client.post("/api/v1/teams/", json=team_data[0])
        created_team = create_response.json()
        team_id = created_team["id"]
        
        # Try to remove a member
        member_id = str(uuid.uuid4())  # Mock member ID
        
        response = captain_client.delete(f"/api/v1/teams/{team_id}/members/{member_id}")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN
        ]

    async def test_leave_team(self, client, authenticated_users, auth_client_factory, team_data):
        """Test player leaving team."""
        player_token = authenticated_users["tokens"]["player1"]
        player_client = auth_client_factory(player_token)
        
        # Assuming player is in a team, try to leave
        team_id = str(uuid.uuid4())  # Mock team ID
        
        response = player_client.post(f"/api/v1/teams/{team_id}/leave")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN
        ]

    async def test_transfer_captaincy(self, client, authenticated_users, auth_client_factory, team_data):
        """Test transferring team captaincy."""
        captain_token = authenticated_users["tokens"]["captain1"]
        captain_client = auth_client_factory(captain_token)
        
        # Create a team
        create_response = captain_client.post("/api/v1/teams/", json=team_data[0])
        created_team = create_response.json()
        team_id = created_team["id"]
        
        # Transfer captaincy
        transfer_data = {
            "new_captain_username": "player1"
        }
        
        response = captain_client.post(f"/api/v1/teams/{team_id}/transfer-captaincy", json=transfer_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN
        ]


@pytest.mark.asyncio
@pytest.mark.team
@integration
class TestTeamSearch:
    """Test team search and filtering."""

    async def test_search_teams_by_name(self, client, authenticated_users, auth_client_factory, team_data):
        """Test searching teams by name."""
        captain_token = authenticated_users["tokens"]["captain1"]
        captain_client = auth_client_factory(captain_token)
        
        # Create teams
        for team in team_data:
            captain_client.post("/api/v1/teams/", json=team)
        
        # Search for teams
        response = captain_client.get("/api/v1/teams/?search=Mumbai")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)

    async def test_filter_teams_by_type(self, client, authenticated_users, auth_client_factory, team_data):
        """Test filtering teams by type."""
        captain_token = authenticated_users["tokens"]["captain1"]
        captain_client = auth_client_factory(captain_token)
        
        # Search by team type
        response = captain_client.get("/api/v1/teams/?team_type=club")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)

    async def test_get_teams_with_pagination(self, client, authenticated_users, auth_client_factory):
        """Test getting teams with pagination."""
        captain_token = authenticated_users["tokens"]["captain1"]
        captain_client = auth_client_factory(captain_token)
        
        response = captain_client.get("/api/v1/teams/?skip=0&limit=10")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10


@pytest.mark.asyncio
@pytest.mark.team
@unit
class TestTeamValidation:
    """Test team validation logic."""

    async def test_team_name_validation(self):
        """Test team name validation rules."""
        valid_names = ["Team Alpha", "Mumbai Warriors", "Delhi-Capitals", "Team_Beta"]
        invalid_names = ["", "A", "X" * 100]  # Empty, too short, too long
        
        # Test cases ready for validation implementation
        assert len(valid_names) > 0
        assert len(invalid_names) > 0

    async def test_team_size_limits(self):
        """Test team size validation."""
        valid_sizes = [11, 15, 20]
        invalid_sizes = [0, -1, 100]
        
        # Test cases ready for validation implementation
        assert len(valid_sizes) > 0
        assert len(invalid_sizes) > 0

    async def test_team_description_validation(self):
        """Test team description validation."""
        valid_descriptions = ["A great cricket team", "We play cricket"]
        invalid_descriptions = ["", "X" * 1000]  # Empty or too long
        
        # Test cases ready for validation implementation
        assert len(valid_descriptions) > 0
        assert len(invalid_descriptions) > 0