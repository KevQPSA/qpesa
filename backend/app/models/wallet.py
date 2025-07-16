"""
SQLAlchemy model for Wallet entity.
Represents a user's internal crypto or fiat wallet.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.user import User # Import User model for relationship
from enum import Enum as PyEnum
from decimal import Decimal

class WalletType(PyEnum):
    """Defines the type of wallet."""
    CRYPTO = "crypto"
    FIAT = "fiat"

class Wallet(Base):
    """
    Represents a user's internal wallet for a specific currency.
    """
    __tablename__ = "wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    currency = Column(String, nullable=False) # E.g., "BTC", "USDT", "KES"
    balance = Column(Numeric(precision=18, scale=8), default=Decimal('0.0'), nullable=False)
    wallet_type = Column(Enum(WalletType), nullable=False)
    
    # For crypto wallets, might store a derived address or xpub
    # For fiat, might store M-Pesa account details (though usually handled by M-Pesa service)
    address = Column(String, unique=True, index=True) # For crypto deposit addresses
    
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="wallets")

    __table_args__ = (
        UniqueConstraint('user_id', 'currency', name='_user_currency_uc'),
    )

    def __repr__(self):
        return f"<Wallet(id={self.id}, user_id={self.user_id}, currency='{self.currency}', balance={self.balance})>"
