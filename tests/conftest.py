"""
Pytest configuration and shared fixtures for Kreeda backend tests.
"""

import asyncio
import os
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, List, Optional, Any
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["TESTING"] = "true"

# Import after setting environment
from app.main import app
from app.utils.database import Base, get_db

# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )

# Mock Supabase Authentication
class MockSupabaseAuth:
    """Mock Supabase authentication for testing."""
    
    def __init__(self):
        self.users = {}
        self.sessions = {}
        
    def sign_up_with_email_password(self, email: str, password: str, user_metadata: Optional[Dict[str, Any]] = None):
        """Mock sign up."""
        if user_metadata is None:
            user_metadata = {}
            
        user_id = f"mock_user_{len(self.users) + 1}"
        user = {
            "id": user_id,
            "email": email,
            "user_metadata": user_metadata,
            "created_at": datetime.utcnow().isoformat()
        }
        self.users[user_id] = user
        
        session = {
            "access_token": f"mock_token_{user_id}",
            "refresh_token": f"mock_refresh_{user_id}",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": user
        }
        self.sessions[user_id] = session
        
        return {
            "success": True,
            "user": user,
            "session": session
        }
    
    def sign_in_with_password(self, email: str, password: str):
        """Mock sign in."""
        # Find user by email
        for user_id, user in self.users.items():
            if user["email"] == email:
                session = self.sessions.get(user_id)
                if session:
                    return {
                        "success": True,
                        "user": user,
                        "session": session
                    }
        
        return {"success": False, "error": "Invalid credentials"}
    
    def get_user_from_token(self, token: str):
        """Mock get user from token."""
        for user_id, session in self.sessions.items():
            if session["access_token"] == token:
                return self.users[user_id]
        raise Exception("Invalid token")
    
    def refresh_session(self, refresh_token: str):
        """Mock refresh session."""
        for user_id, session in self.sessions.items():
            if session["refresh_token"] == refresh_token:
                # Generate new tokens
                new_session = {
                    "access_token": f"mock_token_{user_id}_new",
                    "refresh_token": f"mock_refresh_{user_id}_new",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "user": self.users[user_id]
                }
                self.sessions[user_id] = new_session
                return {"success": True, "session": new_session}
        
        return {"success": False, "error": "Invalid refresh token"}
    
    def sign_out(self, token: str):
        """Mock sign out."""
        for user_id, session in self.sessions.items():
            if session["access_token"] == token:
                del self.sessions[user_id]
                return {"success": True}
        return {"success": False, "error": "Invalid token"}


@pytest_asyncio.fixture
async def test_db():
    """Create a test database engine and session."""
    # Create test database engine
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with TestSessionLocal() as session:
        yield session
    
    # Clean up
    await test_engine.dispose()


@pytest.fixture
def mock_supabase_auth():
    """Provide mock Supabase authentication."""
    return MockSupabaseAuth()


