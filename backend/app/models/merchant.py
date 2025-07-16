"""
SQLAlchemy model for Merchant entity.
Defines attributes specific to merchant accounts.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.user import User # Import User model for relationship
from enum import Enum as PyEnum

class MerchantStatus(PyEnum):
    """Defines the status of a merchant account."""
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REJECTED = "rejected"

class Merchant(Base):
    """
    Represents a merchant account in the system.
    Each merchant is linked to a User.
    """
    __tablename__ = "merchants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False) # One-to-one with User
    
    business_name = Column(String, nullable=False)
    business_email = Column(String, unique=True, index=True, nullable=False)
    business_phone = Column(String, unique=True, index=True, nullable=False)
    
    status = Column(Enum(MerchantStatus), default=MerchantStatus.PENDING_APPROVAL, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="merchant", uselist=False) # One-to-one relationship

    def __repr__(self):
        return f"<Merchant(id={self.id}, business_name='{self.business_name}', status='{self.status.value}')>"
