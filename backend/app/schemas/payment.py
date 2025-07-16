"""
Pydantic schemas for payment-related data.
Defines data structures for initiating payments, status checks, and history.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from app.domain.value_objects import Currency, Network # Import enums from domain
from app.models.transaction import TransactionStatus, TransactionType # Import enums from models

class PaymentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=8, description="Amount to be paid. Max 8 decimal places for crypto.")
    currency: Currency = Field(..., description="Currency of the payment (e.g., BTC, USDT, KES).")
    description: Optional[str] = Field(None, max_length=255, description="Optional description for the payment.")

class CryptoPaymentRequest(PaymentRequest):
    currency: Currency = Field(..., description="Crypto currency (BTC, USDT).")
    network: Optional[Network] = Field(None, description="Blockchain network (e.g., BITCOIN, ETHEREUM, TRON). Required for USDT.")

class MpesaPaymentRequest(PaymentRequest):
    currency: Currency = Field(Currency.KES, description="M-Pesa payments must be in KES.")
    phone: str = Field(..., pattern=r"^\+254[1-9]\d{8}$", description="Kenyan phone number in international format (+254XXXXXXXXX).")

class PaymentResponse(BaseModel):
    transaction_id: str
    status: str # Use string for status for now, will map to TransactionStatus enum
    amount: Decimal
    currency: str
    payment_address: Optional[str] = Field(None, description="Crypto deposit address.")
    qr_code: Optional[str] = Field(None, description="QR code data for crypto payment.")
    expires_at: Optional[str] = Field(None, description="ISO formatted datetime when payment request expires.")
    instructions: Optional[str] = Field(None, description="Human-readable payment instructions.")

class PaymentStatus(BaseModel):
    transaction_id: str
    status: TransactionStatus
    amount: Decimal
    currency: str
    confirmations: Optional[int] = Field(0, description="Number of blockchain confirmations (for crypto).")
    blockchain_hash: Optional[str] = Field(None, description="Blockchain transaction hash (for crypto).")
    created_at: datetime
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    
    class Config:
        from_attributes = True

class PaymentHistoryEntry(BaseModel):
    id: str
    type: TransactionType
    amount: Decimal
    currency: str
    status: TransactionStatus
    network: Optional[str] = None
    blockchain_hash: Optional[str] = None
    confirmations: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

# M-Pesa Callback Schemas (simplified for example)
class MpesaCallbackItem(BaseModel):
    Name: str
    Value: Optional[str] = None

class MpesaCallbackMetadata(BaseModel):
    Item: List[MpesaCallbackItem]

class MpesaStkCallback(BaseModel):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: int
    ResultDesc: str
    CallbackMetadata: Optional[MpesaCallbackMetadata] = None

class MpesaCallback(BaseModel):
    Body: MpesaStkCallback # M-Pesa sends the STKCallback object nested under 'Body'
