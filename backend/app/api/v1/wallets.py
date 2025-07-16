"""
Wallet management endpoints.
Handles creation, balance checks, and transaction history for user wallets.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Annotated
from decimal import Decimal

from app.core.database import get_async_db
from app.core.exceptions import NotFoundError, ValidationError, DuplicateEntryError
from app.schemas.wallet import WalletCreate, WalletResponse, WalletHistoryEntry
from app.services.wallet import WalletService
from app.services.auth import get_current_user_dependency
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    wallet_data: WalletCreate,
    current_user: Annotated[User, Depends(get_current_user_dependency)],
    db: AsyncSession = Depends(get_async_db)
) -> WalletResponse:
    """
    Create a new wallet for the current user.
    A user can have multiple wallets for different currencies.
    """
    try:
        wallet_service = WalletService(db)
        new_wallet = await wallet_service.create_wallet(user_id=current_user.id, wallet_data=wallet_data)
        return new_wallet
    except DuplicateEntryError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create wallet: {str(e)}")

@router.get("/", response_model=List[WalletResponse])
async def get_user_wallets(
    current_user: Annotated[User, Depends(get_current_user_dependency)],
    db: AsyncSession = Depends(get_async_db)
) -> List[WalletResponse]:
    """
    Retrieve all wallets belonging to the current user.
    """
    try:
        wallet_service = WalletService(db)
        wallets = await wallet_service.get_user_wallets(user_id=current_user.id)
        return wallets
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve wallets: {str(e)}")

@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet_by_id(
    wallet_id: str,
    current_user: Annotated[User, Depends(get_current_user_dependency)],
    db: AsyncSession = Depends(get_async_db)
) -> WalletResponse:
    """
    Retrieve a specific wallet by its ID for the current user.
    """
    try:
        wallet_service = WalletService(db)
        wallet = await wallet_service.get_wallet_by_id(wallet_id=wallet_id, user_id=current_user.id)
        if not wallet:
            raise NotFoundError("Wallet not found or does not belong to user")
        return wallet
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve wallet: {str(e)}")

@router.get("/{wallet_id}/history", response_model=List[WalletHistoryEntry])
async def get_wallet_history(
    wallet_id: str,
    current_user: Annotated[User, Depends(get_current_user_dependency)],
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db)
) -> List[WalletHistoryEntry]:
    """
    Retrieve transaction history for a specific wallet.
    """
    try:
        wallet_service = WalletService(db)
        history = await wallet_service.get_wallet_history(
            wallet_id=wallet_id,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        return history
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve wallet history: {str(e)}")

@router.patch("/{wallet_id}/deactivate", response_model=WalletResponse)
async def deactivate_wallet(
    wallet_id: str,
    current_user: Annotated[User, Depends(get_current_user_dependency)],
    db: AsyncSession = Depends(get_async_db)
) -> WalletResponse:
    """
    Deactivate a wallet. Funds cannot be moved in/out of a deactivated wallet.
    """
    try:
        wallet_service = WalletService(db)
        updated_wallet = await wallet_service.deactivate_wallet(wallet_id=wallet_id, user_id=current_user.id)
        return updated_wallet
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to deactivate wallet: {str(e)}")
