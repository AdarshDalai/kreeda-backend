import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestAuthFlow:
    """Integration tests for complete authentication flow"""
    
    @pytest.mark.asyncio
    async def test_complete_user_journey(self, client: AsyncClient):
        """Test complete user registration to profile update journey"""
        # 1. Register
        register_data = {
            "email": "journey@example.com",
            "password": "Journey123!",
            "phone_number": "+1234567890"
        }
        reg_response = await client.post("/auth/register", json=register_data)
        assert reg_response.status_code == 200
        token = reg_response.json()["session"]["access_token"]
        refresh_token = reg_response.json()["session"]["refresh_token"]
        
        # 2. Get user info
        user_response = await client.get(
            "/auth/user",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert user_response.status_code == 200
        user_id = user_response.json()["id"]
        
        # 3. Update profile
        profile_data = {
            "name": "Journey User",
            "bio": "Integration test user",
            "location": "Test City"
        }
        profile_response = await client.put(
            "/user/profile/",
            json=profile_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert profile_response.status_code == 200
        assert profile_response.json()["name"] == "Journey User"
        
        # 4. Refresh token
        refresh_response = await client.post("/auth/token", json={
            "refresh_token": refresh_token
        })
        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["session"]["access_token"]
        
        # 5. Logout
        logout_response = await client.post(
            "/auth/signout",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert logout_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_password_update_flow(self, client: AsyncClient):
        """Test password update flow"""
        # Register
        user_data = {
            "email": "passupdate@example.com",
            "password": "OldPass123!"
        }
        reg_response = await client.post("/auth/register", json=user_data)
        token = reg_response.json()["session"]["access_token"]
        
        # Update password
        update_response = await client.put(
            "/auth/user",
            json={"password": "NewPass456!"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert update_response.status_code == 200
        
        # Login with new password
        login_response = await client.post("/auth/login", json={
            "email": user_data["email"],
            "password": "NewPass456!"
        })
        assert login_response.status_code == 200
        
        # Old password should fail
        old_login_response = await client.post("/auth/login", json={
            "email": user_data["email"],
            "password": "OldPass123!"
        })
        assert old_login_response.status_code == 401
