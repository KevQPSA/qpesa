"""
Merchant service for managing merchant accounts and operations.
Handles merchant registration, profile updates, and merchant-specific reporting.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from decimal import Decimal
import uuid
from datetime import datetime

from app.core.exceptions import NotFoundError, ValidationError, DuplicateEntryError
from app.schemas.merchant import MerchantCreate, MerchantResponse, MerchantUpdate
from app.schemas.payment import PaymentHistoryEntry # For merchant payment history
from app.models.merchant import Merchant, MerchantStatus
from app.models.user import User, UserRole, KYCStatus # For user role update
from app.models.transaction import Transaction, TransactionType, TransactionStatus # For payment history

class MerchantService:
    """Service class for merchant operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_merchant(self, user_id: uuid.UUID, merchant_data: MerchantCreate) -> MerchantResponse:
        """
        Register a new merchant account for an existing user.
        Updates the user's role to MERCHANT.
        """
        # Check if user exists and is a customer
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        if user.role != UserRole.CUSTOMER:
            raise ValidationError("Only customer accounts can be upgraded to merchants.")

        # Check if merchant profile already exists for this user
        existing_merchant_stmt = select(Merchant).where(Merchant.user_id == user_id)
        existing_merchant_result = await self.db.execute(existing_merchant_stmt)
        if existing_merchant_result.scalar_one_or_none():
            raise DuplicateEntryError("Merchant profile already exists for this user.")

        # Check for duplicate business email or phone
        duplicate_check_stmt = select(Merchant).where(
            (Merchant.business_email == merchant_data.business_email) |
            (Merchant.business_phone == merchant_data.business_phone)
        )
        duplicate_check_result = await self.db.execute(duplicate_check_stmt)
        if duplicate_check_result.scalar_one_or_none():
            raise DuplicateEntryError("Business email or phone number already registered.")

        new_merchant = Merchant(
            user_id=user_id,
            business_name=merchant_data.business_name,
            business_email=merchant_data.business_email,
            business_phone=merchant_data.business_phone,
            status=MerchantStatus.PENDING_APPROVAL # Requires admin approval
        )
        self.db.add(new_merchant)
        
        # Update user role
        user.role = UserRole.MERCHANT
        user.kyc_status = KYCStatus.PENDING # Merchant KYC might be more stringent
        self.db.add(user)

        await self.db.commit()
        await self.db.refresh(new_merchant)
        await self.db.refresh(user) # Refresh user to reflect role change
        return MerchantResponse.from_orm(new_merchant)
    
    async def get_merchant_by_user_id(self, user_id: uuid.UUID) -> Optional[MerchantResponse]:
        """Retrieve a merchant profile by user ID."""
        stmt = select(Merchant).where(Merchant.user_id == user_id)
        result = await self.db.execute(stmt)
        merchant = result.scalar_one_or_none()
        if not merchant:
            return None
        return MerchantResponse.from_orm(merchant)

    async def update_merchant_profile(self, user_id: uuid.UUID, update_data: MerchantUpdate) -> MerchantResponse:
        """Update a merchant's profile."""
        stmt = select(Merchant).where(Merchant.user_id == user_id)
        result = await self.db.execute(stmt)
        merchant = result.scalar_one_or_none()
        
        if not merchant:
            raise NotFoundError("Merchant profile not found for this user.")
        
        update_data_dict = update_data.dict(exclude_unset=True)
        for key, value in update_data_dict.items():
            setattr(merchant, key, value)
        
        await self.db.commit()
        await self.db.refresh(merchant)
        return MerchantResponse.from_orm(merchant)

    async def get_merchant_payment_history(self, merchant_user_id: uuid.UUID, limit: int = 50, offset: int = 0) -> List[PaymentHistoryEntry]:
        """
        Retrieve payment history for a merchant.
        This would typically involve transactions where the merchant is the recipient.
        For simplicity, we'll fetch transactions where the user_id matches the merchant_user_id
        and the transaction type is a deposit.
        """
        stmt = (
            select(Transaction)
            .where(
                Transaction.user_id == merchant_user_id,
                Transaction.transaction_type.in_([TransactionType.CRYPTO_DEPOSIT, TransactionType.FIAT_DEPOSIT])
            )
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        transactions = result.scalars().all()

        history = []
        for tx in transactions:
            history.append(PaymentHistoryEntry(
                id=str(tx.id),
                type=tx.transaction_type,
                amount=tx.amount,
                currency=tx.currency,
                status=tx.status,
                network=tx.network,
                blockchain_hash=tx.blockchain_hash,
                confirmations=tx.confirmations,
                created_at=tx.created_at,
                completed_at=tx.completed_at,
                description=tx.notes
            ))
        return history
