"""
User model definition
Includes user authentication details, roles, and KYC status
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class UserRole(PyEnum):
    """Defines user roles within the system."""
    CUSTOMER = "customer"
    MERCHANT = "merchant"
    ADMIN = "admin"

class KYCStatus(PyEnum):
    """Defines the Know Your Customer (KYC) verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REQUIRED = "required" # Initial state for new users

class User(Base):
    """
    Represents a user in the system.
    Can be a customer, merchant, or admin.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False) # E.g., +2547XXXXXXXX
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    
    # User status and roles
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False) # Email/phone verification
    kyc_status = Column(Enum(KYCStatus), default=KYCStatus.REQUIRED, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Security features
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    lockout_until = Column(DateTime(timezone=True))

    # Relationships
    wallets = relationship("Wallet", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"
