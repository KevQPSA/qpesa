"""
Comprehensive tests for Bitcoin service
Tests wallet generation, transactions, and monitoring
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import httpx

from app.services.bitcoin_service import BitcoinService
from app.domain.value_objects import Money, WalletAddress, TransactionHash, Currency, Network
from app.domain.entities import CryptoWallet, TransactionRecord, PaymentStatus
from app.core.exceptions import BlockchainError, ValidationError

@pytest.fixture
def bitcoin_service():
    """Create Bitcoin service instance for testing"""
    with patch('app.services.bitcoin_service.settings') as mock_settings:
        mock_settings.BITCOIN_RPC_URL = "http://test:test@localhost:8332"
        mock_settings.BTC_CONFIRMATIONS_REQUIRED = 3
        mock_settings.ENCRYPTION_KEY = "test-encryption-key-32-characters"
        
        service = BitcoinService()
        return service

@pytest.fixture
def mock_rpc_response():
    """Mock RPC response data"""
    return {
        "result": {
            "balance": 0.5,
            "confirmations": 6,
            "txid": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890"
        }
    }

class TestBitcoinService:
    """Test suite for Bitcoin service"""
    
    @pytest.mark.asyncio
    async def test_generate_wallet_address_success(self, bitcoin_service):
        """Test successful wallet address generation"""
        user_id = "test-user-123"
        
        with patch('app.services.bitcoin_service.HDKey') as mock_hdkey:
            # Mock HD key generation
            mock_master = MagicMock()
            mock_child = MagicMock()
            mock_child.address.return_value = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
            mock_child.wif.return_value = "L1aW4aubDFB7yfras2S1mN3bqg9nwySY8nkoLmJebSLD5BWv3ENZ"
            mock_master.child_private.return_value = mock_child
            mock_hdkey.return_value = mock_master
            
            # Generate wallet
            wallet = await bitcoin_service.generate_wallet_address(user_id)
            
            # Assertions
            assert isinstance(wallet, CryptoWallet)
            assert wallet.user_id == user_id
            assert wallet.currency == Currency.BTC
            assert wallet.address.address == "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
            assert wallet.address.network == "bitcoin"
            assert wallet.balance.amount == Decimal('0')
            assert wallet.encrypted_private_key is not None
    
    @pytest.mark.asyncio
    async def test_generate_wallet_address_failure(self, bitcoin_service):
        """Test wallet generation failure handling"""
        user_id = "test-user-123"
        
        with patch('app.services.bitcoin_service.HDKey', side_effect=Exception("Key generation failed")):
            with pytest.raises(BlockchainError) as exc_info:
                await bitcoin_service.generate_wallet_address(user_id)
            
            assert "Failed to generate Bitcoin wallet" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_address_balance_success(self, bitcoin_service):
        """Test successful balance retrieval"""
        address = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        
        # Mock RPC response
        mock_utxos = [
            {"amount": 0.3, "confirmations": 6},
            {"amount": 0.2, "confirmations": 3}
        ]
        
        with patch.object(bitcoin_service, '_rpc_call', return_value=mock_utxos):
            balance = await bitcoin_service.get_address_balance(address)
            
            assert isinstance(balance, Money)
            assert balance.currency == Currency.BTC
            assert balance.amount == Decimal('0.5')
    
    @pytest.mark.asyncio
    async def test_get_address_balance_empty(self, bitcoin_service):
        """Test balance retrieval for empty address"""
        address = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        
        with patch.object(bitcoin_service, '_rpc_call', return_value=[]):
            balance = await bitcoin_service.get_address_balance(address)
            
            assert balance.amount == Decimal('0')
            assert balance.currency == Currency.BTC
    
    @pytest.mark.asyncio
    async def test_get_address_balance_rpc_error(self, bitcoin_service):
        """Test balance retrieval with RPC error"""
        address = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        
        with patch.object(bitcoin_service, '_rpc_call', side_effect=BlockchainError("RPC failed")):
            with pytest.raises(BlockchainError):
                await bitcoin_service.get_address_balance(address)
    
    @pytest.mark.asyncio
    async def test_estimate_transaction_fee_success(self, bitcoin_service):
        """Test successful fee estimation"""
        from_address = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        to_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        amount = Money(Decimal('0.1'), Currency.BTC)
        
        # Mock fee rate response
        mock_fee_response = {"feerate": 0.00001}
        
        with patch.object(bitcoin_service, '_rpc_call', return_value=mock_fee_response):
            fee = await bitcoin_service.estimate_transaction_fee(from_address, to_address, amount)
            
            assert isinstance(fee, Money)
            assert fee.currency == Currency.BTC
            assert fee.amount > Decimal('0')
    
    @pytest.mark.asyncio
    async def test_estimate_transaction_fee_fallback(self, bitcoin_service):
        """Test fee estimation with fallback when RPC fails"""
        from_address = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        to_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        amount = Money(Decimal('0.1'), Currency.BTC)
        
        # Mock RPC failure
        with patch.object(bitcoin_service, '_rpc_call', side_effect=Exception("RPC failed")):
            fee = await bitcoin_service.estimate_transaction_fee(from_address, to_address, amount)
            
            assert isinstance(fee, Money)
            assert fee.currency == Currency.BTC
            assert fee.amount == Decimal('0.0001')  # Fallback fee
    
    @pytest.mark.asyncio
    async def test_send_transaction_success(self, bitcoin_service):
        """Test successful Bitcoin transaction"""
        # Create mock wallet
        user_id = "test-user-123"
        wallet_address = WalletAddress("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", "bitcoin")
        
        from app.domain.value_objects import EncryptedPrivateKey
        encrypted_key = EncryptedPrivateKey.encrypt(
            "L1aW4aubDFB7yfras2S1mN3bqg9nwySY8nkoLmJebSLD5BWv3ENZ",
            b"test-encryption-key-32-characters"
        )
        
        wallet = CryptoWallet(
            user_id=user_id,
            currency=Currency.BTC,
            address=wallet_address,
            encrypted_private_key=encrypted_key,
            balance=Money(Decimal('1.0'), Currency.BTC)
        )
        
        to_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        amount = Money(Decimal('0.1'), Currency.BTC)
        fee = Money(Decimal('0.0001'), Currency.BTC)
        
        # Mock RPC calls
        mock_utxos = [
            {
                "txid": "prev_tx_hash",
                "vout": 0,
                "amount": 1.0,
                "confirmations": 6
            }
        ]
        
        mock_responses = {
            "listunspent": mock_utxos,
            "createrawtransaction": "raw_tx_hex",
            "signrawtransactionwithkey": {"hex": "signed_tx_hex", "complete": True},
            "sendrawtransaction": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890"
        }
        
        async def mock_rpc_call(method, params=None):
            return mock_responses.get(method, {})
        
        with patch.object(bitcoin_service, '_rpc_call', side_effect=mock_rpc_call):
            transaction = await bitcoin_service.send_transaction(wallet, to_address, amount, fee)
            
            assert isinstance(transaction, TransactionRecord)
            assert transaction.user_id == user_id
            assert transaction.amount == amount
            assert transaction.fee == fee
            assert transaction.status == PaymentStatus.PENDING
            assert transaction.transaction_hash.hash == "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890"
    
    @pytest.mark.asyncio
    async def test_send_transaction_insufficient_balance(self, bitcoin_service):
        """Test transaction with insufficient balance"""
        user_id = "test-user-123"
        wallet_address = WalletAddress("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", "bitcoin")
        
        from app.domain.value_objects import EncryptedPrivateKey
        encrypted_key = EncryptedPrivateKey.encrypt(
            "L1aW4aubDFB7yfras2S1mN3bqg9nwySY8nkoLmJebSLD5BWv3ENZ",
            b"test-encryption-key-32-characters"
        )
        
        wallet = CryptoWallet(
            user_id=user_id,
            currency=Currency.BTC,
            address=wallet_address,
            encrypted_private_key=encrypted_key,
            balance=Money(Decimal('0.05'), Currency.BTC)  # Insufficient balance
        )
        
        to_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        amount = Money(Decimal('0.1'), Currency.BTC)
        fee = Money(Decimal('0.0001'), Currency.BTC)
        
        with pytest.raises(ValidationError) as exc_info:
            await bitcoin_service.send_transaction(wallet, to_address, amount, fee)
        
        assert "Insufficient balance" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_send_transaction_invalid_currency(self, bitcoin_service):
        """Test transaction with invalid currency"""
        user_id = "test-user-123"
        wallet_address = WalletAddress("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", "bitcoin")
        
        from app.domain.value_objects import EncryptedPrivateKey
        encrypted_key = EncryptedPrivateKey.encrypt(
            "L1aW4aubDFB7yfras2S1mN3bqg9nwySY8nkoLmJebSLD5BWv3ENZ",
            b"test-encryption-key-32-characters"
        )
        
        wallet = CryptoWallet(
            user_id=user_id,
            currency=Currency.BTC,
            address=wallet_address,
            encrypted_private_key=encrypted_key,
            balance=Money(Decimal('1.0'), Currency.BTC)
        )
        
        to_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        amount = Money(Decimal('100'), Currency.USDT)  # Wrong currency
        fee = Money(Decimal('0.0001'), Currency.BTC)
        
        with pytest.raises(ValidationError) as exc_info:
            await bitcoin_service.send_transaction(wallet, to_address, amount, fee)
        
        assert "Amount and fee must be in BTC" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_transaction_status_confirmed(self, bitcoin_service):
        """Test getting status of confirmed transaction"""
        tx_hash = "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890"
        
        mock_tx_info = {
            "confirmations": 6,
            "blockhash": "block_hash_123"
        }
        
        mock_block_info = {
            "height": 700000
        }
        
        async def mock_rpc_call(method, params=None):
            if method == "gettransaction":
                return mock_tx_info
            elif method == "getblock":
                return mock_block_info
            return {}
        
        with patch.object(bitcoin_service, '_rpc_call', side_effect=mock_rpc_call):
            status = await bitcoin_service.get_transaction_status(tx_hash)
            
            assert status['confirmations'] == 6
            assert status['block_number'] == 700000
            assert status['status'] == 'confirmed'
    
    @pytest.mark.asyncio
    async def test_get_transaction_status_pending(self, bitcoin_service):
        """Test getting status of pending transaction"""
        tx_hash = "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890"
        
        mock_tx_info = {
            "confirmations": 1  # Below minimum confirmations
        }
        
        with patch.object(bitcoin_service, '_rpc_call', return_value=mock_tx_info):
            status = await bitcoin_service.get_transaction_status(tx_hash)
            
            assert status['confirmations'] == 1
            assert status['status'] == 'pending'
    
    @pytest.mark.asyncio
    async def test_validate_address_valid(self, bitcoin_service):
        """Test validation of valid Bitcoin address"""
        address = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        
        mock_response = {"isvalid": True}
        
        with patch.object(bitcoin_service, '_rpc_call', return_value=mock_response):
            is_valid = await bitcoin_service.validate_address(address)
            
            assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_address_invalid(self, bitcoin_service):
        """Test validation of invalid Bitcoin address"""
        address = "invalid_address"
        
        mock_response = {"isvalid": False}
        
        with patch.object(bitcoin_service, '_rpc_call', return_value=mock_response):
            is_valid = await bitcoin_service.validate_address(address)
            
            assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_validate_address_rpc_error(self, bitcoin_service):
        """Test address validation with RPC error"""
        address = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        
        with patch.object(bitcoin_service, '_rpc_call', side_effect=Exception("RPC failed")):
            is_valid = await bitcoin_service.validate_address(address)
            
            assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_get_network_info_success(self, bitcoin_service):
        """Test successful network info retrieval"""
        mock_network_info = {
            "subversion": "/Satoshi:0.21.0/",
            "connections": 8
        }
        
        mock_blockchain_info = {
            "blocks": 700000,
            "difficulty": 20000000000000,
            "chain": "main"
        }
        
        async def mock_rpc_call(method, params=None):
            if method == "getnetworkinfo":
                return mock_network_info
            elif method == "getblockchaininfo":
                return mock_blockchain_info
            return {}
        
        with patch.object(bitcoin_service, '_rpc_call', side_effect=mock_rpc_call):
            info = await bitcoin_service.get_network_info()
            
            assert info['network'] == "/Satoshi:0.21.0/"
            assert info['connections'] == 8
            assert info['blocks'] == 700000
            assert info['chain'] == "main"
    
    @pytest.mark.asyncio
    async def test_rpc_call_success(self, bitcoin_service):
        """Test successful RPC call"""
        method = "getblockcount"
        expected_result = 700000
        
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": expected_result
        }
        
        with patch.object(bitcoin_service.client, 'post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status.return_value = None
            
            result = await bitcoin_service._rpc_call(method)
            
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_rpc_call_error_response(self, bitcoin_service):
        """Test RPC call with error response"""
        method = "invalid_method"
        
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }
        
        with patch.object(bitcoin_service.client, 'post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status.return_value = None
            
            with pytest.raises(BlockchainError) as exc_info:
                await bitcoin_service._rpc_call(method)
            
            assert "Method not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_rpc_call_connection_error(self, bitcoin_service):
        """Test RPC call with connection error"""
        method = "getblockcount"
        
        with patch.object(bitcoin_service.client, 'post', side_effect=httpx.RequestError("Connection failed")):
            with pytest.raises(BlockchainError) as exc_info:
                await bitcoin_service._rpc_call(method)
            
            assert "Bitcoin node connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_wallet_address_success_integration(self):
        """Test successful Bitcoin wallet address generation (integration)"""
        user_id = "test_user_123"
        async with BitcoinService() as service:
            address = await service.generate_wallet_address(user_id)
            assert isinstance(address, WalletAddress)
            assert address.network == Network.BITCOIN
            assert address.address.startswith("1") or address.address.startswith("3") or address.address.startswith("bc1")
            assert len(address.address) > 25 # Basic length check
    
    @pytest.mark.asyncio
    async def test_generate_wallet_address_failure_integration(self):
        """Test Bitcoin wallet address generation failure (integration)"""
        user_id = "test_user_error"
        with patch('app.services.bitcoin_service.hashlib.sha256', side_effect=Exception("Mock hashing error")):
            async with BitcoinService() as service:
                with pytest.raises(BlockchainError, match="Failed to generate Bitcoin address"):
                    await service.generate_wallet_address(user_id)
    
    @pytest.mark.asyncio
    async def test_get_transaction_info_success_integration(self):
        """Test successful Bitcoin transaction info retrieval (integration)"""
        tx_hash = TransactionHash(hash="a" * 64, network=Network.BITCOIN)
        async with BitcoinService() as service:
            info = await service.get_transaction_info(tx_hash)
            assert isinstance(info, dict)
            assert info["hash"] == tx_hash.hash
            assert info["status"] == "confirmed"
            assert info["confirmations"] >= 3
            assert info["network"] == Network.BITCOIN.value
    
    @pytest.mark.asyncio
    async def test_get_transaction_info_failure_integration(self):
        """Test Bitcoin transaction info retrieval failure (integration)"""
        tx_hash = TransactionHash(hash="b" * 64, network=Network.BITCOIN)
        with patch('app.services.bitcoin_service.datetime', side_effect=Exception("Mock datetime error")):
            async with BitcoinService() as service:
                with pytest.raises(BlockchainError, match="Failed to retrieve Bitcoin transaction info"):
                    await service.get_transaction_info(tx_hash)

# Integration tests for Bitcoin service
class TestBitcoinServiceIntegration:
    """Integration tests for Bitcoin service (requires test Bitcoin node)"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_transaction_flow(self, bitcoin_service):
        """Test complete transaction flow from generation to confirmation"""
        # This test would require a test Bitcoin node
        # Skip in unit tests, run only in integration test environment
        pytest.skip("Integration test - requires test Bitcoin node")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_address_monitoring(self, bitcoin_service):
        """Test address monitoring functionality"""
        # This test would require a test Bitcoin node and time
        pytest.skip("Integration test - requires test Bitcoin node")

