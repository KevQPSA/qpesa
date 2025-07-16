"""
Merchant management endpoints.
Handles merchant registration, profile updates, and specific merchant operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.core.database import get_async_db
from app.core.exceptions import NotFoundError, ValidationError, DuplicateEntryError, AuthorizationError
from app.schemas.merchant import MerchantCreate, MerchantResponse, MerchantUpdate
from app.services.merchant import MerchantService
from app.services.auth import get_current_user_dependency
from app.models.user import User, UserRole # Import UserRole for authorization

router = APIRouter()

@router.post("/", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
async def register_merchant(
    merchant_data: MerchantCreate,
    current_user: Annotated[User, Depends(get_current_user_dependency)],
    db: AsyncSession = Depends(get_async_db)
) -> MerchantResponse:
    """
    Register a new merchant account.
    Requires the user to be a customer initially, and their role will be updated.
    """
    if current_user.role != UserRole.CUSTOMER:
        raise AuthorizationError("Only customer accounts can register as merchants.")
    if str(current_user.id) != merchant_data.user_id:
        raise AuthorizationError("Cannot register a merchant account for another user.")

    try:
        merchant_service = MerchantService(db)
        new_merchant = await merchant_service.register_merchant(user_id=current_user.id, merchant_data=merchant_data)
        return new_merchant
    except DuplicateEntryError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to register merchant: {str(e)}")

@router.get("/me", response_model=MerchantResponse)
async def get_current_merchant_profile(
    current_user: Annotated[User, Depends(get_current_user_dependency)],
    db: AsyncSession = Depends(get_async_db)
) -> MerchantResponse:
    """
    Retrieve the profile of the current authenticated merchant.
    """
    if current_user.role != UserRole.MERCHANT:
        raise AuthorizationError("User is not a merchant.")
    
    try:
        merchant_service = MerchantService(db)
        merchant = await merchant_service.get_merchant_by_user_id(user_id=current_user.id)
        if not merchant:
            raise NotFoundError("Merchant profile not found.")
        return merchant
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve merchant profile: {str(e)}")

@router.patch("/me", response_model=MerchantResponse)
async def update_current_merchant_profile(
    merchant_update: MerchantUpdate,
    current_user: Annotated[User, Depends(get_current_user_dependency)],
    db: AsyncSession = Depends(get_async_db)
) -> MerchantResponse:
    """
    Update the profile of the current authenticated merchant.
    """
    if current_user.role != UserRole.MERCHANT:
        raise AuthorizationError("User is not a merchant.")
    
    try:
        merchant_service = MerchantService(db)
        updated_merchant = await merchant_service.update_merchant_profile(user_id=current_user.id, update_data=merchant_update)
        return updated_merchant
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update merchant profile: {str(e)}")

# Merchant-specific payment endpoints (simplified, could be more complex)
@router.get("/payments/history", response_model=List[PaymentHistoryEntry])
async def get_merchant_payment_history(
    current_user: Annotated[User, Depends(get_current_user_dependency)],
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db)
) -> List[PaymentHistoryEntry]:
    """
    Retrieve payment history for the current merchant.
    This would typically show payments received by the merchant.
    """
    if current_user.role != UserRole.MERCHANT:
        raise AuthorizationError("User is not a merchant.")
    
    try:
        merchant_service = MerchantService(db)
        history = await merchant_service.get_merchant_payment_history(
            merchant_user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve merchant payment history: {str(e)}")
