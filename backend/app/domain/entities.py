"""
Domain Entities for the Kenya Crypto-Fiat Payment Processor.
These are mutable objects with an identity, representing core business concepts.
They encapsulate business logic and state.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from app.domain.value_objects import Money, Currency, Network, PhoneNumber, WalletAddress, TransactionHash
from enum import Enum as PyEnum

class PaymentType(PyEnum):
    """Defines the type of payment operation."""
    CRYPTO_DEPOSIT = "crypto_deposit"
    CRYPTO_WITHDRAWAL = "crypto_withdrawal"
    MPESA_DEPOSIT = "mpesa_deposit"
    MPESA_WITHDRAWAL = "mpesa_withdrawal"
    EXCHANGE = "exchange" # Crypto-to-fiat, fiat-to-crypto, crypto-to-crypto

class PaymentStatus(PyEnum):
    """Defines the status of a payment request/transaction."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    CONFIRMING = "confirming" # For crypto transactions awaiting confirmations

class PaymentRequest:
    """
    Represents a request for a payment (e.g., a user wants to deposit BTC).
    This is a domain entity that captures the intent and initial state.
    """
    def __init__(
        self,
        amount: Money,
        payment_type: PaymentType,
        network: Optional[Network] = None,
        phone_number: Optional[PhoneNumber] = None,
        description: Optional[str] = None,
        expires_in_minutes: int = 30 # Default expiration for payment requests
    ):
        if not isinstance(amount, Money):
            raise ValueError("Amount must be a Money object.")
        if not isinstance(payment_type, PaymentType):
            raise ValueError("Payment type must be a PaymentType enum.")
        
        if payment_type in [PaymentType.CRYPTO_DEPOSIT, PaymentType.CRYPTO_WITHDRAWAL]:
            if not network:
                raise ValueError("Network is required for crypto payments.")
            if not isinstance(network, Network):
                raise ValueError("Network must be a Network enum.")
        elif payment_type in [PaymentType.MPESA_DEPOSIT, PaymentType.MPESA_WITHDRAWAL]:
            if not phone_number:
                raise ValueError("Phone number is required for M-Pesa payments.")
            if not isinstance(phone_number, PhoneNumber):
                raise ValueError("Phone number must be a PhoneNumber object.")
            if amount.currency != Currency.KES:
                raise ValueError("M-Pesa payments must be in KES.")

        self._id = uuid.uuid4()
        self._amount = amount
        self._payment_type = payment_type
        self._network = network
        self._phone_number = phone_number
        self._description = description
        self._created_at = datetime.utcnow()
        self._expires_at = self._created_at + timedelta(minutes=expires_in_minutes)
        self._status = PaymentStatus.PENDING

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def amount(self) -> Money:
        return self._amount

    @property
    def payment_type(self) -> PaymentType:
        return self._payment_type

    @property
    def network(self) -> Optional[Network]:
        return self._network

    @property
    def phone_number(self) -> Optional[PhoneNumber]:
        return self._phone_number

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def expires_at(self) -> datetime:
        return self._expires_at

    @property
    def status(self) -> PaymentStatus:
        return self._status

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def update_status(self, new_status: PaymentStatus):
        if not isinstance(new_status, PaymentStatus):
            raise ValueError("New status must be a PaymentStatus enum.")
        self._status = new_status

    def __repr__(self):
        return f"PaymentRequest(id={self.id}, type={self.payment_type.name}, amount={self.amount}, status={self.status.name})"
