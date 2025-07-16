"""
Domain Value Objects for the Kenya Crypto-Fiat Payment Processor.
These are immutable objects representing core concepts like Money, Currency, Network, etc.
They enforce business rules and ensure data integrity.
"""
from decimal import Decimal, InvalidOperation
from enum import Enum
import re
import uuid

class Currency(Enum):
    """Supported currencies."""
    BTC = "BTC"
    USDT = "USDT"
    KES = "KES" # Kenyan Shilling
    USD = "USD" # United States Dollar (for internal conversion/reporting)

    def __str__(self):
        return self.value

class Network(Enum):
    """Supported blockchain networks."""
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum" # For ERC-20 USDT
    TRON = "tron" # For TRC-20 USDT

    def __str__(self):
        return self.value

class Money:
    """
    Value object for monetary amounts.
    Uses Decimal for precise financial calculations.
    """
    def __init__(self, amount: float | str | Decimal, currency: Currency):
        if not isinstance(currency, Currency):
            raise ValueError("Currency must be an instance of Currency enum.")
        try:
            self._amount = Decimal(str(amount))
        except InvalidOperation:
            raise ValueError("Invalid amount format.")
        if self._amount < 0:
            raise ValueError("Amount cannot be negative.")
        self._currency = currency

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def currency(self) -> Currency:
        return self._currency

    def __eq__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other):
        if not isinstance(other, Money) or self.currency != other.currency:
            raise TypeError("Cannot compare Money objects of different currencies or non-Money types.")
        return self.amount < other.amount

    def __le__(self, other):
        if not isinstance(other, Money) or self.currency != other.currency:
            raise TypeError("Cannot compare Money objects of different currencies or non-Money types.")
        return self.amount <= other.amount

    def __gt__(self, other):
        if not isinstance(other, Money) or self.currency != other.currency:
            raise TypeError("Cannot compare Money objects of different currencies or non-Money types.")
        return self.amount > other.amount

    def __ge__(self, other):
        if not isinstance(other, Money) or self.currency != other.currency:
            raise TypeError("Cannot compare Money objects of different currencies or non-Money types.")
        return self.amount >= other.amount

    def __add__(self, other):
        if not isinstance(other, Money) or self.currency != other.currency:
            raise TypeError("Cannot add Money objects of different currencies or non-Money types.")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other):
        if not isinstance(other, Money) or self.currency != other.currency:
            raise TypeError("Cannot subtract Money objects of different currencies or non-Money types.")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, other: float | int | Decimal):
        if not isinstance(other, (float, int, Decimal)):
            raise TypeError("Can only multiply Money by a numeric type.")
        return Money(self.amount * Decimal(str(other)), self.currency)

    def __truediv__(self, other: float | int | Decimal):
        if not isinstance(other, (float, int, Decimal)):
            raise TypeError("Can only divide Money by a numeric type.")
        if Decimal(str(other)) == 0:
            raise ValueError("Cannot divide by zero.")
        return Money(self.amount / Decimal(str(other)), self.currency)

    def __str__(self):
        return f"{self.amount.normalize()} {self.currency.value}"

    def __repr__(self):
        return f"Money(amount={self.amount.normalize()}, currency={self.currency.name})"

class PhoneNumber:
    """
    Value object for Kenyan phone numbers.
    Enforces international format (+254XXXXXXXXX).
    """
    KENYAN_PHONE_REGEX = r"^\+254[1-9]\d{8}$"

    def __init__(self, number: str):
        if not re.fullmatch(self.KENYAN_PHONE_REGEX, number):
            raise ValueError("Phone number must be a valid Kenyan number in international format (+254XXXXXXXXX).")
        self._number = number

    @property
    def number(self) -> str:
        return self._number

    def to_international_format(self) -> str:
        return self._number

    def to_safaricom_format(self) -> str:
        """Converts to 07XXXXXXXX format."""
        return "0" + self._number[4:]

    def __eq__(self, other):
        if not isinstance(other, PhoneNumber):
            return NotImplemented
        return self.number == other.number

    def __str__(self):
        return self.number

    def __repr__(self):
        return f"PhoneNumber(number='{self.number}')"

class WalletAddress:
    """
    Value object for blockchain wallet addresses.
    Includes network information for context.
    """
    def __init__(self, address: str, network: Network):
        if not isinstance(network, Network):
            raise ValueError("Network must be an instance of Network enum.")
        if not address or not isinstance(address, str):
            raise ValueError("Address cannot be empty and must be a string.")
        # Basic validation, more robust validation would involve checksums/regex per network
        self._address = address
        self._network = network

    @property
    def address(self) -> str:
        return self._address

    @property
    def network(self) -> Network:
        return self._network

    def __eq__(self, other):
        if not isinstance(other, WalletAddress):
            return NotImplemented
        return self.address == other.address and self.network == other.network

    def __str__(self):
        return f"{self.address} ({self.network.value})"

    def __repr__(self):
        return f"WalletAddress(address='{self.address}', network={self.network.name})"

class TransactionHash:
    """
    Value object for blockchain transaction hashes.
    Includes network information for context.
    """
    def __init__(self, hash: str, network: Network):
        if not isinstance(network, Network):
            raise ValueError("Network must be an instance of Network enum.")
        if not hash or not isinstance(hash, str) or len(hash) < 10: # Basic length check
            raise ValueError("Transaction hash cannot be empty and must be a string.")
        self._hash = hash
        self._network = network

    @property
    def hash(self) -> str:
        return self._hash

    @property
    def network(self) -> Network:
        return self._network

    def __eq__(self, other):
        if not isinstance(other, TransactionHash):
            return NotImplemented
        return self.hash == other.hash and self.network == other.network

    def __str__(self):
        return f"{self.hash} ({self.network.value})"

    def __repr__(self):
        return f"TransactionHash(hash='{self.hash}', network={self.network.name})"
