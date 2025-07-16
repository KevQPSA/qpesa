"""
Unit tests for domain value objects (Money, Currency, Network, PhoneNumber, WalletAddress, TransactionHash).
Ensures immutability, validation, and correct behavior.
"""
import pytest
from decimal import Decimal, InvalidOperation
from app.domain.value_objects import Money, Currency, Network, PhoneNumber, WalletAddress, TransactionHash

# --- Money Value Object Tests ---

def test_money_creation_valid():
    """Test valid Money object creation."""
    m1 = Money(100.50, Currency.KES)
    assert m1.amount == Decimal('100.50')
    assert m1.currency == Currency.KES

    m2 = Money("0.00000001", Currency.BTC)
    assert m2.amount == Decimal('0.00000001')
    assert m2.currency == Currency.BTC

    m3 = Money(Decimal('25.75'), Currency.USDT)
    assert m3.amount == Decimal('25.75')
    assert m3.currency == Currency.USDT

def test_money_creation_invalid_amount():
    """Test Money creation with invalid amount."""
    with pytest.raises(ValueError, match="Invalid amount format."):
        Money("abc", Currency.KES)
    with pytest.raises(ValueError, match="Amount cannot be negative."):
        Money(-10, Currency.KES)

def test_money_creation_invalid_currency():
    """Test Money creation with invalid currency type."""
    with pytest.raises(ValueError, match="Currency must be an instance of Currency enum."):
        Money(100, "KES") # type: ignore

def test_money_equality():
    """Test equality comparison for Money objects."""
    m1 = Money(100, Currency.KES)
    m2 = Money(100.00, Currency.KES)
    m3 = Money(100, Currency.BTC)
    m4 = Money(200, Currency.KES)

    assert m1 == m2
    assert m1 != m3
    assert m1 != m4
    assert m1 != 100 # Not equal to non-Money type

def test_money_comparison_same_currency():
    """Test comparison operators for Money objects of the same currency."""
    m1 = Money(100, Currency.KES)
    m2 = Money(200, Currency.KES)
    m3 = Money(100, Currency.KES)

    assert m1 < m2
    assert m2 > m1
    assert m1 <= m3
    assert m1 >= m3
    assert m1 <= m2
    assert m2 >= m1

def test_money_comparison_different_currency():
    """Test comparison operators for Money objects of different currencies."""
    m1 = Money(100, Currency.KES)
    m2 = Money(100, Currency.BTC)
    with pytest.raises(TypeError, match="Cannot compare Money objects of different currencies"):
        assert m1 < m2

def test_money_addition():
    """Test addition of Money objects."""
    m1 = Money(50, Currency.KES)
    m2 = Money(75.50, Currency.KES)
    result = m1 + m2
    assert result.amount == Decimal('125.50')
    assert result.currency == Currency.KES

def test_money_addition_different_currency():
    """Test addition of Money objects with different currencies."""
    m1 = Money(50, Currency.KES)
    m2 = Money(75, Currency.BTC)
    with pytest.raises(TypeError, match="Cannot add Money objects of different currencies"):
        m1 + m2

def test_money_subtraction():
    """Test subtraction of Money objects."""
    m1 = Money(100, Currency.KES)
    m2 = Money(25.50, Currency.KES)
    result = m1 - m2
    assert result.amount == Decimal('74.50')
    assert result.currency == Currency.KES

def test_money_subtraction_different_currency():
    """Test subtraction of Money objects with different currencies."""
    m1 = Money(100, Currency.KES)
    m2 = Money(25, Currency.BTC)
    with pytest.raises(TypeError, match="Cannot subtract Money objects of different currencies"):
        m1 - m2

def test_money_multiplication():
    """Test multiplication of Money objects by a numeric value."""
    m1 = Money(10, Currency.KES)
    result = m1 * 2.5
    assert result.amount == Decimal('25.0')
    assert result.currency == Currency.KES

    result = m1 * Decimal('3')
    assert result.amount == Decimal('30.0')
    assert result.currency == Currency.KES

def test_money_multiplication_invalid_type():
    """Test multiplication of Money objects by an invalid type."""
    m1 = Money(10, Currency.KES)
    with pytest.raises(TypeError, match="Can only multiply Money by a numeric type."):
        m1 * "abc" # type: ignore

def test_money_division():
    """Test division of Money objects by a numeric value."""
    m1 = Money(100, Currency.KES)
    result = m1 / 4
    assert result.amount == Decimal('25.0')
    assert result.currency == Currency.KES

    result = m1 / Decimal('2.5')
    assert result.amount == Decimal('40.0')
    assert result.currency == Currency.KES

def test_money_division_by_zero():
    """Test division of Money objects by zero."""
    m1 = Money(100, Currency.KES)
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        m1 / 0

def test_money_division_invalid_type():
    """Test division of Money objects by an invalid type."""
    m1 = Money(100, Currency.KES)
    with pytest.raises(TypeError, match="Can only divide Money by a numeric type."):
        m1 / "abc" # type: ignore

