"""
Authentication endpoints.
Handles user registration, login, and JWT token management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Annotated
import logging

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ValidationError, DuplicateEntryError, NotFoundError
from app.schemas.auth import UserRegistration, UserLogin, TokenResponse
from app.services.auth import AuthService
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer() # For token extraction from Authorization header

@router.post("/register", response_model=TokenResponse, summary="Register a new user")
async def register_user(
    user_data: UserRegistration,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    """
    Register a new user with email and phone verification.
    Initiates KYC process for compliance.
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.register_user(user_data)
        
        logger.info(f"User registered successfully: {user_data.email}")
        return result
        
    except DuplicateEntryError as e:
        logger.warning(f"Registration failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    except ValidationError as e:
        logger.warning(f"Registration validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to an unexpected error."
        )

@router.post("/login", response_model=TokenResponse, summary="Authenticate user and get tokens")
async def login_user(
    login_data: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.
    Implements rate limiting and failed attempt tracking (conceptual).
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.authenticate_user(login_data)
        
        logger.info(f"User logged in successfully: {login_data.email}")
        return result
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Login failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to an unexpected error."
        )

@router.post("/refresh", response_model=TokenResponse, summary="Refresh JWT access token")
async def refresh_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    """
    Refresh JWT access token using refresh token.
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.refresh_token(credentials.credentials)
        
        return result
        
    except AuthenticationError as e:
        logger.warning(f"Token refresh failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed due to an unexpected error."
        )

@router.post("/logout", summary="Logout user and invalidate tokens")
async def logout_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Dict[str, str]:
    """
    Logout user and invalidate tokens.
    In a production system, this would add the token to a blacklist.
    """
    try:
        auth_service = AuthService(db)
        await auth_service.logout_user(credentials.credentials)
        
        logger.info("User logged out successfully.")
        return {"message": "Logged out successfully"}
        
    except AuthenticationError as e:
        logger.warning(f"Logout failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed due to an unexpected error."
        )

@router.get("/me", summary="Get current user information")
async def get_current_user_info(
    current_user: Annotated[Any, Depends(AuthService.get_current_user_dependency)] # Use the dependency directly
) -> Dict[str, Any]:
    """
    Get current user information based on the provided access token.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "phone": current_user.phone,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "kyc_status": current_user.kyc_status.value,
        "role": current_user.role.value,
        "is_verified": current_user.is_verified,
        "is_active": current_user.is_active
    }
