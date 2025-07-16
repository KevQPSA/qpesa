"""
Pydantic schemas for authentication-related data.
Defines data structures for user registration, login, and token responses.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, KYCStatus # Import enums from models

class UserBase(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+254[1-9]\d{8}$", description="Kenyan phone number in international format (+254XXXXXXXXX)")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=64, description="Password must be at least 8 characters long")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    kyc_status: KYCStatus
    role: UserRole
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True # For Pydantic v2, use from_attributes=True instead of orm_mode=True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    expires_in: int # Seconds until access token expires

class TokenResponse(Token):
    user_id: str
    email: EmailStr
    kyc_status: KYCStatus