@pytest.fixture
def client(test_db, mock_supabase_auth):
    """Create a test client with database dependency override."""
    # Import inside function to avoid circular imports
    from app.auth import supabase_auth
    from app.auth import middleware
    
    def override_get_db():
        return test_db
    
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Override Supabase auth functions with mocks
    original_sign_up = supabase_auth.sign_up_with_email_password
    original_sign_in = supabase_auth.sign_in_with_email_password
    original_refresh = supabase_auth.refresh_session
    original_sign_out = supabase_auth.sign_out
    original_get_user = supabase_auth.get_user_from_token
    original_middleware_get_user = middleware.get_user_from_token
    
    supabase_auth.sign_up_with_email_password = mock_supabase_auth.sign_up_with_email_password
    supabase_auth.sign_in_with_email_password = mock_supabase_auth.sign_in_with_password
    supabase_auth.refresh_session = mock_supabase_auth.refresh_session
    supabase_auth.sign_out = mock_supabase_auth.sign_out
    supabase_auth.get_user_from_token = mock_supabase_auth.get_user_from_token
    # CRITICAL: Also patch the imported function in middleware
    middleware.get_user_from_token = mock_supabase_auth.get_user_from_token
    
    try:
        # Create test client
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Restore original functions
        supabase_auth.sign_up_with_email_password = original_sign_up
        supabase_auth.sign_in_with_email_password = original_sign_in
        supabase_auth.refresh_session = original_refresh
        supabase_auth.sign_out = original_sign_out
        supabase_auth.get_user_from_token = original_get_user
        middleware.get_user_from_token = original_middleware_get_user
        
        # Clear dependency overrides
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(test_db, mock_supabase_auth):
    """Create an async test client with database dependency override."""
    # Import inside function to avoid circular imports
    from app.auth import supabase_auth
    
    async def override_get_db():
        return test_db
    
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Override Supabase auth functions with mocks
    original_sign_up = supabase_auth.sign_up_with_email_password
    original_sign_in = supabase_auth.sign_in_with_email_password
    original_refresh = supabase_auth.refresh_session
    original_sign_out = supabase_auth.sign_out
    original_get_user = supabase_auth.get_user_from_token
    
    supabase_auth.sign_up_with_email_password = mock_supabase_auth.sign_up_with_email_password
    supabase_auth.sign_in_with_email_password = mock_supabase_auth.sign_in_with_password
    supabase_auth.refresh_session = mock_supabase_auth.refresh_session
    supabase_auth.sign_out = mock_supabase_auth.sign_out
    supabase_auth.get_user_from_token = mock_supabase_auth.get_user_from_token
    
    try:
        # Create async test client
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            yield ac
    finally:
        # Restore original functions
        supabase_auth.sign_up_with_email_password = original_sign_up
        supabase_auth.sign_in_with_email_password = original_sign_in
        supabase_auth.refresh_session = original_refresh
        supabase_auth.sign_out = original_sign_out
        supabase_auth.get_user_from_token = original_get_user
        
        # Clear dependency overrides
        app.dependency_overrides.clear()


class AuthenticatedClient:
    """Helper class for authenticated requests."""
    
    def __init__(self, client: TestClient, token: str):
        self.client = client
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def get(self, url: str, **kwargs):
        kwargs.setdefault("headers", {}).update(self.headers)
        return self.client.get(url, **kwargs)
    
    def post(self, url: str, **kwargs):
        kwargs.setdefault("headers", {}).update(self.headers)
        return self.client.post(url, **kwargs)
    
    def put(self, url: str, **kwargs):
        kwargs.setdefault("headers", {}).update(self.headers)
        return self.client.put(url, **kwargs)
    
    def patch(self, url: str, **kwargs):
        kwargs.setdefault("headers", {}).update(self.headers)
        return self.client.patch(url, **kwargs)
    
    def delete(self, url: str, **kwargs):
        kwargs.setdefault("headers", {}).update(self.headers)
        return self.client.delete(url, **kwargs)


@pytest.fixture
def auth_client_factory(client):
    """Factory for creating authenticated clients."""
    def _create_authenticated_client(token: str) -> AuthenticatedClient:
        return AuthenticatedClient(client, token)
    return _create_authenticated_client


@pytest_asyncio.fixture
async def authenticated_users(mock_supabase_auth):
    """Create multiple authenticated users for testing."""
    users = {}
    tokens = {}
    
    # Create 24 test users for comprehensive testing
    user_data = [
        {"email": "organizer@test.com", "username": "organizer", "full_name": "Tournament Organizer"},
        {"email": "captain1@test.com", "username": "captain1", "full_name": "Captain One"},
        {"email": "captain2@test.com", "username": "captain2", "full_name": "Captain Two"},
        {"email": "captain3@test.com", "username": "captain3", "full_name": "Captain Three"},
        {"email": "player1@test.com", "username": "player1", "full_name": "Player One"},
        {"email": "player2@test.com", "username": "player2", "full_name": "Player Two"},
        {"email": "player3@test.com", "username": "player3", "full_name": "Player Three"},
        {"email": "player4@test.com", "username": "player4", "full_name": "Player Four"},
        {"email": "player5@test.com", "username": "player5", "full_name": "Player Five"},
        {"email": "player6@test.com", "username": "player6", "full_name": "Player Six"},
        {"email": "player7@test.com", "username": "player7", "full_name": "Player Seven"},
        {"email": "player8@test.com", "username": "player8", "full_name": "Player Eight"},
        {"email": "player9@test.com", "username": "player9", "full_name": "Player Nine"},
        {"email": "player10@test.com", "username": "player10", "full_name": "Player Ten"},
        {"email": "player11@test.com", "username": "player11", "full_name": "Player Eleven"},
        {"email": "player12@test.com", "username": "player12", "full_name": "Player Twelve"},
        {"email": "player13@test.com", "username": "player13", "full_name": "Player Thirteen"},
        {"email": "player14@test.com", "username": "player14", "full_name": "Player Fourteen"},
        {"email": "player15@test.com", "username": "player15", "full_name": "Player Fifteen"},
        {"email": "player16@test.com", "username": "player16", "full_name": "Player Sixteen"},
        {"email": "player17@test.com", "username": "player17", "full_name": "Player Seventeen"},
        {"email": "player18@test.com", "username": "player18", "full_name": "Player Eighteen"},
        {"email": "player19@test.com", "username": "player19", "full_name": "Player Nineteen"},
        {"email": "player20@test.com", "username": "player20", "full_name": "Player Twenty"},
        {"email": "player21@test.com", "username": "player21", "full_name": "Player Twenty One"},
        {"email": "player22@test.com", "username": "player22", "full_name": "Player Twenty Two"},
    ]
    
    for data in user_data:
        result = mock_supabase_auth.sign_up_with_email_password(
            data["email"], "password123", user_metadata=data
        )
        users[data["username"]] = result["user"]
        tokens[data["username"]] = result["session"]["access_token"]
    
    return {"users": users, "tokens": tokens}


