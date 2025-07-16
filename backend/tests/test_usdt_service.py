"""
Unit tests for the USDTService.
Tests address generation, transaction info retrieval, and address validation for ERC-20 and TRC-20.
"""
import pytest
from app.services.usdt_service import USDTService
from app.domain.value_objects import WalletAddress, Network, TransactionHash, Currency
from app.core.exceptions import BlockchainError

@pytest.mark.asyncio
async def test_generate_deposit_address_ethereum():
    """Test successful ERC-20 USDT address generation."""
    service = USDTService()
    user_id = "test_user_erc20"
    address = await service.generate_deposit_address(user_id, Network.ETHEREUM)
    
    assert isinstance(address, WalletAddress)
    assert address.network == Network.ETHEREUM
    assert address.address.startswith("0x")
    assert len(address.address) == 42 # Standard Ethereum address length

@pytest.mark.asyncio
async def test_generate_deposit_address_tron():
    """Test successful TRC-20 USDT address generation."""
    service = USDTService()
    user_id = "test_user_trc20"
    address = await service.generate_deposit_address(user_id, Network.TRON)
    
    assert isinstance(address, WalletAddress)
    assert address.network == Network.TRON
    assert address.address.startswith("T")
    assert len(address.address) == 34 # Standard Tron address length

@pytest.mark.asyncio
async def test_generate_deposit_address_unsupported_network():
    """Test USDT address generation for an unsupported network."""
    service = USDTService()
    user_id = "test_user_unsupported"
    with pytest.raises(BlockchainError, match="Unsupported network for USDT: bitcoin"):
        await service.generate_deposit_address(user_id, Network.BITCOIN)

@pytest.mark.asyncio
async def test_get_transaction_info_ethereum_success():
    """Test successful retrieval of ERC-20 USDT transaction info."""
    service = USDTService()
    mock_tx_hash = TransactionHash(hash="0x" + "a" * 40, network=Network.ETHEREUM)
    info = await service.get_transaction_info(mock_tx_hash)
    
    assert isinstance(info, dict)
    assert info["hash"] == mock_tx_hash.hash
    assert info["network"] == Network.ETHEREUM.value
    assert info["currency"] == Currency.USDT.value
    assert info["confirmations"] >= 0
    assert "amount" in info
    assert "status" in info

@pytest.mark.asyncio
async def test_get_transaction_info_tron_success():
    """Test successful retrieval of TRC-20 USDT transaction info."""
    service = USDTService()
    mock_tx_hash = TransactionHash(hash="T" + "b" * 33, network=Network.TRON)
    info = await service.get_transaction_info(mock_tx_hash)
    
    assert isinstance(info, dict)
    assert info["hash"] == mock_tx_hash.hash
    assert info["network"] == Network.TRON.value
    assert info["currency"] == Currency.USDT.value
    assert info["confirmations"] >= 0
    assert "amount" in info
    assert "status" in info

@pytest.mark.asyncio
async def test_get_transaction_info_unsupported_network():
    """Test fetching USDT transaction info for an unsupported network."""
    service = USDTService()
    mock_tx_hash = TransactionHash(hash="c" * 64, network=Network.BITCOIN)
    with pytest.raises(BlockchainError, match="Unsupported network for USDT transaction hash: bitcoin"):
        await service.get_transaction_info(mock_tx_hash)

@pytest.mark.asyncio
async def test_validate_address_ethereum_valid():
    """Test validation of a valid ERC-20 USDT address."""
    service = USDTService()
    valid_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f444"
    assert await service.validate_address(valid_address, Network.ETHEREUM) is True

@pytest.mark.asyncio
async def test_validate_address_ethereum_invalid():
    """Test validation of an invalid ERC-20 USDT address."""
    service = USDTService()
    invalid_addresses = [
        "0x123", # Too short
        "0x742d35Cc6634C0532925a3b844Bc454e4438f4445", # Too long
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", # Bitcoin address
        "T1234567890abcdef1234567890abcdef1234", # Tron address
        "invalid_address",
        "",
        None
    ]
    for addr in invalid_addresses:
        assert await service.validate_address(addr, Network.ETHEREUM) is False

@pytest.mark.asyncio
async def test_validate_address_tron_valid():
    """Test validation of a valid TRC-20 USDT address."""
    service = USDTService()
    valid_address = "TJRyY1234567890abcdef1234567890abcdef1234"
    assert await service.validate_address(valid_address, Network.TRON) is True

@pytest.mark.asyncio
async def test_validate_address_tron_invalid():
    """Test validation of an invalid TRC-20 USDT address."""
    service = USDTService()
    invalid_addresses = [
        "T123", # Too short
        "TJRyY1234567890abcdef1234567890abcdef12345", # Too long
        "0x742d35Cc6634C0532925a3b844Bc454e4438f444", # Ethereum address
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", # Bitcoin address
        "invalid_address",
        "",
        None
    ]
    for addr in invalid_addresses:
        assert await service.validate_address(addr, Network.TRON) is False
