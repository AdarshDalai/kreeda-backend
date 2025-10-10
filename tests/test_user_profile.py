import pytest
from httpx import AsyncClient

@pytest.mark.unit
class TestUserProfile:
    """Test user profile endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_profile(self, client: AsyncClient, test_user_data):
        """Test profile creation"""
        # Register user
        reg_response = await client.post("/auth/register", json=test_user_data)
        token = reg_response.json()["session"]["access_token"]
        
        # Create profile
        profile_data = {
            "name": "Test User",
            "bio": "Test bio",
            "location": "Test City",
            "preferences": {"theme": "dark"},
            "roles": {"player": True}
        }
        response = await client.post(
            "/user/profile/",
            json=profile_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_get_profile(self, client: AsyncClient, test_user_data):
        """Test get profile"""
        # Register user
        reg_response = await client.post("/auth/register", json=test_user_data)
        token = reg_response.json()["session"]["access_token"]
        
        # Get profile
        response = await client.get(
            "/user/profile/",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Profile auto-created on registration
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_update_profile(self, client: AsyncClient, test_user_data):
        """Test profile update"""
        # Register user
        reg_response = await client.post("/auth/register", json=test_user_data)
        token = reg_response.json()["session"]["access_token"]
        
        # Update profile
        update_data = {"name": "Updated Name", "bio": "Updated bio"}
        response = await client.put(
            "/user/profile/",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
