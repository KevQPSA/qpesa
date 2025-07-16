"""
Pydantic schemas for merchant-related data.
Includes merchant registration, response, payment link management, and settings.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from decimal import Decimal
from datetime import datetime
from app.models.merchant import MerchantStatus # Import enum from models

class MerchantRegistration(BaseModel):
    """Schema for merchant registration request"""
    business_name: str = Field(..., min_length=3, max_length=100)
    contact_email: EmailStr = Field(..., example="merchant@example.com")
    phone_number: str = Field(..., example="+254712345678", min_length=10, max_length=15)
    industry: Optional[str] = Field(None, max_length=100)
    website_url: Optional[str] = Field(None, example="https://www.mybusiness.com")

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if not v.startswith('+254') or not v[1:].isdigit() or len(v) != 13:
            raise ValueError('Phone number must be a valid Kenyan number starting with +254')
        return v

class MerchantCreate(BaseModel):
    user_id: str = Field(..., description="ID of the associated user account.")
    business_name: str = Field(..., min_length=3, max_length=100)
    business_email: EmailStr
    business_phone: str = Field(..., pattern=r"^\+254[1-9]\d{8}$", description="Kenyan phone number in international format (+254XXXXXXXXX)")

class MerchantResponse(BaseModel):
    """Schema for merchant details response"""
    id: str
    user_id: str
    business_name: str
    business_email: EmailStr
    business_phone: str
    status: MerchantStatus
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MerchantUpdate(BaseModel):
    business_name: Optional[str] = Field(None, min_length=3, max_length=100)
    business_email: Optional[EmailStr] = None
    business_phone: Optional[str] = Field(None, pattern=r"^\+254[1-9]\d{8}$")
    is_active: Optional[bool] = None

class MerchantSettings(BaseModel):
    # Example settings for a merchant
    callback_url: Optional[str] = Field(None, description="URL for receiving payment callbacks.")
    api_key: Optional[str] = Field(None, description="Merchant's API key for integration.")
    # Add more settings as needed

class PaymentLinkCreate(BaseModel):
    """Schema for creating a payment link"""
    amount: Decimal = Field(..., gt=0, decimal_places=2, example=500.00)
    currency: str = Field(..., example="KES", description="Currency for the payment link (e.g., KES, USDT)")
    description: Optional[str] = Field(None, max_length=255, example="Invoice #123 for services")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date for the link")

class PaymentLinkResponse(BaseModel):
    """Schema for payment link details response"""
    id: str
    merchant_id: str
    amount: Decimal
    currency: str
    description: Optional[str]
    link_url: str
    is_active: bool
    created_at: str # ISO format datetime string
    expires_at: Optional[str] # ISO format datetime string
