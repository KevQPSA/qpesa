"""
Wallet service for managing user wallets.
Handles creation, balance updates, and history retrieval.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from decimal import Decimal
import uuid
from datetime import datetime

from app.core.exceptions import NotFoundError, ValidationError, DuplicateEntryError
from app.schemas.wallet import WalletCreate, WalletResponse, WalletHistoryEntry
from app.models.wallet import Wallet, WalletType
from app.models.transaction import Transaction, TransactionType, TransactionStatus # For history
from app.models.user import User # For user validation

class WalletService:
    """Service class for wallet operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_wallet(self, user_id: uuid.UUID, wallet_data: WalletCreate) -> WalletResponse:
        """
        Create a new wallet for a user.
        Ensures a user doesn't have duplicate wallets for the same currency.
        """
        # Check if user exists
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")

        # Check for existing wallet of the same currency for this user
        existing_wallet_stmt = select(Wallet).where(
            Wallet.user_id == user_id,
            Wallet.currency == wallet_data.currency
        )
        existing_wallet_result = await self.db.execute(existing_wallet_stmt)
        if existing_wallet_result.scalar_one_or_none():
            raise DuplicateEntryError(f"Wallet for currency {wallet_data.currency} already exists for this user.")

        new_wallet = Wallet(
            user_id=user_id,
            currency=wallet_data.currency,
            wallet_type=wallet_data.wallet_type,
            address=wallet_data.address,
            balance=Decimal('0.0') # New wallets start with 0 balance
        )
        self.db.add(new_wallet)
        await self.db.commit()
        await self.db.refresh(new_wallet)
        return WalletResponse.from_orm(new_wallet)
    
    async def get_user_wallets(self, user_id: uuid.UUID) -> List[WalletResponse]:
        """Retrieve all wallets for a given user."""
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        result = await self.db.execute(stmt)
        wallets = result.scalars().all()
        return [WalletResponse.from_orm(wallet) for wallet in wallets]

    async def get_wallet_by_id(self, wallet_id: uuid.UUID, user_id: uuid.UUID) -> Optional[WalletResponse]:
        """Retrieve a specific wallet by ID, ensuring it belongs to the user."""
        stmt = select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id)
        result = await self.db.execute(stmt)
        wallet = result.scalar_one_or_none()
        if not wallet:
            return None
        return WalletResponse.from_orm(wallet)

    async def update_wallet_balance(self, wallet_id: uuid.UUID, amount: Decimal, transaction_type: TransactionType) -> WalletResponse:
        """
        Update a wallet's balance.
        This method should be called internally by transaction processing, not directly by API.
        """
        stmt = select(Wallet).where(Wallet.id == wallet_id)
        result = await self.db.execute(stmt)
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            raise NotFoundError("Wallet not found")
        if not wallet.is_active:
            raise ValidationError("Cannot update balance of an inactive wallet.")

        if transaction_type in [TransactionType.CRYPTO_DEPOSIT, TransactionType.FIAT_DEPOSIT]:
            wallet.balance += amount
        elif transaction_type in [TransactionType.CRYPTO_WITHDRAWAL, TransactionType.FIAT_WITHDRAWAL]:
            if wallet.balance < amount:
                raise ValidationError("Insufficient balance")
            wallet.balance -= amount
        else:
            raise ValidationError(f"Unsupported transaction type for balance update: {transaction_type}")

        await self.db.commit()
        await self.db.refresh(wallet)
        return WalletResponse.from_orm(wallet)

    async def get_wallet_history(self, wallet_id: uuid.UUID, user_id: uuid.UUID, limit: int = 50, offset: int = 0) -> List[WalletHistoryEntry]:
        """
        Retrieve transaction history for a specific wallet.
        This would typically involve filtering transactions related to this wallet.
        For simplicity, we'll fetch all user transactions and filter by currency.
        A more robust solution would link transactions directly to wallets.
        """
        wallet_stmt = select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id)
        wallet_result = await self.db.execute(wallet_stmt)
        wallet = wallet_result.scalar_one_or_none()
        if not wallet:
            raise NotFoundError("Wallet not found or does not belong to user")

        stmt = (
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.currency == wallet.currency # Filter by wallet's currency
            )
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        transactions = result.scalars().all()

        history = []
        for tx in transactions:
            # This is a simplified mapping. In a real system, you'd calculate balance_after
            # based on a running balance or fetch it from a dedicated ledger.
            history.append(WalletHistoryEntry(
                transaction_id=str(tx.id),
                type=tx.transaction_type.value,
                amount=tx.amount,
                currency=tx.currency,
                balance_after=wallet.balance, # Placeholder, needs actual calculation
                created_at=tx.created_at,
                description=tx.notes
            ))
        return history

    async def deactivate_wallet(self, wallet_id: uuid.UUID, user_id: uuid.UUID) -> WalletResponse:
        """Deactivate a wallet, preventing further transactions."""
        stmt = select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id)
        result = await self.db.execute(stmt)
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            raise NotFoundError("Wallet not found or does not belong to user")
        
        if not wallet.is_active:
            raise ValidationError("Wallet is already inactive.")
        
        wallet.is_active = False
        await self.db.commit()
        await self.db.refresh(wallet)
        return WalletResponse.from_orm(wallet)
