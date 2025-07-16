"""
Admin panel endpoints for system management.
Handles user management, transaction review, and system settings.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Annotated

from app.core.database import get_async_db
from app.core.exceptions import NotFoundError, ValidationError, AuthorizationError
from app.schemas.auth import UserResponse
from app.schemas.payment import PaymentHistoryEntry
from app.schemas.admin import AdminUserUpdate, AdminTransactionFilter, AdminSystemSetting, AdminSystemSettingUpdate
from app.services.admin import AdminService
from app.services.auth import get_current_user_dependency
from app.models.user import User, UserRole # Import UserRole for authorization

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency to ensure the current user is an admin
async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user_dependency)]
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise AuthorizationError("Only admin users can access this endpoint.")
    return current_user

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db)
) -> List[UserResponse]:
    """
    Retrieve a list of all users in the system (Admin only).
    """
    try:
        admin_service = AdminService(db)
        users = await admin_service.get_all_users(limit=limit, offset=offset)
        return users
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve users: {str(e)}")

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: AsyncSession = Depends(get_async_db)
) -> UserResponse:
    """
    Retrieve a specific user by ID (Admin only).
    """
    try:
        admin_service = AdminService(db)
        user = await admin_service.get_user_by_id(user_id=user_id)
        if not user:
            raise NotFoundError("User not found")
        return user
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve user: {str(e)}")

@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    user_id: str,
    user_update: AdminUserUpdate,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: AsyncSession = Depends(get_async_db)
) -> UserResponse:
    """
    Update a user's information (Admin only).
    Allows changing roles, KYC status, active status, etc.
    """
    try:
        admin_service = AdminService(db)
        updated_user = await admin_service.update_user(user_id=user_id, update_data=user_update)
        return updated_user
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update user: {str(e)}")

@router.get("/transactions", response_model=List[PaymentHistoryEntry])
async def get_all_transactions(
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    filters: Annotated[AdminTransactionFilter, Depends()],
    db: AsyncSession = Depends(get_async_db)
) -> List[PaymentHistoryEntry]:
    """
    Retrieve a list of all transactions with filtering capabilities (Admin only).
    """
    try:
        admin_service = AdminService(db)
        transactions = await admin_service.get_all_transactions(filters=filters)
        return transactions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve transactions: {str(e)}")

@router.get("/settings", response_model=List[AdminSystemSetting])
async def get_system_settings(
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: AsyncSession = Depends(get_async_db)
) -> List[AdminSystemSetting]:
    """
    Retrieve all system settings (Admin only).
    """
    try:
        admin_service = AdminService(db)
        settings = await admin_service.get_system_settings()
        return settings
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve settings: {str(e)}")

@router.patch("/settings/{key}", response_model=AdminSystemSetting)
async def update_system_setting(
    key: str,
    setting_update: AdminSystemSettingUpdate,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: AsyncSession = Depends(get_async_db)
) -> AdminSystemSetting:
    """
    Update a specific system setting (Admin only).
    """
    try:
        admin_service = AdminService(db)
        updated_setting = await admin_service.update_system_setting(key=key, update_data=setting_update)
        return updated_setting
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update setting: {str(e)}")
