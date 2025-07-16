"""
Admin service for system-wide management tasks.
Handles user management, transaction oversight, and system settings.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from decimal import Decimal
import uuid
from datetime import datetime

from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.auth import UserResponse
from app.schemas.payment import PaymentHistoryEntry
from app.schemas.admin import AdminUserUpdate, AdminTransactionFilter, AdminSystemSetting, AdminSystemSettingUpdate
from app.models.user import User, UserRole, KYCStatus
from app.models.transaction import Transaction, TransactionType, TransactionStatus

class AdminService:
    """Service class for administrative operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[UserResponse]:
        """Retrieve a paginated list of all users."""
        stmt = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        return [UserResponse.from_orm(user) for user in users]

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserResponse]:
        """Retrieve a specific user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return None
        return UserResponse.from_orm(user)

    async def update_user(self, user_id: uuid.UUID, update_data: AdminUserUpdate) -> UserResponse:
        """Update a user's information."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User not found")
        
        update_data_dict = update_data.dict(exclude_unset=True)
        for key, value in update_data_dict.items():
            setattr(user, key, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return UserResponse.from_orm(user)

    async def get_all_transactions(self, filters: AdminTransactionFilter) -> List[PaymentHistoryEntry]:
        """Retrieve a filtered and paginated list of all transactions."""
        stmt = select(Transaction).order_by(Transaction.created_at.desc())

        if filters.user_id:
            stmt = stmt.where(Transaction.user_id == filters.user_id)
        if filters.transaction_type:
            stmt = stmt.where(Transaction.transaction_type == filters.transaction_type)
        if filters.status:
            stmt = stmt.where(Transaction.status == filters.status)
        if filters.currency:
            stmt = stmt.where(Transaction.currency == filters.currency)
        if filters.start_date:
            stmt = stmt.where(Transaction.created_at >= filters.start_date)
        if filters.end_date:
            stmt = stmt.where(Transaction.created_at <= filters.end_date)
        if filters.min_amount is not None:
            stmt = stmt.where(Transaction.amount >= Decimal(str(filters.min_amount)))
        if filters.max_amount is not None:
            stmt = stmt.where(Transaction.amount <= Decimal(str(filters.max_amount)))

        stmt = stmt.limit(filters.limit).offset(filters.offset)
        
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

    async def get_system_settings(self) -> List[AdminSystemSetting]:
        """Retrieve all system settings. (Placeholder - implement a Settings model if needed)"""
        # In a real system, you'd have a dedicated 'Settings' model in your database
        # For now, return mock settings
        return [
            AdminSystemSetting(key="min_crypto_deposit_btc", value="0.0001", description="Minimum BTC deposit amount"),
            AdminSystemSetting(key="mpesa_stk_timeout_seconds", value="60", description="M-Pesa STK Push timeout"),
            AdminSystemSetting(key="kyc_required_threshold_usd", value="1000", description="KYC required for transactions over this amount (USD equivalent)"),
        ]

    async def update_system_setting(self, key: str, update_data: AdminSystemSettingUpdate) -> AdminSystemSetting:
        """Update a specific system setting. (Placeholder)"""
        # In a real system, you'd update the Settings model in your database
        # For now, simulate update
        mock_settings = {
            "min_crypto_deposit_btc": AdminSystemSetting(key="min_crypto_deposit_btc", value="0.0001", description="Minimum BTC deposit amount"),
            "mpesa_stk_timeout_seconds": AdminSystemSetting(key="mpesa_stk_timeout_seconds", value="60", description="M-Pesa STK Push timeout"),
            "kyc_required_threshold_usd": AdminSystemSetting(key="kyc_required_threshold_usd", value="1000", description="KYC required for transactions over this amount (USD equivalent)"),
        }
        if key not in mock_settings:
            raise NotFoundError("Setting not found")
        
        setting = mock_settings[key]
        setting.value = update_data.value
        if update_data.description:
            setting.description = update_data.description
        
        return setting
