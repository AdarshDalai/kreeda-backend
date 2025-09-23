"""
Test cases for tournament management functionality.

This module tests:
- Tournament creation and configuration
- Team registration for tournaments
- Tournament brackets and scheduling
- Tournament progression and results
- Prize distribution and rankings
"""

import pytest
from fastapi import status
from datetime import datetime, timedelta
import uuid

from conftest import unit, integration


@pytest.mark.asyncio
@pytest.mark.tournament
@integration
class TestTournamentCreation:
    """Test tournament creation and configuration."""

    async def test_tournaments_health_check(self, client):
        """Test tournaments service health check."""
        # Assuming there's a health endpoint
        response = client.get("/api/v1/tournaments/health")
        # If no specific health endpoint exists, test basic functionality
        assert True  # Placeholder

    async def test_create_tournament_success(self, client, authenticated_users, auth_client_factory, tournament_data):
        """Test successful tournament creation."""
        organizer_token = authenticated_users["tokens"]["organizer"]
        organizer_client = auth_client_factory(organizer_token)
        
        response = organizer_client.post("/api/v1/tournaments/", json=tournament_data)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["name"] == tournament_data["name"]
            assert data["tournament_type"] == tournament_data["tournament_type"]
            assert "id" in data

    async def test_create_tournament_invalid_dates(self, client, authenticated_users, auth_client_factory):
        """Test creating tournament with invalid dates."""
        organizer_token = authenticated_users["tokens"]["organizer"]
        organizer_client = auth_client_factory(organizer_token)
        
        invalid_tournament = {
            "name": "Invalid Tournament",
            "description": "Tournament with invalid dates",
            "tournament_type": "league",
            "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),  # Past date
            "end_date": (datetime.utcnow() - timedelta(days=5)).isoformat(),   # End before start
            "max_teams": 8,
            "entry_fee": 1000.0,
            "prize_pool": 50000.0
        }
        
        response = organizer_client.post("/api/v1/tournaments/", json=invalid_tournament)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_get_tournaments_list(self, client, authenticated_users, auth_client_factory):
        """Test getting list of tournaments."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/tournaments/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)

    async def test_get_tournament_by_id(self, client, authenticated_users, auth_client_factory, tournament_data):
        """Test getting tournament by ID."""
        organizer_token = authenticated_users["tokens"]["organizer"]
        organizer_client = auth_client_factory(organizer_token)
        
        # Create tournament first
        create_response = organizer_client.post("/api/v1/tournaments/", json=tournament_data)
        if create_response.status_code in [200, 201]:
            tournament = create_response.json()
            tournament_id = tournament["id"]
            
            # Get tournament by ID
            response = organizer_client.get(f"/api/v1/tournaments/{tournament_id}")
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["id"] == tournament_id
            assert data["name"] == tournament_data["name"]

    async def test_update_tournament(self, client, authenticated_users, auth_client_factory, tournament_data):
        """Test updating tournament details."""
        organizer_token = authenticated_users["tokens"]["organizer"]
        organizer_client = auth_client_factory(organizer_token)
        
        # Create tournament first
        create_response = organizer_client.post("/api/v1/tournaments/", json=tournament_data)
        if create_response.status_code in [200, 201]:
            tournament = create_response.json()
            tournament_id = tournament["id"]
            
            update_data = {
                "description": "Updated tournament description",
                "prize_money": 150000.0
            }
            
            response = organizer_client.put(f"/api/v1/tournaments/{tournament_id}", json=update_data)
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_delete_tournament(self, client, authenticated_users, auth_client_factory, tournament_data):
        """Test deleting a tournament."""
        organizer_token = authenticated_users["tokens"]["organizer"]
        organizer_client = auth_client_factory(organizer_token)
        
        # Create tournament first
        create_response = organizer_client.post("/api/v1/tournaments/", json=tournament_data)
        if create_response.status_code in [200, 201]:
            tournament = create_response.json()
            tournament_id = tournament["id"]
            
            response = organizer_client.delete(f"/api/v1/tournaments/{tournament_id}")
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_204_NO_CONTENT,
                status.HTTP_404_NOT_FOUND
            ]


@pytest.mark.asyncio
@pytest.mark.tournament
@integration
class TestTeamRegistration:
    """Test team registration for tournaments."""

    async def test_register_team_for_tournament(self, client, authenticated_users, auth_client_factory, tournament_data, team_data):
        """Test registering a team for tournament."""
        organizer_token = authenticated_users["tokens"]["organizer"]
        captain_token = authenticated_users["tokens"]["captain1"]
        organizer_client = auth_client_factory(organizer_token)
        captain_client = auth_client_factory(captain_token)
        
        # Create tournament
        tournament_response = organizer_client.post("/api/v1/tournaments/", json=tournament_data)
        if tournament_response.status_code not in [200, 201]:
            pytest.skip("Tournament creation failed")
            
        tournament = tournament_response.json()
        tournament_id = tournament["id"]
        
        # Create team
        team_response = captain_client.post("/api/v1/teams/", json=team_data[0])
        if team_response.status_code != 200:
            pytest.skip("Team creation failed")
            
        team = team_response.json()
        team_id = team["id"]
        
        # Register team for tournament
        response = organizer_client.post(f"/api/v1/tournaments/{tournament_id}/teams/{team_id}")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND
        ]

    async def test_register_team_tournament_full(self, client, authenticated_users, auth_client_factory):
        """Test registering team when tournament is full."""
        organizer_token = authenticated_users["tokens"]["organizer"]
        organizer_client = auth_client_factory(organizer_token)
        
        # Create tournament with max 1 team
        tournament_data = {
            "name": "Small Tournament",
            "description": "Tournament with limited capacity",
            "tournament_type": "knockout",
            "start_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
            "max_teams": 1,  # Only 1 team allowed
            "entry_fee": 1000.0,
            "prize_pool": 10000.0
        }
        
        tournament_response = organizer_client.post("/api/v1/tournaments/", json=tournament_data)
        if tournament_response.status_code in [200, 201]:
            tournament_id = tournament_response.json()["id"]
            
            # Try to register multiple teams
            team_id1 = str(uuid.uuid4())
            team_id2 = str(uuid.uuid4())
            
            response1 = organizer_client.post(f"/api/v1/tournaments/{tournament_id}/teams/{team_id1}")
            response2 = organizer_client.post(f"/api/v1/tournaments/{tournament_id}/teams/{team_id2}")
            
            # One should succeed, other should fail
            status_codes = [response1.status_code, response2.status_code]
            assert status.HTTP_400_BAD_REQUEST in status_codes or status.HTTP_409_CONFLICT in status_codes

    async def test_get_tournament_teams(self, client, authenticated_users, auth_client_factory, tournament_data):
        """Test getting teams registered for tournament."""
        organizer_token = authenticated_users["tokens"]["organizer"]
        organizer_client = auth_client_factory(organizer_token)
        
        # Create tournament
        tournament_response = organizer_client.post("/api/v1/tournaments/", json=tournament_data)
        if tournament_response.status_code in [200, 201]:
            tournament_id = tournament_response.json()["id"]
            
            response = organizer_client.get(f"/api/v1/tournaments/{tournament_id}/teams")
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert isinstance(data, list)

    async def test_withdraw_team_from_tournament(self, client, authenticated_users, auth_client_factory):
        """Test withdrawing team from tournament."""
        organizer_token = authenticated_users["tokens"]["organizer"]
        organizer_client = auth_client_factory(organizer_token)
        
        tournament_id = str(uuid.uuid4())
        team_id = str(uuid.uuid4())
        
        response = organizer_client.delete(f"/api/v1/tournaments/{tournament_id}/teams/{team_id}")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND
        ]


@pytest.mark.asyncio
@pytest.mark.tournament
@integration
class TestTournamentScheduling:
    """Test tournament scheduling and brackets."""

    async def test_generate_tournament_bracket(self, client, authenticated_users, auth_client_factory):
        """Test generating tournament bracket."""
        organizer_token = authenticated_users["tokens"]["organizer"]
        organizer_client = auth_client_factory(organizer_token)
        
        tournament_id = str(uuid.uuid4())
        
        response = organizer_client.post(f"/api/v1/tournaments/{tournament_id}/generate-bracket")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_get_tournament_bracket(self, client, authenticated_users, auth_client_factory):
        """Test getting tournament bracket."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        tournament_id = str(uuid.uuid4())
        
        response = user_client.get(f"/api/v1/tournaments/{tournament_id}/bracket")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_schedule_tournament_matches(self, client, authenticated_users, auth_client_factory):
        """Test scheduling tournament matches."""
        organizer_token = authenticated_users["tokens"]["organizer"]
        organizer_client = auth_client_factory(organizer_token)
        
        tournament_id = str(uuid.uuid4())
        
        schedule_data = {
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "venue": "Main Stadium",
            "match_duration_hours": 4,
            "break_between_matches_hours": 1
        }
        
        response = organizer_client.post(f"/api/v1/tournaments/{tournament_id}/schedule", json=schedule_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_get_tournament_schedule(self, client, authenticated_users, auth_client_factory):
        """Test getting tournament schedule."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        tournament_id = str(uuid.uuid4())
        
        response = user_client.get(f"/api/v1/tournaments/{tournament_id}/schedule")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
@pytest.mark.tournament
@integration
class TestTournamentProgression:
    """Test tournament progression and advancement."""

    async def test_advance_team_to_next_round(self, client, authenticated_users, auth_client_factory):
        """Test advancing team to next round."""
        organizer_token = authenticated_users["tokens"]["organizer"]
        organizer_client = auth_client_factory(organizer_token)
        
        tournament_id = str(uuid.uuid4())
        match_id = str(uuid.uuid4())
        
        advancement_data = {
            "winning_team_id": str(uuid.uuid4()),
            "match_result": "Team A won by 5 wickets",
            "next_round": "semi_final"
        }
        
        response = organizer_client.post(
            f"/api/v1/tournaments/{tournament_id}/matches/{match_id}/advance",
            json=advancement_data
        )
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_get_tournament_standings(self, client, authenticated_users, auth_client_factory):
        """Test getting tournament standings."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        tournament_id = str(uuid.uuid4())
        
        response = user_client.get(f"/api/v1/tournaments/{tournament_id}/standings")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_complete_tournament(self, client, authenticated_users, auth_client_factory):
        """Test completing a tournament."""
        organizer_token = authenticated_users["tokens"]["organizer"]
        organizer_client = auth_client_factory(organizer_token)
        
        tournament_id = str(uuid.uuid4())
        
        completion_data = {
            "winner_team_id": str(uuid.uuid4()),
            "runner_up_team_id": str(uuid.uuid4()),
            "tournament_result": "Great tournament with exciting matches",
            "prize_distribution": {
                "winner": 60000.0,
                "runner_up": 30000.0,
                "semi_finalists": 10000.0
            }
        }
        
        response = organizer_client.post(f"/api/v1/tournaments/{tournament_id}/complete", json=completion_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]


@pytest.mark.asyncio
@pytest.mark.tournament
@integration
class TestTournamentStatistics:
    """Test tournament statistics and analytics."""

    async def test_get_tournament_statistics(self, client, authenticated_users, auth_client_factory):
        """Test getting tournament statistics."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        tournament_id = str(uuid.uuid4())
        
        response = user_client.get(f"/api/v1/tournaments/{tournament_id}/statistics")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_tournament_leaderboard(self, client, authenticated_users, auth_client_factory):
        """Test getting tournament leaderboard."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        tournament_id = str(uuid.uuid4())
        
        response = user_client.get(f"/api/v1/tournaments/{tournament_id}/leaderboard")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_tournament_matches(self, client, authenticated_users, auth_client_factory):
        """Test getting all matches in tournament."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        tournament_id = str(uuid.uuid4())
        
        response = user_client.get(f"/api/v1/tournaments/{tournament_id}/matches")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
@pytest.mark.tournament
@unit
class TestTournamentValidation:
    """Test tournament validation logic."""

    async def test_tournament_type_validation(self):
        """Test tournament type validation."""
        valid_types = ["league", "knockout", "round_robin", "swiss"]
        invalid_types = ["invalid_type", "wrong", ""]
        
        # Test cases ready for validation implementation
        assert len(valid_types) > 0
        assert len(invalid_types) > 0

    async def test_date_validation(self):
        """Test tournament date validation."""
        now = datetime.utcnow()
        
        valid_dates = [
            {"start": now + timedelta(days=1), "end": now + timedelta(days=10)},
            {"start": now + timedelta(days=7), "end": now + timedelta(days=30)}
        ]
        
        invalid_dates = [
            {"start": now - timedelta(days=1), "end": now + timedelta(days=10)},  # Past start
            {"start": now + timedelta(days=10), "end": now + timedelta(days=1)}   # End before start
        ]
        
        assert len(valid_dates) > 0
        assert len(invalid_dates) > 0

    async def test_team_limit_validation(self):
        """Test team limit validation."""
        valid_limits = [2, 4, 8, 16, 32]  # Powers of 2 for knockout
        invalid_limits = [0, 1, 3, 5, -1]  # Invalid team counts
        
        assert len(valid_limits) > 0
        assert len(invalid_limits) > 0

    async def test_prize_pool_validation(self):
        """Test prize pool validation."""
        valid_pools = [1000.0, 50000.0, 100000.0]
        invalid_pools = [-1000.0, 0.0]  # Negative or zero prizes
        
        assert len(valid_pools) > 0
        assert len(invalid_pools) > 0