# Performance tests for Bitcoin service
class TestBitcoinServicePerformance:
    """Performance tests for Bitcoin service"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_balance_checks(self, bitcoin_service):
        """Test concurrent balance checking performance"""
        addresses = [f"1BvBMSEYstWetqTFn5Au4m4GFg7xJaNV{i:02d}" for i in range(10)]
        
        with patch.object(bitcoin_service, '_rpc_call', return_value=[]):
            start_time = asyncio.get_event_loop().time()
            
            # Run concurrent balance checks
            tasks = [bitcoin_service.get_address_balance(addr) for addr in addresses]
            results = await asyncio.gather(*tasks)
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            # Should complete within reasonable time
            assert duration < 5.0  # 5 seconds max
            assert len(results) == 10
            assert all(isinstance(result, Money) for result in results)

# Additional unit tests
@pytest.mark.asyncio
async def test_generate_wallet_address():
    """Test successful Bitcoin address generation."""
    service = BitcoinService()
    user_id = "test_user_123"
    address = await service.generate_wallet_address(user_id)
    
    assert isinstance(address, WalletAddress)
    assert address.network == Network.BITCOIN
    assert address.address.startswith("bc1q") or address.address.startswith("1") or address.address.startswith("3")
    assert len(address.address) > 25 # Basic length check

@pytest.mark.asyncio
async def test_get_transaction_info_success():
    """Test successful retrieval of Bitcoin transaction info."""
    service = BitcoinService()
    mock_tx_hash = TransactionHash(hash="a" * 64, network=Network.BITCOIN)
    info = await service.get_transaction_info(mock_tx_hash)
    
    assert isinstance(info, dict)
    assert info["hash"] == mock_tx_hash.hash
    assert info["confirmations"] >= 0
    assert "amount" in info
    assert "status" in info

@pytest.mark.asyncio
async def test_get_transaction_info_wrong_network():
    """Test fetching Bitcoin transaction info with a non-Bitcoin hash."""
    service = BitcoinService()
    mock_tx_hash = TransactionHash(hash="0x" + "b" * 40, network=Network.ETHEREUM) # Ethereum hash
    
    with pytest.raises(BlockchainError, match="Transaction hash is not for Bitcoin network."):
        await service.get_transaction_info(mock_tx_hash)

@pytest.mark.asyncio
async def test_broadcast_transaction():
    """Test simulated Bitcoin transaction broadcast."""
    service = BitcoinService()
    signed_tx = "mock_signed_bitcoin_tx_hex"
    tx_hash = await service.broadcast_transaction(signed_tx)
    
    assert isinstance(tx_hash, TransactionHash)
    assert tx_hash.network == Network.BITCOIN
    assert tx_hash.hash.startswith("mock_btc_tx_")

@pytest.mark.asyncio
async def test_validate_address_valid():
    """Test validation of a valid Bitcoin address."""
    service = BitcoinService()
    valid_addresses = [
        "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", # P2PKH
        "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy", # P2SH
        "bc1qgdjfm02222222222222222222222222222222222222222222222222222222", # Bech32
    ]
    for addr in valid_addresses:
        assert await service.validate_address(addr) is True

@pytest.mark.asyncio
async def test_validate_address_invalid():
    """Test validation of an invalid Bitcoin address."""
    service = BitcoinService()
    invalid_addresses = [
        "invalid_address",
        "0x1234567890abcdef1234567890abcdef12345678", # Ethereum address
        "T1234567890abcdef1234567890abcdef1234", # Tron address
        "",
        None
    ]
    for addr in invalid_addresses:
        assert await service.validate_address(addr) is False
