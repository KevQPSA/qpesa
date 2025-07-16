"""
Tests for enhanced payment service
Validates crypto and M-Pesa payment processing
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.payment import PaymentService
from app.schemas.payment import PaymentRequest, PaymentCurrency, PaymentNetwork
from app.models.transaction import Transaction, TransactionStatus
from app.models.user import User
from app.domain.value_objects import Network
from app.core.exceptions import PaymentError, ValidationError

class TestPaymentService:
    """Test enhanced payment service functionality"""
    
    @pytest.fixture
    async def payment_service(self, db_session: AsyncSession):
        """Create payment service instance for testing"""
        return PaymentService(db_session)
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing"""
        return User(
            id="test_user_123",
            email="test@example.com",
            phone="+254712345678",
            first_name="John",
            last_name="Doe"
        )
    
    @pytest.fixture
    def btc_payment_request(self):
        """Create BTC payment request"""
        return PaymentRequest(
            amount=Decimal('0.001'),
            currency=PaymentCurrency.BTC,
            description="Test BTC payment"
        )
    
    @pytest.fixture
    def usdt_payment_request(self):
        """Create USDT payment request"""
        return PaymentRequest(
            amount=Decimal('100.0'),
            currency=PaymentCurrency.USDT,
            network=PaymentNetwork.ETHEREUM,
            description="Test USDT payment"
        )
    
    @pytest.fixture
    def mpesa_payment_request(self):
        """Create M-Pesa payment request"""
        return PaymentRequest(
            amount=Decimal('1000.00'),
            currency=PaymentCurrency.KES,
            phone="+254712345678",
            description="Test M-Pesa payment"
        )
    
    @pytest.mark.asyncio
    async def test_initiate_btc_payment_success(
        self, 
        payment_service: PaymentService, 
        btc_payment_request: PaymentRequest,
        db_session: AsyncSession
    ):
        """Test successful BTC payment initiation"""
        user_id = "test_user_123"
        
        with patch.object(payment_service, '_generate_wallet_address') as mock_gen_addr:
            from app.domain.value_objects import WalletAddress
            mock_gen_addr.return_value = WalletAddress(
                "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", 
                Network.BITCOIN
            )
            
            response = await payment_service.initiate_crypto_payment(user_id, btc_payment_request)
            
            assert response.status == "pending"
            assert response.currency == "BTC"
            assert response.amount == btc_payment_request.amount
            assert response.payment_address == "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
            assert "bitcoin:" in response.qr_code
            assert "3 network confirmations" in response.instructions
    
    @pytest.mark.asyncio
    async def test_initiate_usdt_payment_success(
        self, 
        payment_service: PaymentService, 
        usdt_payment_request: PaymentRequest,
        db_session: AsyncSession
    ):
        """Test successful USDT payment initiation"""
        user_id = "test_user_123"
        
        with patch.object(payment_service, '_generate_wallet_address') as mock_gen_addr:
            from app.domain.value_objects import WalletAddress
            mock_gen_addr.return_value = WalletAddress(
                "0x742d35Cc6634C0532925a3b8D4C9db96590c4C5d", 
                Network.ETHEREUM
            )
            
            response = await payment_service.initiate_crypto_payment(user_id, usdt_payment_request)
            
            assert response.status == "pending"
            assert response.currency == "USDT"
            assert response.amount == usdt_payment_request.amount
            assert response.payment_address == "0x742d35Cc6634C0532925a3b8D4C9db96590c4C5d"
            assert "ethereum:" in response.qr_code
            assert "gas fees" in response.instructions
    
    @pytest.mark.asyncio
    async def test_initiate_crypto_payment_invalid_currency(
        self, 
        payment_service: PaymentService,
        db_session: AsyncSession
    ):
        """Test crypto payment with invalid currency"""
        user_id = "test_user_123"
        
        # Create invalid payment request
        invalid_request = PaymentRequest(
            amount=Decimal('100.0'),
            currency="INVALID",  # Invalid currency
            description="Invalid payment"
        )
        
        with pytest.raises(PaymentError, match="Unsupported crypto currency"):
            await payment_service.initiate_crypto_payment(user_id, invalid_request)
    
    @pytest.mark.asyncio
    async def test_initiate_mpesa_payment_success(
        self, 
        payment_service: PaymentService, 
        mpesa_payment_request: PaymentRequest,
        db_session: AsyncSession
    ):
        """Test successful M-Pesa payment initiation"""
        user_id = "test_user_123"
        
        with patch.object(payment_service, '_initiate_stk_push') as mock_stk:
            mock_stk.return_value = {
                "MerchantRequestID": "mock_merchant_123",
                "CheckoutRequestID": "mock_checkout_123",
                "ResponseCode": "0",
                "ResponseDescription": "Success"
            }
            
            response = await payment_service.initiate_mpesa_payment(user_id, mpesa_payment_request)
            
            assert response.status == "pending"
            assert response.currency == "KES"
            assert response.amount == mpesa_payment_request.amount
            assert "M-Pesa payment prompt" in response.instructions
    
    @pytest.mark.asyncio
    async def test_initiate_mpesa_payment_missing_phone(
        self, 
        payment_service: PaymentService,
        db_session: AsyncSession
    ):
        """Test M-Pesa payment without phone number"""
        user_id = "test_user_123"
        
        invalid_request = PaymentRequest(
            amount=Decimal('1000.00'),
            currency=PaymentCurrency.KES,
            # Missing phone number
            description="Invalid M-Pesa payment"
        )
        
        with pytest.raises(PaymentError, match="Phone number required for M-Pesa payments"):
            await payment_service.initiate_mpesa_payment(user_id, invalid_request)
    
    @pytest.mark.asyncio
    async def test_initiate_mpesa_payment_wrong_currency(
        self, 
        payment_service: PaymentService,
        db_session: AsyncSession
    ):
        """Test M-Pesa payment with wrong currency"""
        user_id = "test_user_123"
        
        invalid_request = PaymentRequest(
            amount=Decimal('100.0'),
            currency=PaymentCurrency.USDT,  # Wrong currency for M-Pesa
            phone="+254712345678",
            description="Invalid M-Pesa payment"
        )
        
        with pytest.raises(PaymentError, match="M-Pesa payments must be in KES"):
            await payment_service.initiate_mpesa_payment(user_id, invalid_request)
    
    @pytest.mark.asyncio
    async def test_get_payment_status_success(
        self, 
        payment_service: PaymentService,
        db_session: AsyncSession
    ):
        """Test successful payment status retrieval"""
        user_id = "test_user_123"
        
        # Create test transaction
        transaction = Transaction(
            user_id=user_id,
            transaction_type="crypto_deposit",
            amount=0.001,
            currency="BTC",
            status=TransactionStatus.PENDING,
            network="bitcoin"
        )
        
        db_session.add(transaction)
        await db_session.commit()
        await db_session.refresh(transaction)
        
        with patch.object(payment_service, '_get_blockchain_status') as mock_blockchain:
            mock_blockchain.return_value = {"confirmations": 2}
            
            status = await payment_service.get_payment_status(str(transaction.id), user_id)
            
            assert status.transaction_id == str(transaction.id)
            assert status.status == "pending"
            assert status.amount == Decimal('0.001')
            assert status.currency == "BTC"
            assert status.confirmations == 2
    
    @pytest.mark.asyncio
    async def test_get_payment_status_not_found(
        self, 
        payment_service: PaymentService,
        db_session: AsyncSession
    ):
        """Test payment status for non-existent transaction"""
        user_id = "test_user_123"
        fake_tx_id = "non_existent_transaction"
        
        with pytest.raises(ValidationError, match="Transaction not found"):
            await payment_service.get_payment_status(fake_tx_id, user_id)
    
    @pytest.mark.asyncio
    async def test_get_payment_history_success(
        self, 
        payment_service: PaymentService,
        db_session: AsyncSession
    ):
        """Test successful payment history retrieval"""
        user_id = "test_user_123"
        
        # Create test transactions
        transactions = [
            Transaction(
                user_id=user_id,
                transaction_type="crypto_deposit",
                amount=0.001,
                currency="BTC",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.utcnow() - timedelta(days=1)
            ),
            Transaction(
                user_id=user_id,
                transaction_type="mpesa_deposit",
                amount=1000.0,
                currency="KES",
                status=TransactionStatus.PENDING,
                created_at=datetime.utcnow()
            )
        ]
        
        for tx in transactions:
            db_session.add(tx)
        await db_session.commit()
        
        history = await payment_service.get_payment_history(user_id, limit=10, offset=0)
        
        assert len(history) == 2
        assert history[0]["currency"] == "KES"  # Most recent first
        assert history[1]["currency"] == "BTC"
        assert all("id" in tx for tx in history)
        assert all("created_at" in tx for tx in history)
    
    @pytest.mark.asyncio
    async def test_process_mpesa_callback_success(
        self, 
        payment_service: PaymentService,
        db_session: AsyncSession
    ):
        """Test successful M-Pesa callback processing"""
        # Create test transaction
        transaction = Transaction(
            user_id="test_user_123",
            transaction_type="mpesa_deposit",
            amount=1000.0,
            currency="KES",
            status=TransactionStatus.PENDING,
            mpesa_reference="mock_checkout_123"
        )
        
        db_session.add(transaction)
        await db_session.commit()
        
        # Mock successful callback
        callback_data = {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "mock_checkout_123",
                    "ResultCode": 0,
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "MpesaReceiptNumber", "Value": "ABC123456"}
                        ]
                    }
                }
            }
        }
        
        await payment_service.process_mpesa_callback(callback_data)
        
        # Refresh transaction
        await db_session.refresh(transaction)
        
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.mpesa_receipt == "ABC123456"
        assert transaction.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_process_mpesa_callback_failure(
        self, 
        payment_service: PaymentService,
        db_session: AsyncSession
    ):
        """Test M-Pesa callback processing for failed payment"""
        # Create test transaction
        transaction = Transaction(
            user_id="test_user_123",
            transaction_type="mpesa_deposit",
            amount=1000.0,
            currency="KES",
            status=TransactionStatus.PENDING,
            mpesa_reference="mock_checkout_123"
        )
        
        db_session.add(transaction)
        await db_session.commit()
        
        # Mock failed callback
        callback_data = {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "mock_checkout_123",
                    "ResultCode": 1032,  # User cancelled
                }
            }
        }
        
        await payment_service.process_mpesa_callback(callback_data)
        
        # Refresh transaction
        await db_session.refresh(transaction)
        
        assert transaction.status == TransactionStatus.FAILED
        assert "M-Pesa payment failed with code: 1032" in transaction.failure_reason
    
    @pytest.mark.asyncio
    async def test_generate_wallet_address_bitcoin(self, payment_service: PaymentService):
        """Test Bitcoin wallet address generation"""
        user_id = "test_user_123"
        
        with patch('app.services.payment.BitcoinService') as mock_bitcoin_service:
            mock_service_instance = AsyncMock()
            mock_bitcoin_service.return_value.__aenter__.return_value = mock_service_instance
            
            from app.domain.value_objects import WalletAddress
            expected_address = WalletAddress("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", Network.BITCOIN)
            mock_service_instance.generate_wallet_address.return_value = expected_address
            
            address = await payment_service._generate_wallet_address(user_id, Network.BITCOIN)
            
            assert address == expected_address
            mock_service_instance.generate_wallet_address.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_generate_wallet_address_ethereum(self, payment_service: PaymentService):
        """Test Ethereum wallet address generation (placeholder)"""
        user_id = "test_user_123"
        
        address = await payment_service._generate_wallet_address(user_id, Network.ETHEREUM)
        
        assert address.network == Network.ETHEREUM
        assert address.address.startswith("0x")
        assert len(address.address) == 42
    
    @pytest.mark.asyncio
    async def test_generate_wallet_address_tron(self, payment_service: PaymentService):
        """Test Tron wallet address generation (placeholder)"""
        user_id = "test_user_123"
        
        address = await payment_service._generate_wallet_address(user_id, Network.TRON)
        
        assert address.network == Network.TRON
        assert address.address.startswith("T")
        assert len(address.address) == 34
    
    @pytest.mark.asyncio
    async def test_generate_wallet_address_unsupported_network(self, payment_service: PaymentService):
        """Test wallet address generation for unsupported network"""
        user_id = "test_user_123"
        
        with pytest.raises(ValidationError, match="Unsupported network"):
            await payment_service._generate_wallet_address(user_id, "UNSUPPORTED")
    
    def test_generate_payment_qr_bitcoin(self, payment_service: PaymentService):
        """Test Bitcoin payment QR code generation"""
        from app.domain.value_objects import WalletAddress, Money, Currency
        
        address = WalletAddress("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", Network.BITCOIN)
        amount = Money(Decimal('0.001'), Currency.BTC)
        
        qr_data = payment_service._generate_payment_qr(address, amount)
        
        assert qr_data == "bitcoin:1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa?amount=0.001"
    
    def test_generate_payment_qr_ethereum(self, payment_service: PaymentService):
        """Test Ethereum USDT payment QR code generation"""
        from app.domain.value_objects import WalletAddress, Money, Currency
        
        address = WalletAddress("0x742d35Cc6634C0532925a3b8D4C9db96590c4C5d", Network.ETHEREUM)
        amount = Money(Decimal('100.0'), Currency.USDT)
        
        qr_data = payment_service._generate_payment_qr(address, amount)
        
        assert "ethereum:" in qr_data
        assert "0xdAC17F958D2ee523a2206206994597C13D831ec7" in qr_data  # USDT contract
        assert address.address in qr_data
    
    def test_get_payment_instructions_bitcoin(self, payment_service: PaymentService):
        """Test Bitcoin payment instructions"""
        from app.domain.value_objects import Money, Currency
        
        amount = Money(Decimal('0.001'), Currency.BTC)
        instructions = payment_service._get_payment_instructions(Network.BITCOIN, amount)
        
        assert "Send exactly 0.001 BTC" in instructions
        assert "3 network confirmations" in instructions
    
    def test_get_payment_instructions_ethereum(self, payment_service: PaymentService):
        """Test Ethereum USDT payment instructions"""
        from app.domain.value_objects import Money, Currency
        
        amount = Money(Decimal('100.0'), Currency.USDT)
        instructions = payment_service._get_payment_instructions(Network.ETHEREUM, amount)
        
        assert "Send exactly 100.0 USDT (ERC-20)" in instructions
        assert "gas fees" in instructions
    
    def test_get_payment_instructions_tron(self, payment_service: PaymentService):
        """Test Tron USDT payment instructions"""
        from app.domain.value_objects import Money, Currency
        
        amount = Money(Decimal('100.0'), Currency.USDT)
        instructions = payment_service._get_payment_instructions(Network.TRON, amount)
        
        assert "Send exactly 100.0 USDT (TRC-20)" in instructions
        assert "Lower fees compared to Ethereum" in instructions
