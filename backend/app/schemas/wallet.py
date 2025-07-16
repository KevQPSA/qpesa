"""
Pydantic schemas for wallet-related data.
Defines data structures for wallet creation, balance, and history.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from app.models.wallet import WalletType # Import enum from models

class WalletCreate(BaseModel):
    currency: str = Field(..., min_length=2, max_length=10, description="Currency code (e.g., BTC, KES, USDT).")
    wallet_type: WalletType = Field(..., description="Type of wallet (crypto or fiat).")
    address: Optional[str] = Field(None, description="Optional deposit address for crypto wallets.")

class WalletResponse(BaseModel):
    id: str
    user_id: str
    currency: str
    balance: Decimal = Field(..., decimal_places=8)
    wallet_type: WalletType
    address: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WalletBalanceUpdate(BaseModel):
    amount: Decimal = Field(..., description="Amount to add or subtract from balance.")
    transaction_type: str = Field(..., description="Type of transaction (e.g., 'deposit', 'withdrawal').")
    reference_id: Optional[str] = Field(None, description="Reference ID for the transaction.")

class WalletHistoryEntry(BaseModel):
    transaction_id: str
    type: str
    amount: Decimal
    currency: str
    balance_after: Decimal
    created_at: datetime
    description: Optional[str] = None

    class Config:
        from_attributes = True
