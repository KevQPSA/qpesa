"""
Authentication service.
Handles user authentication, JWT tokens, and session management.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from typing import Annotated
from abc import ABC, abstractmethod
import logging
import uuid

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ValidationError, DuplicateEntryError, NotFoundError
from app.models.user import User, UserRole, KYCStatus
from app.schemas.auth import UserRegistration, UserLogin, TokenResponse

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
class IAuthService(ABC):
    """Abstract base class for authentication service."""
    @abstractmethod
    async def register_user(self, user_data: UserRegistration) -> TokenResponse:
        pass

    @abstractmethod
    async def authenticate_user(self, login_data: UserLogin) -> TokenResponse:
        pass

    @abstractmethod
    async def get_current_user(self, token: str) -> User:
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token_str: str) -> TokenResponse:
        pass

    @abstractmethod
    async def logout_user(self, token: str) -> None:
        pass
    """Authentication service class."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Helper to get a user by email."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_user_by_phone(self, phone: str) -> Optional[User]:
        """Helper to get a user by phone number."""
        stmt = select(User).where(User.phone == phone)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Helper to get a user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def register_user(self, user_data: UserRegistration) -> TokenResponse:
        """Register a new user."""
        # Check if user already exists by email or phone
        if await self._get_user_by_email(user_data.email):
            raise DuplicateEntryError("Email already registered.")
        if await self._get_user_by_phone(user_data.phone):
            raise DuplicateEntryError("Phone number already registered.")
        
        # Hash password
        hashed_password = pwd_context.hash(user_data.password)
        
        # Create new user
        new_user = User(
            email=user_data.email,
            phone=user_data.phone,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=UserRole.CUSTOMER,
            kyc_status=KYCStatus.REQUIRED # Initial KYC status
        )
        
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        # Generate tokens
        access_token = self._create_access_token(str(new_user.id), "access")
        refresh_token = self._create_access_token(str(new_user.id), "refresh")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, # Convert minutes to seconds
            user_id=str(new_user.id),
            email=new_user.email,
            kyc_status=new_user.kyc_status
        )
    
    async def authenticate_user(self, login_data: UserLogin) -> TokenResponse:
        """Authenticate user and return tokens."""
        user = await self._get_user_by_email(login_data.email)
        
        if not user or not pwd_context.verify(login_data.password, user.password_hash):
            # Increment failed login attempts (conceptual)
            # user.failed_login_attempts += 1
            # await self.db.commit()
            raise AuthenticationError("Invalid email or password.")
        
        # Brute-force protection stub
        # If user.failed_login_attempts > threshold, lock account and raise error
        # Example:
        # if user.failed_login_attempts > 5:
        #     user.is_locked = True
        #     await self.db.commit()
        #     raise AuthenticationError("Account locked due to too many failed login attempts.")
        if not user.is_active:
            raise AuthenticationError("Account is deactivated.")
        
        # Reset failed login attempts and update last login
        user.last_login = datetime.now(timezone.utc)
        user.failed_login_attempts = 0
        await self.db.commit()
        
        # Generate tokens
        access_token = self._create_access_token(str(user.id), "access")
        refresh_token = self._create_access_token(str(user.id), "refresh")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            email=user.email,
            kyc_status=user.kyc_status
        )
    
    async def get_current_user(self, token: str) -> User:
        """Get current user from JWT token."""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            user_id_str = payload.get("sub")
            token_type = payload.get("type")
            
            if user_id_str is None or token_type != "access":
                raise AuthenticationError("Invalid token or wrong token type.")
            
            user_id = uuid.UUID(user_id_str)
        except (JWTError, ValueError): # ValueError for invalid UUID string
            raise AuthenticationError("Invalid token.")
        
        user = await self._get_user_by_id(user_id)
        
        if user is None:
            raise AuthenticationError("User not found.")
        
        if not user.is_active:
            raise AuthenticationError("Account is deactivated.")
        
        return user
    
    async def refresh_token(self, refresh_token_str: str) -> TokenResponse:
        """Refresh access token using a valid refresh token."""
        try:
            payload = jwt.decode(
                refresh_token_str,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            user_id_str = payload.get("sub")
            token_type = payload.get("type")
            
            if user_id_str is None or token_type != "refresh":
                raise AuthenticationError("Invalid refresh token or wrong token type.")
            
            user_id = uuid.UUID(user_id_str)
        except (JWTError, ValueError):
            raise AuthenticationError("Invalid refresh token.")
        
        user = await self._get_user_by_id(user_id)
        
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive.")
        
        # Generate new tokens
        access_token = self._create_access_token(str(user.id), "access")
        new_refresh_token = self._create_access_token(str(user.id), "refresh") # Issue new refresh token
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            email=user.email,
            kyc_status=user.kyc_status
        )
    
    async def logout_user(self, token: str) -> None:
        """Logout user and invalidate token."""
        # In a production system, you would add the token to a blacklist (e.g., Redis)
        # with its expiration time. For now, we'll just validate the token.
        await self.get_current_user(token) # Ensure the token is valid before "logging out"
        logger.info(f"Simulated logout for token: {token[:10]}...")
   
    def _create_access_token(self, user_id: str, token_type: str) -> str:
        """Create JWT token (access or refresh)."""
        if token_type == "access":
            expire_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        elif token_type == "refresh":
            expire_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS) # Assuming a setting for refresh token expiry
        else:
            raise ValueError("Invalid token type.")

        expire = datetime.now(timezone.utc) + expire_delta
        payload = {
            "sub": user_id,
            "type": token_type,
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# Dependency for getting current user
async def get_current_user_dependency(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """FastAPI dependency for getting current authenticated user."""
    auth_service = AuthService(db)
    return await auth_service.get_current_user(credentials.credentials)
