"""
Test Authentication Endpoints

Basic tests for authentication functionality
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_endpoint(client: AsyncClient, sample_user_data):
    """Test login endpoint"""
    login_data = {
        "email": sample_user_data["email"],
        "password": sample_user_data["password"]
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_endpoint(client: AsyncClient, sample_user_data):
    """Test registration endpoint"""
    response = await client.post("/api/v1/auth/register", json=sample_user_data)
    
    assert response.status_code == 201
    data = response.json()
    
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_current_user_endpoint(client: AsyncClient):
    """Test current user endpoint"""
    response = await client.get("/api/v1/auth/me")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "id" in data
    assert "email" in data
    assert "full_name" in data


@pytest.mark.asyncio
async def test_logout_endpoint(client: AsyncClient):
    """Test logout endpoint"""
    response = await client.post("/api/v1/auth/logout")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data