"""
Main application API endpoint integration tests.
Tests health check endpoints and global exception handling.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock

from app.core.database import get_db
from app.core.exceptions import CustomException
from app.main import app # Import the main FastAPI app
from app.core.config import settings

@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test the root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to the Kenya Crypto-Fiat Payment Processor API"

@pytest.mark.asyncio
async def test_health_check_success(client: AsyncClient):
    """Test basic health check endpoint."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == settings.PROJECT_VERSION

@pytest.mark.asyncio
async def test_readiness_probe_success(client: AsyncClient):
    """Test readiness probe endpoint with successful DB connection."""
    response = await client.get("/ready")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert "timestamp" in data
    assert data["version"] == settings.PROJECT_VERSION

@pytest.mark.asyncio
async def test_readiness_probe_db_failure(client: AsyncClient, db_session: AsyncSession):
    """Test readiness probe endpoint with simulated DB connection failure."""
    # Mock the database execute method to raise an exception
    with patch.object(db_session, 'execute', side_effect=Exception("Database connection failed")):
        response = await client.get("/ready")
        
        assert response.status_code == 503
        data = response.json()["detail"] # Access detail from CustomException
        assert data["status"] == "unready"
        assert data["database"] == "disconnected"
        assert "Database connection failed" in data["error"]
        assert "timestamp" in data

@pytest.mark.asyncio
async def test_global_custom_exception_handler(client: AsyncClient):
    """Test the global custom exception handler."""
    # Create a dummy endpoint that raises a CustomException
    @app.get("/test-custom-exception")
    async def test_endpoint():
        raise CustomException(status_code=418, message="I'm a teapot", details={"code": "TEAPOT_ERROR"})

    response = await client.get("/test-custom-exception")
    
    assert response.status_code == 418
    data = response.json()
    assert data["error"] == "I'm a teapot"
    assert data["details"] == {"code": "TEAPOT_ERROR"}

    # Clean up the dummy endpoint (important for subsequent tests)
    app.routes = [route for route in app.routes if route.path != "/test-custom-exception"]

@pytest.mark.asyncio
async def test_cors_headers(client: AsyncClient):
    """Test if CORS headers are correctly set."""
    # Simulate a preflight OPTIONS request
    response = await client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, Authorization"
        }
    )
    assert response.status_code == 200 # Preflight success
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-methods" in response.headers
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "access-control-allow-headers" in response.headers
    assert "Content-Type" in response.headers["access-control-allow-headers"]
    assert "Authorization" in response.headers["access-control-allow-headers"]
    assert response.headers["access-control-allow-credentials"] == "true"

    # Test a simple GET request with CORS origin
    response = await client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
