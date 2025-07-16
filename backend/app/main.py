"""
FastAPI main application for Kenya Crypto-Fiat Payment Processor.
Handles BTC/USDT payments with M-Pesa integration.
"""
from fastapi import FastAPI, Request, status, Depends
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
from typing import Dict, Any, Annotated

from app.core.config import settings
from app.core.database import async_engine, Base, get_db
from app.core.exceptions import CustomException
from app.api.v1 import auth, payments, wallets, merchants, admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events for startup and shutdown."""
    # Startup
    logger.info("Starting Kenya Crypto-Fiat Payment Processor")
    
    # Create database tables if they don't exist
    # This is for development/testing. In production, use Alembic migrations.
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield # Application runs
    
    # Shutdown
    logger.info("Shutting down application")
    await async_engine.dispose() # Close database connections

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None, # Disable docs in production
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None, # Disable redoc in production
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan # Register the lifespan context manager
)

# Security middleware: TrustedHostMiddleware to prevent HTTP Host Header attacks
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"], # OPTIONS for preflight requests
    allow_headers=["*"], # Allow all headers
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Logs request processing time and warns about slow requests."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests (>1 second)
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.method} {request.url} took {process_time:.2f}s")
    
    return response

# Simple rate limiting middleware (for demonstration)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import collections

RATE_LIMIT = 100  # requests
RATE_LIMIT_WINDOW = 60  # seconds
request_counts = collections.defaultdict(list)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        client_ip = request.client.host
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW
        # Remove old requests
        request_counts[client_ip] = [t for t in request_counts[client_ip] if t > window_start]
        if len(request_counts[client_ip]) >= RATE_LIMIT:
            return Response("Rate limit exceeded", status_code=429)
        request_counts[client_ip].append(now)
        return await call_next(request)

app.add_middleware(RateLimitMiddleware)

# Global exception handler for CustomException
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    """Handles custom exceptions and returns a standardized JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details}
    )

# Health check endpoints
@app.get("/health", tags=["Health"], summary="Basic Health Check")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    Returns "healthy" if the application is running.
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.PROJECT_VERSION
    }

@app.get("/ready", tags=["Health"], summary="Readiness Probe")
async def readiness_probe(db: Annotated[Any, Depends(get_db)]) -> Dict[str, Any]:
    """
    Readiness probe endpoint.
    Checks if the application is ready to serve traffic, including database connectivity.
    """
    try:
        # Test database connection by executing a simple query
        await db.execute("SELECT 1")
        return {
            "status": "ready",
            "database": "connected",
            "timestamp": time.time(),
            "version": settings.PROJECT_VERSION
        }
    except Exception as e:
        logger.error(f"Readiness probe failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unready",
                "database": "disconnected",
                "error": str(e),
                "timestamp": time.time()
            }
        )

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(wallets.router, prefix="/api/v1/wallets", tags=["Wallets"])
app.include_router(merchants.router, prefix="/api/v1/merchants", tags=["Merchants"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development" # Enable auto-reload in development
    )
