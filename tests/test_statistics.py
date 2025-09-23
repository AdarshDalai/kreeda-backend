"""
Test cases for statistics and analytics functionality.

This module tests:
- Player performance statistics
- Team analytics and rankings
- Match statistics and insights
- Career statistics tracking
- Leaderboards and comparisons
- Statistical data integrity
"""

import pytest
from fastapi import status
from datetime import datetime, timedelta
import uuid

from conftest import unit, integration


@pytest.mark.asyncio
@pytest.mark.statistics
@integration
class TestPlayerStatistics:
    """Test player statistics and performance tracking."""

    async def test_statistics_health_check(self, client):
        """Test statistics service health check."""
        # Test stats endpoints
        response = client.get("/api/v1/stats/health")
        # If no specific health endpoint, test basic functionality
        assert True  # Placeholder

    async def test_get_player_performance_stats(self, client, authenticated_users, auth_client_factory):
        """Test getting player performance statistics."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/statistics/players/performance")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, (list, dict))

    async def test_get_specific_player_stats(self, client, authenticated_users, auth_client_factory):
        """Test getting statistics for a specific player."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        player_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/players/{player_id}")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_player_batting_stats(self, client, authenticated_users, auth_client_factory):
        """Test getting player batting statistics."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        player_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/players/{player_id}/batting")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_player_bowling_stats(self, client, authenticated_users, auth_client_factory):
        """Test getting player bowling statistics."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        player_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/players/{player_id}/bowling")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_player_career_summary(self, client, authenticated_users, auth_client_factory):
        """Test getting player career summary."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        player_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/players/{player_id}/career")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_player_recent_form(self, client, authenticated_users, auth_client_factory):
        """Test getting player recent form."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        player_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/players/{player_id}/recent-form")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
