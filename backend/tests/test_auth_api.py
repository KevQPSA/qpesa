"""
Authentication API endpoint integration tests.
Tests user registration, login, JWT token handling, refresh, and logout.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole, KYCStatus
from app.schemas.auth import UserRegistration, UserLogin
from app.services.auth import AuthService # Import AuthService to create users directly for refresh/logout tests
from datetime import datetime, timedelta, timezone

@pytest.mark.asyncio
async def test_user_registration_success(client: AsyncClient, registered_user_data: dict):
    """Test successful user registration."""
    response = await client.post("/api/v1/auth/register", json=registered_user_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["email"] == registered_user_data["email"]
    assert data["kyc_status"] == KYCStatus.REQUIRED.value
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert data["user_id"] is not None

@pytest.mark.asyncio
async def test_user_registration_duplicate_email(client: AsyncClient, registered_user: User, registered_user_data: dict):
    """Test user registration with duplicate email."""
    # Attempt to register again with the same email
    response = await client.post("/api/v1/auth/register", json=registered_user_data)
    
    assert response.status_code == 409 # Conflict
    assert response.json()["detail"] == "Email already registered."

@pytest.mark.asyncio
async def test_user_registration_duplicate_phone(client: AsyncClient, registered_user: User, registered_user_data: dict):
    """Test user registration with duplicate phone number."""
    # Change email but keep same phone
    duplicate_phone_data = registered_user_data.copy()
    duplicate_phone_data["email"] = "another_email@example.com"
    
    response = await client.post("/api/v1/auth/register", json=duplicate_phone_data)
    
    assert response.status_code == 409 # Conflict
    assert response.json()["detail"] == "Phone number already registered."

@pytest.mark.asyncio
async def test_user_registration_invalid_phone(client: AsyncClient, registered_user_data: dict):
    """Test user registration with invalid phone number format."""
    invalid_phone_data = registered_user_data.copy()
    invalid_phone_data["phone"] = "123456789"  # Invalid Kenyan phone format
    
    response = await client.post("/api/v1/auth/register", json=invalid_phone_data)
    
    assert response.status_code == 422  # Unprocessable Entity (Pydantic validation error)
    assert "Phone number must be a valid Kenyan number" in response.json()["detail"][0]["msg"]

@pytest.mark.asyncio
async def test_user_registration_weak_password(client: AsyncClient, registered_user_data: dict):
    """Test user registration with weak password."""
    weak_password_data = registered_user_data.copy()
    weak_password_data["password"] = "weak"  # Weak password
    
    response = await client.post("/api/v1/auth/register", json=weak_password_data)
    
    assert response.status_code == 422  # Unprocessable Entity (Pydantic validation error)
    assert "Password must be at least 8 characters long" in response.json()["detail"][0]["msg"]

@pytest.mark.asyncio
async def test_user_login_success(client: AsyncClient, registered_user: User, registered_user_data: dict):
    """Test successful user login."""
    login_data = {
        "email": registered_user_data["email"],
        "password": registered_user_data["password"]
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["email"] == login_data["email"]
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_user_login_invalid_credentials(client: AsyncClient):
    """Test user login with invalid credentials."""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword123!"
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    
    assert response.status_code == 401  # Authentication error
    assert response.json()["detail"] == "Invalid email or password."

@pytest.mark.asyncio
async def test_user_login_inactive_account(client: AsyncClient, db_session: AsyncSession, registered_user: User, registered_user_data: dict):
    """Test user login with an inactive account."""
    # Deactivate user directly in DB
    registered_user.is_active = False
    await db_session.commit()
    await db_session.refresh(registered_user)

    login_data = {
        "email": registered_user_data["email"],
        "password": registered_user_data["password"]
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Account is deactivated."

@pytest.mark.asyncio
async def test_get_current_user_success(authenticated_client: AsyncClient, registered_user: User):
    """Test getting current user information with valid token."""
    response = await authenticated_client.get("/api/v1/auth/me")
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == registered_user.email
    assert data["first_name"] == registered_user.first_name
    assert data["last_name"] == registered_user.last_name
    assert data["kyc_status"] == registered_user.kyc_status.value
    assert data["role"] == registered_user.role.value
    assert data["is_verified"] == registered_user.is_verified
    assert data["is_active"] == registered_user.is_active

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test getting current user information with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token."

@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    """Test getting current user information without a token."""
    response = await client.get("/api/v1/auth/me")
    
    assert response.status_code == 403 # HTTPBearer raises 403 if no credentials

@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, registered_user: User, db_session: AsyncSession):
    """Test successful token refresh."""
    auth_service = AuthService(db_session)
    login_data = UserLogin(email=registered_user.email, password="SecurePassword123!")
    initial_token_data = await auth_service.authenticate_user(login_data)
    
    headers = {"Authorization": f"Bearer {initial_token_data.refresh_token}"}
    response = await client.post("/api/v1/auth/refresh", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["access_token"] != initial_token_data.access_token
    assert data["refresh_token"] != initial_token_data.refresh_token
    assert data["email"] == registered_user.email

@pytest.mark.asyncio
async def test_refresh_token_invalid_refresh_token(client: AsyncClient):
    """Test token refresh with an invalid refresh token."""
    headers = {"Authorization": "Bearer invalid_refresh_token"}
    response = await client.post("/api/v1/auth/refresh", headers=headers)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token."

@pytest.mark.asyncio
async def test_refresh_token_with_access_token(client: AsyncClient, authenticated_client: AsyncClient):
    """Test token refresh using an access token instead of a refresh token."""
    # authenticated_client already has an access token in its headers
    access_token = authenticated_client.headers["Authorization"].split(" ")[1]
    
    headers = {"Authorization": f"Bearer {access_token}"} # Using access token
    response = await client.post("/api/v1/auth/refresh", headers=headers)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token or wrong token type." # Should fail because type is 'access' not 'refresh'

@pytest.mark.asyncio
async def test_logout_success(authenticated_client: AsyncClient):
    """Test successful user logout."""
    response = await authenticated_client.post("/api/v1/auth/logout")
    
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"

    # Verify token is invalidated (or at least no longer works for protected routes)
    # In a real system with a token blacklist, this would return 401.
    # For this simulation, it will still pass the token validation but the logout message is confirmed.
    verify_response = await authenticated_client.get("/api/v1/auth/me")
    assert verify_response.status_code == 401 # Expecting 401 if token is truly invalidated
    assert verify_response.json()["detail"] == "Invalid token." # Or similar message
