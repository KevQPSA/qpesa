"""
Pydantic schemas for admin-related data.
Defines data structures for user management, transaction review, and system settings.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models.user import UserRole, KYCStatus
from app.models.transaction import TransactionType, TransactionStatus

class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+254[1-9]\d{8}$")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    kyc_status: Optional[KYCStatus] = None
    role: Optional[UserRole] = None

class AdminTransactionFilter(BaseModel):
    user_id: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    status: Optional[TransactionStatus] = None
    currency: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    limit: int = 100
    offset: int = 0

class AdminSystemSetting(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class AdminSystemSettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None
