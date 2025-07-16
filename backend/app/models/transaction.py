"""
SQLAlchemy model for Transaction entity.
Records all financial movements within the system.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.user import User # Import User model for relationship
from enum import Enum as PyEnum
from decimal import Decimal

class TransactionType(PyEnum):
    """Defines the type of financial transaction."""
    CRYPTO_DEPOSIT = "crypto_deposit"
    CRYPTO_WITHDRAWAL = "crypto_withdrawal"
    FIAT_DEPOSIT = "fiat_deposit" # M-Pesa deposit
    FIAT_WITHDRAWAL = "fiat_withdrawal" # M-Pesa withdrawal
    CRYPTO_EXCHANGE = "crypto_exchange" # Crypto to Crypto
    FIAT_EXCHANGE = "fiat_exchange" # Fiat to Fiat (e.g., KES to USD)
    CRYPTO_TO_FIAT = "crypto_to_fiat"
    FIAT_TO_CRYPTO = "fiat_to_crypto"
    FEE = "fee"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"

class TransactionStatus(PyEnum):
    """Defines the current status of a transaction."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"
    CONFIRMING = "confirming" # For crypto transactions awaiting confirmations

class Transaction(Base):
    """
    Represents a financial transaction in the system.
    Uses Numeric type for amounts to ensure precision.
    """
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    transaction_type = Column(Enum(TransactionType), nullable=False)
    
    # Financial details
    amount = Column(Numeric(precision=18, scale=8), nullable=False) # Precision for crypto
    currency = Column(String, nullable=False) # E.g., "BTC", "USDT", "KES"
    
    # Status and timestamps
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True)) # For payments with a time limit

    # External references (e.g., blockchain hash, M-Pesa CheckoutRequestID/Receipt)
    blockchain_hash = Column(String, unique=True, index=True) # For crypto transactions
    network = Column(String) # E.g., "bitcoin", "ethereum", "tron"
    confirmations = Column(Integer, default=0) # For crypto transactions

    mpesa_phone = Column(String) # Phone number for M-Pesa transactions
    mpesa_reference = Column(String, unique=True, index=True) # M-Pesa CheckoutRequestID
    mpesa_receipt = Column(String, unique=True, index=True) # M-Pesa Receipt Number

    # Additional details
    notes = Column(String)
    failure_reason = Column(String)
    metadata_json = Column(JSONB) # For storing arbitrary JSON metadata

    # Relationships
    user = relationship("User", backref="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, type='{self.transaction_type.value}', amount={self.amount} {self.currency}, status='{self.status.value}')>"
