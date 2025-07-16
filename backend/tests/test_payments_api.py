"""
Payment API endpoint integration tests.
Validates crypto and M-Pesa payment processing via API endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import uuid

from app.models.user import User, UserRole, KYCStatus
from app.models.transaction import Transaction, TransactionType, TransactionStatus as EntityPaymentStatus
from app.schemas.payment import PaymentRequest, Currency, Network, MpesaCallback, MpesaStkCallback, MpesaCallbackMetadata, MpesaCallbackItem
from app.services.auth import AuthService
from app.domain.value_objects import WalletAddress, PhoneNumber, TransactionHash

@pytest.fixture
async def verified_authenticated_client(client: AsyncClient, db_session: AsyncSession, registered_user_data: dict):
    """Fixture to provide an authenticated client with a KYC-verified user."""
    auth_service = AuthService(db_session)
    
    # Register user
    token_response = await auth_service.register_user(UserRegistration(**registered_user_data))
    user_id = uuid.UUID(token_response.user_id)
    access_token = token_response.access_token
    
    # Update user to verified KYC for payment operations
    user = await db_session.get(User, user_id)
    user.kyc_status = KYCStatus.VERIFIED
    user.is_verified = True
    await db_session.commit()
    await db_session.refresh(user)
    
    client.headers = {"Authorization": f"Bearer {access_token}"}
    return client

@pytest.mark.asyncio
async def test_initiate_crypto_payment_api_success(
    verified_authenticated_client: AsyncClient, 
    db_session: AsyncSession
):
    """Test successful crypto payment initiation via API."""
    payment_request_data = {
        "amount": 0.001,
        "currency": "BTC",
        "network": "bitcoin",
        "description": "Test BTC deposit via API"
    }
    
    # Mock the internal service call to generate wallet address
    with patch('app.services.payment.bitcoin_service.generate_wallet_address', new_callable=AsyncMock) as mock_gen_addr:
        mock_gen_addr.return_value = WalletAddress(
            "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", 
            Network.BITCOIN
        )
        # Mock the background task to prevent actual monitoring during test
        with patch('app.services.payment.PaymentService.monitor_crypto_payment', new_callable=AsyncMock) as mock_monitor:
            response = await verified_authenticated_client.post("/api/v1/payments/crypto/initiate", json=payment_request_data)
            
            assert response.status_code == 202
            data = response.json()
            assert data["status"] == EntityPaymentStatus.PENDING.value
            assert data["currency"] == "BTC"
            assert Decimal(data["amount"]) == Decimal(str(payment_request_data["amount"]))
            assert data["payment_address"] == "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
            assert "bitcoin:" in data["qr_code"]
            assert "3 network confirmations" in data["instructions"]
            assert "transaction_id" in data

            # Verify transaction was created in DB
            tx = await db_session.get(Transaction, uuid.UUID(data["transaction_id"]))
            assert tx is not None
            assert tx.status == EntityPaymentStatus.PENDING
            assert tx.currency == "BTC"
            assert tx.amount == Decimal(str(payment_request_data["amount"]))
            assert tx.network == Network.BITCOIN.value
            assert tx.metadata_json["deposit_address"] == "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
            mock_monitor.assert_called_once_with(data["transaction_id"])

@pytest.mark.asyncio
async def test_initiate_crypto_payment_api_unauthorized(client: AsyncClient):
    """Test crypto payment initiation without authentication."""
    payment_request_data = {
        "amount": 0.001,
        "currency": "BTC",
        "network": "bitcoin",
        "description": "Unauthorized BTC deposit"
    }
    
    response = await client.post("/api/v1/payments/crypto/initiate", json=payment_request_data)
    
    assert response.status_code == 403 # HTTPBearer raises 403 if no credentials

@pytest.mark.asyncio
async def test_initiate_crypto_payment_api_invalid_data(verified_authenticated_client: AsyncClient):
    """Test crypto payment initiation with invalid data."""
    invalid_payment_request_data = {
        "amount": -10.0, # Invalid amount
        "currency": "BTC",
        "network": "bitcoin",
        "description": "Invalid BTC deposit"
    }
    
    response = await verified_authenticated_client.post("/api/v1/payments/crypto/initiate", json=invalid_payment_request_data)
    
    assert response.status_code == 422 # Pydantic validation error
    assert "amount" in response.json()["detail"][0]["loc"]

@pytest.mark.asyncio
async def test_initiate_mpesa_payment_api_success(
    verified_authenticated_client: AsyncClient, 
    db_session: AsyncSession
):
    """Test successful M-Pesa payment initiation via API."""
    payment_request_data = {
        "amount": 500.00,
        "currency": "KES",
        "phone": "+254712345691",
        "description": "Test M-Pesa deposit via API"
    }
    
    # Mock the internal STK push call
    with patch('app.services.payment.mpesa_daraja_service.initiate_stk_push', new_callable=AsyncMock) as mock_stk_push:
        mock_stk_push.return_value = {
            "MerchantRequestID": "mock_merchant_req_123",
            "CheckoutRequestID": "mock_checkout_req_123",
            "ResponseCode": "0",
            "ResponseDescription": "Success. Request accepted for processing",
            "CustomerMessage": "Success. Request accepted for processing"
        }
        
        response = await verified_authenticated_client.post("/api/v1/payments/mpesa/stk-push", json=payment_request_data)
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == EntityPaymentStatus.PENDING.value
        assert data["currency"] == "KES"
        assert Decimal(data["amount"]) == Decimal(str(payment_request_data["amount"]))
        assert "M-Pesa payment prompt" in data["instructions"]
        assert "transaction_id" in data

        # Verify transaction was created in DB
        tx = await db_session.get(Transaction, uuid.UUID(data["transaction_id"]))
        assert tx is not None
        assert tx.status == EntityPaymentStatus.PENDING
        assert tx.currency == "KES"
        assert tx.amount == Decimal(str(payment_request_data["amount"]))
        assert tx.mpesa_phone == payment_request_data["phone"]
        assert tx.mpesa_reference == "mock_checkout_req_123" # Should be set by service

@pytest.mark.asyncio
async def test_initiate_mpesa_payment_api_missing_phone(verified_authenticated_client: AsyncClient):
    """Test M-Pesa payment initiation with missing phone number."""
    invalid_payment_request_data = {
        "amount": 100.0,
        "currency": "KES",
        "description": "M-Pesa without phone"
    }
    
    response = await verified_authenticated_client.post("/api/v1/payments/mpesa/stk-push", json=invalid_payment_request_data)
    
    assert response.status_code == 400
    assert "Phone number required for M-Pesa payments" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_payment_status_api_success(
    verified_authenticated_client: AsyncClient, 
    db_session: AsyncSession,
    registered_user: User
):
    """Test successful payment status retrieval via API."""
    # Create a transaction directly in DB for testing status retrieval
    transaction_id = uuid.uuid4()
    transaction = Transaction(
        id=transaction_id,
        user_id=registered_user.id,
        transaction_type=TransactionType.CRYPTO_DEPOSIT,
        amount=Decimal("0.0005"),
        currency="BTC",
        status=EntityPaymentStatus.PENDING,
        network="bitcoin",
        blockchain_hash="0x" + "c" * 64,
        confirmations=1,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=10)
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)

    # Mock blockchain status for consistency
    with patch('app.services.payment.PaymentService._get_blockchain_status', new_callable=AsyncMock) as mock_blockchain_status:
        mock_blockchain_status.return_value = {"confirmations": 2, "status": "confirming"}
        
        response = await verified_authenticated_client.get(f"/api/v1/payments/status/{transaction_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == str(transaction_id)
        assert data["status"] == EntityPaymentStatus.PENDING.value # Status from DB, not mock_blockchain_status
        assert Decimal(data["amount"]) == Decimal(str(transaction.amount))
        assert data["currency"] == transaction.currency
        assert data["confirmations"] == 2 # Confirmations from mock_blockchain_status
        assert data["blockchain_hash"] == transaction.blockchain_hash
        assert data["completed_at"] is None

@pytest.mark.asyncio
async def test_get_payment_status_api_not_found(verified_authenticated_client: AsyncClient):
    """Test payment status retrieval for non-existent transaction."""
    fake_tx_id = str(uuid.uuid4())
    response = await verified_authenticated_client.get(f"/api/v1/payments/status/{fake_tx_id}")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found or does not belong to user."

@pytest.mark.asyncio
async def test_get_payment_history_api_success(
    verified_authenticated_client: AsyncClient, 
    db_session: AsyncSession,
    registered_user: User
):
    """Test successful payment history retrieval via API."""
    
    # Create multiple transactions for history
    transactions_to_add = [
        Transaction(
            user_id=registered_user.id,
            transaction_type=TransactionType.CRYPTO_DEPOSIT,
            amount=Decimal("0.001"),
            currency="BTC",
            status=EntityPaymentStatus.COMPLETED,
            created_at=datetime.now(timezone.utc) - timedelta(days=2)
        ),
        Transaction(
            user_id=registered_user.id,
            transaction_type=TransactionType.FIAT_DEPOSIT,
            amount=Decimal("1500.0"),
            currency="KES",
            status=EntityPaymentStatus.PENDING,
            created_at=datetime.now(timezone.utc) - timedelta(days=1)
        ),
        Transaction(
            user_id=registered_user.id,
            transaction_type=TransactionType.CRYPTO_WITHDRAWAL,
            amount=Decimal("0.0002"),
            currency="USDT",
            status=EntityPaymentStatus.FAILED,
            created_at=datetime.now(timezone.utc)
        )
    ]
    db_session.add_all(transactions_to_add)
    await db_session.commit()
    
    response = await verified_authenticated_client.get("/api/v1/payments/history?limit=2&offset=0")
    
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2 # Check pagination
    assert history[0]["currency"] == "USDT" # Most recent first
    assert history[1]["currency"] == "KES"
    assert all("id" in tx for tx in history)

@pytest.mark.asyncio
async def test_mpesa_callback_api_success(
    client: AsyncClient, # Use unauthenticated client as callback is public
    db_session: AsyncSession,
    registered_user: User
):
    """Test successful M-Pesa callback processing via API."""
    # Create a dummy transaction for the callback to update
    checkout_request_id = "mock_checkout_req_for_callback"
    transaction_id = uuid.uuid4()
    transaction = Transaction(
        id=transaction_id,
        user_id=registered_user.id,
        transaction_type=TransactionType.FIAT_DEPOSIT,
        amount=Decimal("1000.0"),
        currency="KES",
        status=EntityPaymentStatus.PENDING,
        mpesa_phone="+254712345699",
        mpesa_reference=checkout_request_id, # This must match the callback data
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5)
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)

    callback_data = MpesaCallback(
        Body=MpesaStkCallback(
            MerchantRequestID="mock_merchant_req_for_callback",
            CheckoutRequestID=checkout_request_id,
            ResultCode=0,
            ResultDesc="Service processing successful.",
            CallbackMetadata=MpesaCallbackMetadata(
                Item=[
                    MpesaCallbackItem(Name="Amount", Value="1000.0"),
                    MpesaCallbackItem(Name="MpesaReceiptNumber", Value="MPESAABC123"),
                    MpesaCallbackItem(Name="Balance", Value=""),
                    MpesaCallbackItem(Name="TransactionDate", Value="20231026100000"),
                    MpesaCallbackItem(Name="PhoneNumber", Value="254712345699")
                ]
            )
        )
    )
    
    response = await client.post("/api/v1/payments/mpesa/callback", json=callback_data.model_dump(mode='json'))
    
    assert response.status_code == 200
    assert response.json() == {"ResultCode": "0", "ResultDesc": "Success"}

    # Verify transaction status updated in DB
    await db_session.refresh(transaction)
    assert transaction.status == EntityPaymentStatus.COMPLETED
    assert transaction.mpesa_receipt == "MPESAABC123"
    assert transaction.completed_at is not None

@pytest.mark.asyncio
async def test_mpesa_callback_api_failure(
    client: AsyncClient, 
    db_session: AsyncSession,
    registered_user: User
):
    """Test M-Pesa callback processing for failed payment via API."""
    checkout_request_id = "mock_checkout_req_fail"
    transaction_id = uuid.uuid4()
    transaction = Transaction(
        id=transaction_id,
        user_id=registered_user.id,
        transaction_type=TransactionType.FIAT_DEPOSIT,
        amount=Decimal("500.0"),
        currency="KES",
        status=EntityPaymentStatus.PENDING,
        mpesa_phone="+254712345698",
        mpesa_reference=checkout_request_id,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5)
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)

    callback_data = MpesaCallback(
        Body=MpesaStkCallback(
            MerchantRequestID="mock_merchant_req_fail",
            CheckoutRequestID=checkout_request_id,
            ResultCode=1032, # User cancelled
            ResultDesc="The transaction was cancelled by the user.",
            CallbackMetadata=None
        )
    )
    
    response = await client.post("/api/v1/payments/mpesa/callback", json=callback_data.model_dump(mode='json'))
    
    assert response.status_code == 200
    assert response.json() == {"ResultCode": "0", "ResultDesc": "Success"} # M-Pesa expects 0 even on internal failure

    # Verify transaction status updated in DB
    await db_session.refresh(transaction)
    assert transaction.status == EntityPaymentStatus.FAILED
    assert "M-Pesa payment failed with code: 1032" in transaction.failure_reason
    assert transaction.completed_at is None
