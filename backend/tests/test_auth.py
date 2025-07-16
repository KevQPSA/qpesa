"""
Authentication endpoint tests
Tests user registration, login, and JWT token handling
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

@pytest.mark.asyncio
async def test_user_registration_success(client: AsyncClient):
    """Test successful user registration"""
    user_data = {
        "email": "test@example.com",
        "phone": "+254712345678",
        "password": "TestPassword123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    response = await client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["email"] == user_data["email"]
    assert data["kyc_status"] == "pending"

@pytest.mark.asyncio
async def test_user_registration_invalid_phone(client: AsyncClient):
    """Test user registration with invalid phone number"""
    user_data = {
        "email": "test@example.com",
        "phone": "123456789",  # Invalid Kenyan phone
        "password": "TestPassword123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    response = await client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_user_registration_weak_password(client: AsyncClient):
    """Test user registration with weak password"""
    user_data = {
        "email": "test@example.com",
        "phone": "+254712345678",
        "password": "weak",  # Weak password
        "first_name": "John",
        "last_name": "Doe"
    }
    
    response = await client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_user_login_success(client: AsyncClient, db_session: AsyncSession):
    """Test successful user login"""
    # First register a user
    user_data = {
        "email": "test@example.com",
        "phone": "+254712345678",
        "password": "TestPassword123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    await client.post("/api/v1/auth/register", json=user_data)
    
    # Then login
    login_data = {
        "email": "test@example.com",
        "password": "TestPassword123!"
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["email"] == login_data["email"]

@pytest.mark.asyncio
async def test_user_login_invalid_credentials(client: AsyncClient):
    """Test user login with invalid credentials"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword123!"
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    
    assert response.status_code == 401  # Authentication error

@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    """Test getting current user information"""
    # First register and login
    user_data = {
        "email": "test@example.com",
        "phone": "+254712345678",
        "password": "TestPassword123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    token_data = register_response.json()
    
    # Get current user
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["first_name"] == user_data["first_name"]
    assert data["last_name"] == user_data["last_name"]
    assert data["kyc_status"] == "pending"
