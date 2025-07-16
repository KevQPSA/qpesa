"""
Database configuration with async SQLAlchemy and connection pooling.
Optimized for high-concurrency financial transactions.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy import event, create_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator, Generator
import logging
from decimal import Decimal # Important for financial precision

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async engine with connection pooling
# `asyncpg` is the recommended async driver for PostgreSQL
async_engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,   # Recycle connections every hour (prevents stale connections)
    echo=settings.DEBUG,  # Log SQL queries in debug mode (set to False in production)
    json_serializer=lambda obj: obj.isoformat() if isinstance(obj, datetime) else str(obj) if isinstance(obj, Decimal) else obj # Handle JSON serialization for datetime/Decimal
)

# Create session factory for async operations
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False # Prevents objects from expiring after commit
)

# Create synchronous engine for specific use cases (e.g., Alembic migrations, initial setup)
# Note: FastAPI dependencies should primarily use the async session.
sync_engine = create_engine(
    settings.DATABASE_URL.replace("+asyncpg", ""), # Remove asyncpg part for sync engine
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

# Create synchronous session factory
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Declarative base for SQLAlchemy models
Base = declarative_base()

# Dependency for async database sessions in FastAPI routes
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an asynchronous database session for FastAPI endpoints.
    Ensures proper session cleanup (commit/rollback/close) after request.
    
    Why Decimal is critical for financial apps:
    Floating-point numbers (float) have precision issues that can lead to
    rounding errors in financial calculations. Decimal type provides exact
    decimal arithmetic, preventing these errors.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback() # Rollback changes on error
            logger.error(f"Database session error: {str(e)}")
            raise # Re-raise the exception to be handled by FastAPI's exception handlers
        finally:
            await session.close()

# Dependency for synchronous database sessions (less common in async FastAPI)
def get_sync_db() -> Generator:
    """
    Provides a synchronous database session.
    Useful for background tasks or scripts that are not part of an async request-response cycle.
    """
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Connection event listeners for monitoring and configuration
@event.listens_for(sync_engine, "connect")
def set_postgresql_timezone(dbapi_connection, connection_record):
    """
    Sets the timezone for PostgreSQL connections to UTC.
    Ensures consistent timestamp handling across the application.
    """
    if "postgresql" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("SET timezone TO 'UTC'")
        cursor.close()

@event.listens_for(sync_engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Logs when a database connection is checked out from the pool."""
    logger.debug("Database connection checked out")

@event.listens_for(sync_engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Logs when a database connection is checked back into the pool."""
    logger.debug("Database connection checked in")
