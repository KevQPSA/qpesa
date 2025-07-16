"""
Pytest fixtures for API and database testing.
Provides an async HTTP client and a clean database session for each test.
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.main import app
from app.core.database import Base, get_db, async_engine as app_async_engine, sync_engine as app_sync_engine
from app.core.config import settings
from app.models.user import User, UserRole, KYCStatus
from app.services.auth import AuthService # Import AuthService to create users directly for refresh/logout tests
from datetime import timedelta, datetime, timezone
import os

# Override database URL for testing
# Use a different database name for tests to avoid conflicts with dev/prod
TEST_DATABASE_URL = settings.DATABASE_URL.replace("kcb_crypto_fiat_db", "kcb_crypto_fiat_test_db")

# Create an async engine for tests
test_async_engine = create_async_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    echo=False # Set to True to see SQL queries during tests
)

# Create a sessionmaker for the test database
TestingAsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_async_engine,
    class_=AsyncSession
)

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Set up and tear down the test database for the entire test session.
    Ensures a clean database for all tests.
    """
    # Ensure the test database exists and is empty before running tests
    # This part might need to be run outside pytest if the database itself needs creation
    # For now, assume the test DB exists and we just manage tables.
    
    # Drop all tables and recreate them
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) # Drop existing tables
        await conn.run_sync(Base.metadata.create_all) # Create new tables
    
    yield # Run tests
    
    # Clean up after tests
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) # Drop tables again

@pytest.fixture(scope="function")
async def db_session():
    """
    Provide a clean, independent database session for each test function.
    Rolls back transactions after each test to ensure isolation.
    """
    async with TestingAsyncSessionLocal() as session:
        # Begin a transaction
        await session.begin()
        try:
            yield session
        finally:
            # Rollback the transaction to clean up changes made by the test
            await session.rollback()
            await session.close()

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    """
    Provide an AsyncClient for making HTTP requests to the FastAPI app.
    Overrides the get_db dependency to use the test session.
    """
    # Override the get_db dependency to use the test session
    app.dependency_overrides[get_db] = lambda: db_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Clear overrides after the test
    app.dependency_overrides.clear()

@pytest.fixture
async def registered_user_data():
    """Returns sample user data for registration."""
    return {
        "email": "test_user@example.com",
        "phone": "+254712345678",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.fixture
async def registered_user(db_session: AsyncSession, registered_user_data: dict) -> User:
    """Registers a test user in the database and returns the user object."""
    auth_service = AuthService(db_session)
    # Use the service to register, which handles hashing and adds to DB
    token_response = await auth_service.register_user(
        UserRegistration(**registered_user_data)
    )
    # Fetch the user object from DB to ensure it's a proper SQLAlchemy instance
    user = await db_session.get(User, token_response.user_id)
    return user

@pytest.fixture
async def authenticated_client(client: AsyncClient, registered_user: User, db_session: AsyncSession):
    """Fixture to provide an authenticated client for tests."""
    auth_service = AuthService(db_session)
    login_data = {
        "email": registered_user.email,
        "password": "SecurePassword123!" # Use the password from registered_user_data
    }
    token_response = await auth_service.authenticate_user(login_data)
    access_token = token_response.access_token
    
    client.headers = {"Authorization": f"Bearer {access_token}"}
    return client

@pytest.fixture
async def admin_user_data():
    """Returns sample admin user data for registration."""
    return {
        "email": "admin@example.com",
        "phone": "+254700000000",
        "password": "AdminSecurePassword123!",
        "first_name": "Admin",
        "last_name": "User"
    }

@pytest.fixture
async def registered_admin_user(db_session: AsyncSession, admin_user_data: dict) -> User:
    """Registers a test admin user in the database and returns the user object."""
    auth_service = AuthService(db_session)
    # Register as a normal user first
    token_response = await auth_service.register_user(
        UserRegistration(**admin_user_data)
    )
    # Fetch the user and update their role to admin
    admin_user = await db_session.get(User, token_response.user_id)
    admin_user.role = UserRole.ADMIN
    admin_user.kyc_status = KYCStatus.VERIFIED # Admins are typically verified
    admin_user.is_verified = True
    await db_session.commit()
    await db_session.refresh(admin_user)
    return admin_user

@pytest.fixture
async def authenticated_admin_client(client: AsyncClient, registered_admin_user: User, db_session: AsyncSession):
    """Fixture to provide an authenticated admin client for tests."""
    auth_service = AuthService(db_session)
    login_data = {
        "email": registered_admin_user.email,
        "password": "AdminSecurePassword123!"
    }
    token_response = await auth_service.authenticate_user(login_data)
    access_token = token_response.access_token
    
    client.headers = {"Authorization": f"Bearer {access_token}"}
    return client