@pytest.fixture
def team_data(authenticated_users):
    """Provide test data for team creation."""
    import uuid
    # Extract user IDs from authenticated_users for captain_id
    users = authenticated_users["users"]
    captain1_id = str(uuid.UUID(int=hash(users["captain1"]["id"]) % (2**128)))
    captain2_id = str(uuid.UUID(int=hash(users["captain2"]["id"]) % (2**128)))
    captain3_id = str(uuid.UUID(int=hash(users["captain3"]["id"]) % (2**128)))
    
    return [
        {
            "name": "Mumbai Warriors",
            "short_name": "MW",
            "logo_url": None,
            "captain_id": captain1_id
        },
        {
            "name": "Delhi Dynamos", 
            "short_name": "DD",
            "logo_url": None,
            "captain_id": captain2_id
        },
        {
            "name": "Chennai Champions",
            "short_name": "CC",
            "logo_url": None,
            "captain_id": captain3_id
        }
    ]


@pytest.fixture
def tournament_data():
    """Provide test data for tournament creation."""
    from decimal import Decimal
    return {
        "name": "Cricket Champions League",
        "description": "Annual cricket tournament featuring the best teams",
        "tournament_type": "knockout",
        "start_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=37)).isoformat(),
        "registration_deadline": (datetime.utcnow() + timedelta(days=20)).isoformat(),
        "max_teams": 16,
        "min_teams": 8,
        "entry_fee": "5000.00",
        "prize_money": "100000.00",
        "overs_per_innings": 20,
        "venue_details": "Cricket Stadium, Mumbai",
        "organizer_contact": "organizer@cricket.com",
        "is_public": True
    }


# Performance monitoring for tests
class PerformanceMonitor:
    """Performance monitoring utility for tests."""
    
    def __init__(self):
        self.timers = {}
        self.durations = {}
    
    def start_timer(self, name: str):
        """Start a timer with the given name."""
        self.timers[name] = datetime.utcnow()
    
    def end_timer(self, name: str):
        """End a timer and calculate duration."""
        if name in self.timers:
            start_time = self.timers[name]
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            self.durations[name] = duration
            del self.timers[name]
            return duration
        return None
    
    def get_duration(self, name: str) -> Optional[float]:
        """Get the duration for a completed timer."""
        return self.durations.get(name)
    
    def get_all_durations(self) -> Dict[str, float]:
        """Get all recorded durations."""
        return self.durations.copy()
    
    def reset(self):
        """Reset all timers and durations."""
        self.timers.clear()
        self.durations.clear()


@pytest.fixture
def performance_monitor():
    """Provide a performance monitor for tests."""
    monitor = PerformanceMonitor()
    yield monitor
    # Optionally log performance results after test
    durations = monitor.get_all_durations()
    if durations:
        print(f"\nPerformance Results: {durations}")


@pytest_asyncio.fixture
async def db_session():
    """Alias for test_db fixture to match integration test expectations."""
    # Create test database engine
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with TestSessionLocal() as session:
        yield session
    
    # Clean up
    await test_engine.dispose()


# Pytest markers for easy test organization
unit = pytest.mark.unit
integration = pytest.mark.integration
e2e = pytest.mark.e2e
performance = pytest.mark.performance
slow = pytest.mark.slow