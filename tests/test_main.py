"""
Comprehensive test suite for Kreeda backend
Tests API endpoints, validation, error handling, and business logic
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.cricket import User

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
    },
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database tables"""
    Base.metadata.create_all(bind=engine)
    
    # Create test user
    db = TestingSessionLocal()
    try:
        test_user = User(
            id=1,
            username="testuser",
            email="test@kreeda.com", 
            full_name="Test User",
            hashed_password="dummy_hash"
        )
        db.add(test_user)
        db.commit()
    finally:
        db.close()
    
    yield
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    def test_health_check(self):
        """Test the main health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "Kreeda" in data["app"]
        assert "version" in data
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Kreeda" in data["message"]
        assert "version" in data
    
    def test_cricket_health(self):
        """Test cricket API health check"""
        response = client.get("/api/cricket/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "cricket-api"


class TestTeamManagement:
    """Test team creation and management"""
    
    def test_create_team_success(self):
        """Test successful team creation"""
        team_data = {
            "name": "Mumbai Indians",
            "short_name": "MI",
            "city": "Mumbai"
        }
        response = client.post("/api/cricket/teams", json=team_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Mumbai Indians"
        assert data["short_name"] == "MI"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_team_validation_error(self):
        """Test team creation with invalid data"""
        # Test missing required fields
        response = client.post("/api/cricket/teams", json={})
        assert response.status_code == 422
        
        # Test invalid field types
        team_data = {
            "name": 123,  # Should be string
            "short_name": "MI"
        }
        response = client.post("/api/cricket/teams", json=team_data)
        assert response.status_code == 422
    
    def test_get_team(self):
        """Test retrieving a team"""
        # First create a team
        team_data = {"name": "Chennai Super Kings", "short_name": "CSK"}
        create_response = client.post("/api/cricket/teams", json=team_data)
        team_id = create_response.json()["id"]
        
        # Get the team
        response = client.get(f"/api/cricket/teams/{team_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Chennai Super Kings"
        assert data["short_name"] == "CSK"
    
    def test_get_team_not_found(self):
        """Test getting non-existent team"""
        response = client.get("/api/cricket/teams/99999")
        assert response.status_code == 404
    
    def test_list_teams(self):
        """Test listing all teams"""
        response = client.get("/api/cricket/teams")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestPlayerManagement:
    """Test player creation and management"""
    
    def test_add_player_success(self):
        """Test successful player addition"""
        # First create a team
        team_data = {"name": "Royal Challengers", "short_name": "RCB"}
        team_response = client.post("/api/cricket/teams", json=team_data)
        team_id = team_response.json()["id"]
        
        # Add player to team
        player_data = {
            "name": "Virat Kohli",
            "jersey_number": 18,
            "position": "Batsman"
        }
        response = client.post(f"/api/cricket/teams/{team_id}/players", json=player_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Virat Kohli"
        assert data["jersey_number"] == 18
        assert data["team_id"] == team_id
    
    def test_add_player_invalid_team(self):
        """Test adding player to non-existent team"""
        player_data = {
            "name": "Test Player",
            "jersey_number": 10
        }
        response = client.post("/api/cricket/teams/99999/players", json=player_data)
        assert response.status_code == 404


class TestMatchManagement:
    """Test match creation and management"""
    
    def test_create_match_success(self):
        """Test successful match creation"""
        # Create two teams first
        team1_data = {"name": "Team A", "short_name": "TA"}
        team2_data = {"name": "Team B", "short_name": "TB"}
        
        team1_response = client.post("/api/cricket/teams", json=team1_data)
        team2_response = client.post("/api/cricket/teams", json=team2_data)
        
        team1_id = team1_response.json()["id"]
        team2_id = team2_response.json()["id"]
        
        # Create match
        match_data = {
            "team_a_id": team1_id,
            "team_b_id": team2_id,
            "overs_per_side": 20,
            "venue": "Test Stadium"
        }
        response = client.post("/api/cricket/matches", json=match_data)
        assert response.status_code == 200
        data = response.json()
        assert data["team_a_id"] == team1_id
        assert data["team_b_id"] == team2_id
        assert data["overs_per_side"] == 20
        assert data["status"] == "not_started"
    
    def test_create_match_same_teams(self):
        """Test match creation with same teams (should fail)"""
        # Create one team
        team_data = {"name": "Same Team", "short_name": "ST"}
        team_response = client.post("/api/cricket/teams", json=team_data)
        team_id = team_response.json()["id"]
        
        # Try to create match with same team
        match_data = {
            "team_a_id": team_id,
            "team_b_id": team_id,  # Same team
            "overs_per_side": 20
        }
        response = client.post("/api/cricket/matches", json=match_data)
        assert response.status_code == 422  # Validation error


class TestSecurityAndValidation:
    """Test security headers and input validation"""
    
    def test_security_headers(self):
        """Test that security headers are present"""
        response = client.get("/health")
        headers = response.headers
        
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
        assert "X-XSS-Protection" in headers
    
    def test_request_id_header(self):
        """Test that request ID is added to responses"""
        response = client.get("/health")
        assert "X-Request-ID" in response.headers
    
    def test_cors_headers(self):
        """Test CORS configuration"""
        response = client.options("/api/cricket/teams")
        assert response.status_code in [200, 204]  # OPTIONS should be allowed


if __name__ == "__main__":
    pytest.main([__file__])
