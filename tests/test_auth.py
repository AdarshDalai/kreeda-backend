import pytest
from httpx import AsyncClient

@pytest.mark.unit
class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient, test_user_data):
        """Test successful user registration"""
        response = await client.post("/auth/register", json=test_user_data)
        assert response.status_code == 200
        data = response.json()
        assert "session" in data
        assert "user" in data
        assert data["user"]["email"] == test_user_data["email"]
        assert "access_token" in data["session"]
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user_data):
        """Test registration with duplicate email"""
        # Register first user
        await client.post("/auth/register", json=test_user_data)
        
        # Try to register same email again
        response = await client.post("/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient, weak_password_data):
        """Test registration with weak password"""
        response = await client.post("/auth/register", json=weak_password_data)
        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user_data):
        """Test successful login"""
        # Register user first
        await client.post("/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["session"]
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient, test_user_data):
        """Test login with invalid credentials"""
        response = await client.post("/auth/login", json={
            "email": test_user_data["email"],
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_user(self, client: AsyncClient, test_user_data):
        """Test get current user"""
        # Register and login
        reg_response = await client.post("/auth/register", json=test_user_data)
        token = reg_response.json()["session"]["access_token"]
        
        # Get user
        response = await client.get(
            "/auth/user",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == test_user_data["email"]
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, test_user_data):
        """Test token refresh"""
        # Register user
        reg_response = await client.post("/auth/register", json=test_user_data)
        refresh_token = reg_response.json()["session"]["refresh_token"]
        
        # Refresh token
        response = await client.post("/auth/token", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        assert "access_token" in response.json()["session"]
    
    @pytest.mark.asyncio
    async def test_anonymous_user_creation(self, client: AsyncClient):
        """Test anonymous user creation"""
        response = await client.post("/auth/signin/anonymous", json={
            "options": {"data": {"anonymous": True}}
        })
        assert response.status_code == 200
        data = response.json()
        assert "anonymous" in data["user"]["email"]