def test_money_string_representation():
    """Test string representation of Money objects."""
    m1 = Money(100.50, Currency.KES)
    assert str(m1) == "100.50 KES"
    m2 = Money(Decimal('0.00000001'), Currency.BTC)
    assert str(m2) == "0.00000001 BTC"
    m3 = Money(100.00, Currency.USD)
    assert str(m3) == "100 USD"

# --- PhoneNumber Value Object Tests ---

def test_phone_number_creation_valid():
    """Test valid PhoneNumber object creation."""
    p1 = PhoneNumber("+254712345678")
    assert p1.number == "+254712345678"

    p2 = PhoneNumber("+254111222333")
    assert p2.number == "+254111222333"

def test_phone_number_creation_invalid():
    """Test invalid PhoneNumber object creation."""
    with pytest.raises(ValueError, match="Phone number must be a valid Kenyan number"):
        PhoneNumber("0712345678") # Missing +254
    with pytest.raises(ValueError, match="Phone number must be a valid Kenyan number"):
        PhoneNumber("+1234567890") # Not Kenyan
    with pytest.raises(ValueError, match="Phone number must be a valid Kenyan number"):
        PhoneNumber("+25471234567") # Too short
    with pytest.raises(ValueError, match="Phone number must be a valid Kenyan number"):
        PhoneNumber("+2547123456789") # Too long
    with pytest.raises(ValueError, match="Phone number must be a valid Kenyan number"):
        PhoneNumber("invalid")

def test_phone_number_formats():
    """Test different format conversions for PhoneNumber."""
    p = PhoneNumber("+254722334455")
    assert p.to_international_format() == "+254722334455"
    assert p.to_safaricom_format() == "0722334455"

def test_phone_number_equality():
    """Test equality comparison for PhoneNumber objects."""
    p1 = PhoneNumber("+254711223344")
    p2 = PhoneNumber("+254711223344")
    p3 = PhoneNumber("+254711223355")

    assert p1 == p2
    assert p1 != p3
    assert p1 != "+254711223344" # Not equal to non-PhoneNumber type

# --- WalletAddress Value Object Tests ---

def test_wallet_address_creation_valid():
    """Test valid WalletAddress object creation."""
    w1 = WalletAddress("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", Network.BITCOIN)
    assert w1.address == "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    assert w1.network == Network.BITCOIN

    w2 = WalletAddress("0xAbc1234567890aBc1234567890aBc1234567890a", Network.ETHEREUM)
    assert w2.address == "0xAbc1234567890aBc1234567890aBc1234567890a"
    assert w2.network == Network.ETHEREUM

def test_wallet_address_creation_invalid():
    """Test WalletAddress creation with invalid inputs."""
    with pytest.raises(ValueError, match="Network must be an instance of Network enum."):
        WalletAddress("address", "bitcoin") # type: ignore
    with pytest.raises(ValueError, match="Address cannot be empty and must be a string."):
        WalletAddress("", Network.BITCOIN)
    with pytest.raises(ValueError, match="Address cannot be empty and must be a string."):
        WalletAddress(None, Network.BITCOIN) # type: ignore

def test_wallet_address_equality():
    """Test equality comparison for WalletAddress objects."""
    w1 = WalletAddress("addr1", Network.BITCOIN)
    w2 = WalletAddress("addr1", Network.BITCOIN)
    w3 = WalletAddress("addr2", Network.BITCOIN)
    w4 = WalletAddress("addr1", Network.ETHEREUM)

    assert w1 == w2
    assert w1 != w3
    assert w1 != w4
    assert w1 != "addr1" # Not equal to non-WalletAddress type

# --- TransactionHash Value Object Tests ---

def test_transaction_hash_creation_valid():
    """Test valid TransactionHash object creation."""
    t1 = TransactionHash("a" * 64, Network.BITCOIN)
    assert t1.hash == "a" * 64
    assert t1.network == Network.BITCOIN

    t2 = TransactionHash("0x" + "b" * 40, Network.ETHEREUM)
    assert t2.hash == "0x" + "b" * 40
    assert t2.network == Network.ETHEREUM

def test_transaction_hash_creation_invalid():
    """Test TransactionHash creation with invalid inputs."""
    with pytest.raises(ValueError, match="Network must be an instance of Network enum."):
        TransactionHash("hash", "ethereum") # type: ignore
    with pytest.raises(ValueError, match="Transaction hash cannot be empty and must be a string."):
        TransactionHash("", Network.BITCOIN)
    with pytest.raises(ValueError, match="Transaction hash cannot be empty and must be a string."):
        TransactionHash("short", Network.BITCOIN) # Too short
    with pytest.raises(ValueError, match="Transaction hash cannot be empty and must be a string."):
        TransactionHash(None, Network.BITCOIN) # type: ignore

def test_transaction_hash_equality():
    """Test equality comparison for TransactionHash objects."""
    t1 = TransactionHash("hash1", Network.BITCOIN)
    t2 = TransactionHash("hash1", Network.BITCOIN)
    t3 = TransactionHash("hash2", Network.BITCOIN)
    t4 = TransactionHash("hash1", Network.ETHEREUM)

    assert t1 == t2
    assert t1 != t3
    assert t1 != t4
    assert t1 != "hash1" # Not equal to non-TransactionHash type