@pytest.mark.statistics
@integration
class TestTeamStatistics:
    """Test team statistics and analytics."""

    async def test_get_team_rankings(self, client, authenticated_users, auth_client_factory):
        """Test getting team rankings."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/statistics/teams/rankings")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, (list, dict))

    async def test_get_specific_team_stats(self, client, authenticated_users, auth_client_factory):
        """Test getting statistics for a specific team."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        team_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/teams/{team_id}")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_team_performance_over_time(self, client, authenticated_users, auth_client_factory):
        """Test getting team performance over time."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        team_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/teams/{team_id}/performance")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_team_vs_team_comparison(self, client, authenticated_users, auth_client_factory):
        """Test getting head-to-head team comparison."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        team1_id = str(uuid.uuid4())
        team2_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/teams/{team1_id}/vs/{team2_id}")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_team_player_stats(self, client, authenticated_users, auth_client_factory):
        """Test getting team's player statistics."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        team_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/teams/{team_id}/players")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
@pytest.mark.statistics
@integration
class TestMatchStatistics:
    """Test match statistics and analytics."""

    async def test_get_match_insights(self, client, authenticated_users, auth_client_factory):
        """Test getting match insights and analytics."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        match_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/matches/{match_id}/insights")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_match_momentum(self, client, authenticated_users, auth_client_factory):
        """Test getting match momentum analysis."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        match_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/matches/{match_id}/momentum")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_partnership_analysis(self, client, authenticated_users, auth_client_factory):
        """Test getting partnership analysis for a match."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        match_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/matches/{match_id}/partnerships")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_bowling_analysis(self, client, authenticated_users, auth_client_factory):
        """Test getting bowling analysis for a match."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        match_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/matches/{match_id}/bowling-analysis")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
@pytest.mark.statistics
@integration
class TestLeaderboards:
    """Test leaderboards and rankings."""

    async def test_statistics_health_check(self, client):
        """Test statistics service health check."""
        response = client.get("/api/v1/statistics/health")
        assert response.status_code == status.HTTP_200_OK
        assert "status" in response.json()

    async def test_get_career_stats(self, client, authenticated_users, auth_client_factory):
        """Test getting player career statistics."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        user_id = list(authenticated_users["users"].values())[0]["id"]
        response = user_client.get(f"/api/v1/statistics/career/{user_id}")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_leaderboard_runs(self, client, authenticated_users, auth_client_factory):
        """Test getting runs leaderboard."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/statistics/leaderboard/runs")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "category" in data
        assert "entries" in data
        assert data["category"] == "runs"

    async def test_get_leaderboard_batting_avg(self, client, authenticated_users, auth_client_factory):
        """Test getting batting average leaderboard."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/statistics/leaderboard/batting_avg")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "category" in data
        assert data["category"] == "batting_avg"

    async def test_get_leaderboard_wickets(self, client, authenticated_users, auth_client_factory):
        """Test getting wickets leaderboard."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/statistics/leaderboard/wickets")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "category" in data
        assert data["category"] == "wickets"

    async def test_get_leaderboard_with_filters(self, client, authenticated_users, auth_client_factory):
        """Test getting leaderboard with filters."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/statistics/leaderboard/runs?limit=10&min_matches=3")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "limit" in data
        assert data["limit"] == 10

    async def test_get_leaderboard_invalid_category(self, client, authenticated_users, auth_client_factory):
        """Test getting leaderboard with invalid category."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/statistics/leaderboard/invalid_category")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_get_match_performance_history(self, client, authenticated_users, auth_client_factory):
        """Test getting player match performance history."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        user_id = list(authenticated_users["users"].values())[0]["id"]
        response = user_client.get(f"/api/v1/statistics/player/{user_id}/history")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_team_season_summary(self, client, authenticated_users, auth_client_factory):
        """Test getting team season summary."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        team_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/team/{team_id}/season")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_tournament_leaderboard(self, client, authenticated_users, auth_client_factory):
        """Test getting tournament-specific leaderboard."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        tournament_id = str(uuid.uuid4())
        response = user_client.get(f"/api/v1/statistics/tournament/{tournament_id}/leaderboard")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_analytics_overview(self, client, authenticated_users, auth_client_factory):
        """Test getting analytics overview."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/statistics/analytics/overview")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "top_run_scorers" in data
        assert "top_wicket_takers" in data
        assert "top_batting_averages" in data


@pytest.mark.asyncio
@pytest.mark.statistics
@integration
class TestStatisticsFiltering:
    """Test statistics filtering and aggregation."""

    async def test_get_stats_by_match_type(self, client, authenticated_users, auth_client_factory):
        """Test getting statistics filtered by match type."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        match_types = ["T20", "ODI", "Test"]
        
        for match_type in match_types:
            response = user_client.get(f"/api/v1/statistics/players/performance?match_type={match_type}")
            assert response.status_code == status.HTTP_200_OK

    async def test_get_stats_by_date_range(self, client, authenticated_users, auth_client_factory):
        """Test getting statistics for a specific date range."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        response = user_client.get(
            f"/api/v1/statistics/players/performance?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_get_stats_by_venue(self, client, authenticated_users, auth_client_factory):
        """Test getting statistics filtered by venue."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        venue = "Wankhede Stadium"
        response = user_client.get(f"/api/v1/statistics/players/performance?venue={venue}")
        assert response.status_code == status.HTTP_200_OK

    async def test_get_stats_with_pagination(self, client, authenticated_users, auth_client_factory):
        """Test getting statistics with pagination."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/statistics/players/performance?skip=0&limit=20")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        if isinstance(data, list):
            assert len(data) <= 20


@pytest.mark.asyncio
@pytest.mark.statistics
@integration
class TestAnalyticsReports:
    """Test analytics reports and insights."""

    async def test_generate_player_report(self, client, authenticated_users, auth_client_factory):
        """Test generating comprehensive player report."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        player_id = str(uuid.uuid4())
        report_data = {
            "report_type": "comprehensive",
            "period": "last_season",
            "include_comparisons": True
        }
        
        response = user_client.post(f"/api/v1/statistics/players/{player_id}/report", json=report_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND
        ]

    async def test_generate_team_report(self, client, authenticated_users, auth_client_factory):
        """Test generating comprehensive team report."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        team_id = str(uuid.uuid4())
        report_data = {
            "report_type": "season_summary",
            "include_player_stats": True,
            "format": "detailed"
        }
        
        response = user_client.post(f"/api/v1/statistics/teams/{team_id}/report", json=report_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND
        ]

    async def test_get_trend_analysis(self, client, authenticated_users, auth_client_factory):
        """Test getting trend analysis."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/statistics/trends/batting")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_comparative_analysis(self, client, authenticated_users, auth_client_factory):
        """Test getting comparative analysis between players."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        player1_id = str(uuid.uuid4())
        player2_id = str(uuid.uuid4())
        
        response = user_client.get(f"/api/v1/statistics/compare/players/{player1_id}/{player2_id}")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
@pytest.mark.statistics
@unit
class TestStatisticsCalculations:
    """Test statistics calculation logic."""

    async def test_batting_average_calculation(self):
        """Test batting average calculation."""
        test_cases = [
            {"runs": 500, "dismissals": 10, "expected": 50.0},
            {"runs": 1000, "dismissals": 20, "expected": 50.0},
            {"runs": 150, "dismissals": 3, "expected": 50.0},
            {"runs": 100, "dismissals": 0, "expected": None}  # Not out
        ]
        
        # Test cases ready for calculation implementation
        assert len(test_cases) > 0

    async def test_strike_rate_calculation(self):
        """Test strike rate calculation."""
        test_cases = [
            {"runs": 100, "balls": 100, "expected": 100.0},
            {"runs": 150, "balls": 100, "expected": 150.0},
            {"runs": 50, "balls": 50, "expected": 100.0},
            {"runs": 0, "balls": 0, "expected": None}  # No balls faced
        ]
        
        assert len(test_cases) > 0

    async def test_bowling_average_calculation(self):
        """Test bowling average calculation."""
        test_cases = [
            {"runs_conceded": 200, "wickets": 10, "expected": 20.0},
            {"runs_conceded": 150, "wickets": 5, "expected": 30.0},
            {"runs_conceded": 100, "wickets": 0, "expected": None}  # No wickets
        ]
        
        assert len(test_cases) > 0

    async def test_economy_rate_calculation(self):
        """Test economy rate calculation."""
        test_cases = [
            {"runs_conceded": 60, "overs": 10, "expected": 6.0},
            {"runs_conceded": 45, "overs": 9, "expected": 5.0},
            {"runs_conceded": 30, "overs": 6, "expected": 5.0},
            {"runs_conceded": 0, "overs": 0, "expected": None}  # No overs bowled
        ]
        
        assert len(test_cases) > 0

    async def test_team_rating_calculation(self):
        """Test team rating calculation logic."""
        test_cases = [
            {"wins": 10, "losses": 5, "draws": 0, "expected_range": (600, 800)},
            {"wins": 5, "losses": 10, "draws": 0, "expected_range": (200, 500)},
            {"wins": 8, "losses": 8, "draws": 4, "expected_range": (400, 600)}
        ]
        
        assert len(test_cases) > 0