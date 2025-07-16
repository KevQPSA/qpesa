from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import datetime, timedelta
import logging
import uuid
import asyncio
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.exceptions import PaymentError, ValidationError, BlockchainError, NotFoundError
from app.schemas.payment import (
    CryptoPaymentInitiate, CryptoPaymentStatus, CryptoPaymentHistory,
    MpesaPaymentInitiate, MpesaPaymentStatus, MpesaPaymentCallback, MpesaPaymentHistory,
    PaymentRequest, PaymentResponse, PaymentStatus
)
from app.domain.value_objects import Money, Currency, Network, PhoneNumber, WalletAddress, TransactionHash
from app.domain.entities import PaymentRequest as PaymentRequestEntity, PaymentType, PaymentStatus as EntityPaymentStatus
from app.services.bitcoin_service import BitcoinService
from app.services.usdt_service import USDTService
from app.models.transaction import Transaction
from app.models.user import User # For user validation
from app.models.transaction import TransactionStatus
from app.models.transaction import TransactionType
from app.schemas.payment import MpesaCallback

logger = logging.getLogger(__name__)

# Placeholder for M-Pesa Daraja API integration
class MpesaDarajaService:
    """
    Simulated M-Pesa Daraja API service.
    In a real application, this would make actual HTTP requests to Safaricom's Daraja API.
    """
    def __init__(self):
        self.base_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest" # Placeholder
        logger.info(f"MpesaDarajaService initialized with base URL: {self.base_url}")

    async def initiate_stk_push(self, phone_number: str, amount: Decimal, account_reference: str, transaction_desc: str) -> Dict[str, Any]:
        """
        Simulates initiating an M-Pesa STK Push request.
        """
        await asyncio.sleep(0.5) # Simulate network latency
        
        # Mock response based on common Daraja API success/failure patterns
        if amount <= 0:
            return {
                "ResponseCode": "1",
                "ResponseDescription": "Invalid Amount",
                "CustomerMessage": "Invalid Amount"
            }
        
        checkout_request_id = str(uuid.uuid4())
        merchant_request_id = str(uuid.uuid4())

        return {
            "MerchantRequestID": merchant_request_id,
            "CheckoutRequestID": checkout_request_id,
            "ResponseCode": "0",
            "ResponseDescription": "Success. Request accepted for processing",
            "CustomerMessage": "Success. Request accepted for processing"
        }

    async def query_stk_status(self, checkout_request_id: str) -> Dict[str, Any]:
        """
        Simulates querying the status of an STK Push transaction.
        """
        await asyncio.sleep(0.3) # Simulate network latency
        
        # Mock status response
        return {
            "ResponseCode": "0",
            "ResultCode": "0", # 0 for success, others for failure
            "ResultDesc": "The service request is processed successfully.",
            "CheckoutRequestID": checkout_request_id,
            "MpesaReceiptNumber": f"MPESA{str(uuid.uuid4())[:5].upper()}",
            "TransactionDate": datetime.now().strftime("%Y%m%d%H%M%S"),
            "Amount": 100.00, # This would be dynamic based on the initial request
            "PhoneNumber": "254712345678" # This would be dynamic
        }

mpesa_daraja_service = MpesaDarajaService()
bitcoin_service = BitcoinService()
usdt_service = USDTService()

class PaymentService:
class IPaymentService(ABC):
    """Abstract base class for payment service."""
    """Abstract base class for payment service."""
    """Abstract base class for payment service."""
    @abstractmethod
    async def initiate_crypto_payment(self, user_id: uuid.UUID, payment_request: PaymentRequest) -> PaymentResponse:
        pass
    @abstractmethod
    async def get_payment_status(self, transaction_id: str) -> PaymentResponse:
        pass
    @abstractmethod
    async def initiate_mpesa_payment(self, user_id: uuid.UUID, payment_request: PaymentRequest) -> PaymentResponse:
        pass
    """Enhanced payment processing service with full crypto and M-Pesa support."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
   
    async def initiate_crypto_payment(
        self, 
        user_id: uuid.UUID, 
        payment_request: PaymentRequest
    ) -> PaymentResponse:
        """
        Initiate crypto payment with proper validation and address generation.
        Supports BTC and USDT on multiple networks.
        """
        # Validate user exists
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found.")

        # Stricter input validation
        if payment_request.amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        if not isinstance(payment_request.currency, Currency):
            raise ValidationError("Invalid currency type.")

        # Convert to domain entity for validation
        amount_obj = Money(payment_request.amount, payment_request.currency)
        
        # Determine network based on currency
        network: Optional[Network] = None
        if payment_request.currency == Currency.BTC:
            network = Network.BITCOIN
            if payment_request.network and payment_request.network != Network.BITCOIN:
                raise ValidationError("Bitcoin currency must use Bitcoin network.")
        elif payment_request.currency == Currency.USDT:
            if not payment_request.network:
                raise ValidationError("Network is required for USDT payments (ETHEREUM or TRON).")
            network = payment_request.network
            if network not in [Network.ETHEREUM, Network.TRON]:
                raise ValidationError(f"Unsupported network for USDT: {network.value}")
        else:
            raise ValidationError(f"Unsupported crypto currency: {payment_request.currency.value}")
        
        # Create payment request entity
        payment_entity = PaymentRequestEntity(
            amount=amount_obj,
            payment_type=PaymentType.CRYPTO_DEPOSIT,
            network=network,
            description=payment_request.description
        )
        
        # Generate wallet address based on network
        wallet_address_obj = await self._generate_wallet_address(user_id, network)
        
        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            transaction_type=payment_entity.payment_type,
            amount=payment_entity.amount.amount,
            currency=payment_entity.amount.currency.value,
            network=network.value,
            blockchain_hash=None, # Will be filled upon confirmation
            confirmations=0,
            status=EntityPaymentStatus.PENDING,
            expires_at=payment_entity.expires_at,
            notes=payment_entity.description,
            metadata_json={"deposit_address": wallet_address_obj.address} # Store address in metadata
        )
        
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        
        # Generate QR code data (simplified)
        qr_code_data = self._generate_payment_qr(wallet_address_obj, amount_obj)
        
        logger.info(f"Crypto payment initiated: {transaction.id} for user {user_id}")
        
        return PaymentResponse(
            transaction_id=str(transaction.id),
            status=transaction.status.value,
            amount=payment_request.amount,
            currency=payment_request.currency.value,
            payment_address=wallet_address_obj.address,
            qr_code=qr_code_data,
            expires_at=payment_entity.expires_at.isoformat(),
            instructions=self._get_payment_instructions(network, amount_obj)
        )
           
    async def _generate_wallet_address(self, user_id: uuid.UUID, network: Network) -> WalletAddress:
        """Generate wallet address for specified network."""
        if network == Network.BITCOIN:
            async with bitcoin_service as btc_service:
                return await btc_service.generate_wallet_address(str(user_id))
        elif network in [Network.ETHEREUM, Network.TRON]:
            async with usdt_service as u_service:
                return await u_service.generate_deposit_address(str(user_id), network)
        else:
            raise ValidationError(f"Unsupported network for address generation: {network.value}")
   
    def _generate_payment_qr(self, address: WalletAddress, amount: Money) -> str:
        """Generate QR code data for payment."""
        if address.network == Network.BITCOIN:
            return f"bitcoin:{address.address}?amount={amount.amount}"
        elif address.network == Network.ETHEREUM:
            # For USDT on Ethereum, include contract address
            usdt_contract = usdt_service.usdt_erc20_contract
            # Amount needs to be in smallest unit (e.g., wei for ETH, 10^6 for USDT)
            # This is a simplification; actual conversion depends on token decimals
            amount_in_smallest_unit = int(amount.amount * (10**6)) # Assuming 6 decimals for USDT
            return f"ethereum:{usdt_contract}/transfer?address={address.address}&uint256={amount_in_smallest_unit}"
        elif address.network == Network.TRON:
            # For USDT on Tron, include contract address
            usdt_contract = usdt_service.usdt_trc20_contract
            amount_in_smallest_unit = int(amount.amount * (10**6)) # Assuming 6 decimals for USDT
            return f"tron:{address.address}?amount={amount_in_smallest_unit}&contract={usdt_contract}"
        return f"{address.network.value}:{address.address}"
   
    def _get_payment_instructions(self, network: Network, amount: Money) -> str:
        """Get human-readable payment instructions."""
        if network == Network.BITCOIN:
            return f"Send exactly {amount.amount.normalize()} {amount.currency.value} to the Bitcoin address above. Transaction will be confirmed after 3 network confirmations."
        elif network == Network.ETHEREUM:
            return f"Send exactly {amount.amount.normalize()} {amount.currency.value} (ERC-20) to the Ethereum address above. Ensure you have enough ETH for gas fees."
        elif network == Network.TRON:
            return f"Send exactly {amount.amount.normalize()} {amount.currency.value} (TRC-20) to the Tron address above. Lower fees compared to Ethereum."
        return "Send the specified amount to the provided address."
   
    async def initiate_mpesa_payment(
        self,
        user_id: uuid.UUID,
        payment_request: PaymentRequest
    ) -> PaymentResponse:
        """
        Initiate M-Pesa STK Push payment with enhanced validation.
        """
        # Validate user exists
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found.")

        # Validate M-Pesa specific requirements
        if not payment_request.phone:
            raise ValidationError("Phone number required for M-Pesa payments.")
        
        if payment_request.currency != Currency.KES:
            raise ValidationError("M-Pesa payments must be in KES.")
        
        # Validate phone number and amount
        phone_obj = PhoneNumber(payment_request.phone)
        amount_obj = Money(payment_request.amount, Currency.KES)
        
        # Create payment request entity
        payment_entity = PaymentRequestEntity(
            amount=amount_obj,
            payment_type=PaymentType.MPESA_DEPOSIT,
            phone_number=phone_obj,
            description=payment_request.description
        )
        
        # Create transaction record (initial pending state)
        transaction = Transaction(
            user_id=user_id,
            transaction_type=payment_entity.payment_type,
            amount=payment_entity.amount.amount,
            currency=payment_entity.amount.currency.value,
            mpesa_phone=phone_obj.to_international_format(),
            status=EntityPaymentStatus.PENDING,
            expires_at=payment_entity.expires_at,
            notes=payment_entity.description
        )
        
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        
        # Initiate STK Push via Daraja API
        stk_response = await mpesa_daraja_service.initiate_stk_push(
            phone_number=phone_obj.to_international_format(),
            amount=amount_obj.amount,
            account_reference=str(transaction.id), # Use internal transaction ID as reference
            transaction_desc=payment_entity.description or f"Deposit {amount_obj.amount} KES"
        )
        
        if stk_response.get("ResponseCode") != "0":
            # STK Push failed at Daraja API level
            transaction.status = EntityPaymentStatus.FAILED
            transaction.failure_reason = stk_response.get("ResponseDescription", "STK Push failed at M-Pesa.")
            await self.db.commit()
            raise PaymentError(transaction.failure_reason)
        
        # Store M-Pesa's CheckoutRequestID for callback matching
        transaction.mpesa_reference = stk_response.get("CheckoutRequestID")
        await self.db.commit()
        await self.db.refresh(transaction)

        logger.info(f"M-Pesa payment initiated: {transaction.id} for user {user_id}")
        
        return PaymentResponse(
            transaction_id=str(transaction.id),
            status=transaction.status.value,
            amount=payment_request.amount,
            currency=payment_request.currency.value,
            expires_at=payment_entity.expires_at.isoformat(),
            instructions="Check your phone for M-Pesa payment prompt. Enter your M-Pesa PIN to complete the payment."
        )
   
    async def get_payment_status(
        self,
        transaction_id: str,
        user_id: uuid.UUID
    ) -> PaymentStatus:
        """Get enhanced payment status with blockchain information."""
        # Get transaction from database
        stmt = select(Transaction).where(
            Transaction.id == uuid.UUID(transaction_id),
            Transaction.user_id == user_id
        )
        result = await self.db.execute(stmt)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise NotFoundError("Transaction not found or does not belong to user.")
        
        # Get additional blockchain info if applicable
        blockchain_info = {}
        if transaction.blockchain_hash and transaction.network:
            try:
                blockchain_info = await self._get_blockchain_status(
                    TransactionHash(hash=transaction.blockchain_hash, network=Network(transaction.network))
                )
                # Update confirmations from blockchain if available and more recent
                if blockchain_info.get("confirmations", 0) > transaction.confirmations:
                    transaction.confirmations = blockchain_info["confirmations"]
                    await self.db.commit() # Commit updated confirmations
            except BlockchainError as e:
                logger.warning(f"Could not fetch blockchain status for {transaction.blockchain_hash}: {e.message}")
                # Continue without blockchain info if there's an error
        
        return PaymentStatus(
            transaction_id=str(transaction.id),
            status=transaction.status,
            amount=transaction.amount,
            currency=transaction.currency,
            confirmations=transaction.confirmations,
            blockchain_hash=transaction.blockchain_hash,
            created_at=transaction.created_at,
            completed_at=transaction.completed_at,
            failure_reason=transaction.failure_reason
        )
   
    async def _get_blockchain_status(self, tx_hash_obj: TransactionHash) -> Dict[str, Any]:
        """Get blockchain transaction status from respective service."""
        if tx_hash_obj.network == Network.BITCOIN:
            async with bitcoin_service as btc_service:
                return await btc_service.get_transaction_info(tx_hash_obj)
        elif tx_hash_obj.network in [Network.ETHEREUM, Network.TRON]:
            async with usdt_service as u_service:
                return await u_service.get_transaction_info(tx_hash_obj)
        else:
            raise BlockchainError(f"Unsupported network for blockchain status: {tx_hash_obj.network.value}")
   
    async def get_payment_history(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get enhanced payment history with proper pagination."""
        stmt = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(stmt)
        transactions = result.scalars().all()
        
        history = []
        for tx in transactions:
            history.append({
                "id": str(tx.id),
                "type": tx.transaction_type.value,
                "amount": float(tx.amount), # Convert Decimal to float for JSON response
                "currency": tx.currency,
                "status": tx.status.value,
                "network": tx.network,
                "blockchain_hash": tx.blockchain_hash,
                "confirmations": tx.confirmations,
                "created_at": tx.created_at.isoformat(),
                "completed_at": tx.completed_at.isoformat() if tx.completed_at else None,
                "description": tx.notes,
                "mpesa_phone": tx.mpesa_phone,
                "mpesa_receipt": tx.mpesa_receipt
            })
        
        return history
   
    async def process_mpesa_callback(self, callback_data: MpesaCallback) -> None:
        """Process M-Pesa callback with proper validation and updates."""
        stk_callback = callback_data.Body # Access the nested STKCallback object
        checkout_request_id = stk_callback.CheckoutRequestID
        result_code = stk_callback.ResultCode
        
        if not checkout_request_id:
            logger.warning("M-Pesa callback missing CheckoutRequestID.")
            return
        
        # Find transaction by M-Pesa reference (CheckoutRequestID)
        stmt = select(Transaction).where(
            Transaction.mpesa_reference == checkout_request_id,
            Transaction.transaction_type == PaymentType.MPESA_DEPOSIT # Ensure it's a deposit
        )
        result = await self.db.execute(stmt)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            logger.warning(f"Transaction not found for M-Pesa callback: {checkout_request_id}")
            return
        
        # Update transaction based on result
        if result_code == 0:  # Success
            transaction.status = EntityPaymentStatus.COMPLETED
            transaction.completed_at = datetime.now()
            
            # Extract M-Pesa receipt number and other details from CallbackMetadata
            if stk_callback.CallbackMetadata and stk_callback.CallbackMetadata.Item:
                for item in stk_callback.CallbackMetadata.Item:
                    if item.Name == "MpesaReceiptNumber":
                        transaction.mpesa_receipt = item.Value
                    elif item.Name == "Amount":
                        try:
                            transaction.amount = Decimal(str(item.Value)) # Update amount from callback
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid amount in M-Pesa callback for {transaction.id}: {item.Value}")
                    # Add other fields like TransactionDate, PhoneNumber if needed
            
            logger.info(f"M-Pesa payment completed: {transaction.id}, Receipt: {transaction.mpesa_receipt}")
        else:
            # Payment failed or cancelled
            transaction.status = EntityPaymentStatus.FAILED
            transaction.failure_reason = f"M-Pesa payment failed with code: {result_code} - {stk_callback.ResultDesc}"
            
            logger.warning(f"M-Pesa payment failed: {transaction.id}, code: {result_code}, desc: {stk_callback.ResultDesc}")
        
        await self.db.commit()
           
    async def monitor_crypto_payment(self, transaction_id: str) -> None:
        """
        Monitor crypto payment for confirmations.
        This would typically be a long-running background task or triggered by webhooks.
        """
        try:
            # Get transaction
            stmt = select(Transaction).where(Transaction.id == uuid.UUID(transaction_id))
            result = await self.db.execute(stmt)
            transaction = result.scalar_one_or_none()
            
            if not transaction or not transaction.network or transaction.status != EntityPaymentStatus.PENDING:
                logger.info(f"Monitoring skipped for {transaction_id}: not found, no network, or not pending.")
                return
            
            network = Network(transaction.network)
            
            # Simulate monitoring logic
            logger.info(f"Simulating monitoring for {network.value} transaction: {transaction.id}")
            
            # In a real scenario, you'd poll the blockchain service or wait for a webhook
            # For this simulation, we'll just update status after a delay
            await asyncio.sleep(5) # Simulate waiting for confirmations
            
            # Assume payment is confirmed for simulation purposes
            transaction.status = EntityPaymentStatus.COMPLETED
            transaction.completed_at = datetime.now()
            transaction.blockchain_hash = f"mock_tx_hash_{transaction_id}" # Assign a mock hash
            transaction.confirmations = 6 # Simulate enough confirmations
            transaction.notes = "Simulated blockchain confirmation."
            
            await self.db.commit()
            logger.info(f"Simulated crypto payment completion for {transaction.id}")
            
        except Exception as e:
            logger.error(f"Crypto payment monitoring failed for {transaction_id}: {str(e)}", exc_info=True)
            # Optionally update transaction status to FAILED or PROCESSING_ERROR
            if transaction and transaction.status == EntityPaymentStatus.PENDING:
                transaction.status = EntityPaymentStatus.FAILED
                transaction.failure_reason = f"Monitoring failed: {str(e)}"
                await self.db.commit()

# Placeholder for M-Pesa API integration
class MpesaService:
    def initiate_stk_push(self, phone_number: str, amount: float, account_reference: str, transaction_desc: str):
        print(f"Simulating M-Pesa STK Push for {phone_number} with amount {amount}")
        # In a real scenario, this would call the Safaricom Daraja API
        # and return a CheckoutRequestID and ResponseCode
        return {
            "CheckoutRequestID": str(uuid.uuid4()),
            "ResponseCode": "0",
            "ResponseDescription": "Success. Request accepted for processing",
            "CustomerMessage": "Success. Request accepted for processing",
            "MerchantRequestID": str(uuid.uuid4())
        }

    def query_stk_status(self, checkout_request_id: str):
        print(f"Simulating M-Pesa STK Push status query for {checkout_request_id}")
        # In a real scenario, this would query the Safaricom Daraja API
        return {
            "ResponseCode": "0",
            "ResultCode": "0",
            "ResultDesc": "The service request is processed successfully.",
            "CheckoutRequestID": checkout_request_id,
            "MpesaReceiptNumber": "MPESA" + str(uuid.uuid4())[:5].upper(),
            "TransactionDate": datetime.now().strftime("%Y%m%d%H%M%S"),
            "Amount": 100.00, # This should be dynamic based on the initial request
            "PhoneNumber": "254712345678" # This should be dynamic
        }

mpesa_service = MpesaService()
bitcoin_service = BitcoinService()
usdt_service = USDTService()

def initiate_crypto_payment(db: Session, user_id: int, payment_data: CryptoPaymentInitiate) -> CryptoPaymentStatus:
    # Determine which crypto service to use
    if payment_data.currency == Currency.BTC:
        service = bitcoin_service
    elif payment_data.currency == Currency.USDT:
        service = usdt_service
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported cryptocurrency")

    # Simulate crypto address generation and payment initiation
    try:
        deposit_address = service.generate_deposit_address(user_id)
        # In a real system, you'd also get a unique identifier for this specific payment request
        # and potentially a QR code or payment link.
        transaction_id = str(uuid.uuid4())
        
        new_transaction = Transaction(
            id=transaction_id,
            user_id=user_id,
            amount=payment_data.amount,
            currency=payment_data.currency.value,
            transaction_type=TransactionType.CRYPTO_DEPOSIT.value,
            status=TransactionStatus.PENDING.value,
            external_id=deposit_address, # Using deposit address as external_id for now
            transaction_type="deposit" # Assuming this is a deposit for now
        )
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)

        return CryptoPaymentStatus(
            transaction_id=new_transaction.id,
            status=TransactionStatus.PENDING,
            currency=new_transaction.currency,
            amount=new_transaction.amount,
            deposit_address=deposit_address,
            message="Payment initiated. Awaiting blockchain confirmation."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to initiate crypto payment: {e}")

def get_crypto_payment_status(db: Session, user_id: int, transaction_id: str) -> Optional[CryptoPaymentStatus]:
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.CRYPTO_DEPOSIT.value
    ).first()

    if not transaction:
        return None

    # In a real system, you would query the blockchain service for the latest status
    # For simulation, we'll just return the stored status
    return CryptoPaymentStatus(
        transaction_id=transaction.id,
        status=TransactionStatus(transaction.status),
        currency=Currency(transaction.currency),
        amount=transaction.amount,
        deposit_address=transaction.external_id, # Assuming external_id stores the deposit address
        message=f"Current status: {transaction.status}"
    )

def get_crypto_payment_history(db: Session, user_id: int) -> List[CryptoPaymentHistory]:
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.CRYPTO_DEPOSIT.value
    ).all()

    return [
        CryptoPaymentHistory(
            transaction_id=t.id,
            amount=t.amount,
            currency=Currency(t.currency),
            status=TransactionStatus(t.status),
            created_at=t.created_at
        ) for t in transactions
    ]

def initiate_mpesa_payment(db: Session, user_id: int, payment_data: MpesaPaymentInitiate) -> MpesaPaymentStatus:
    try:
        # Call M-Pesa STK Push API
        mpesa_response = mpesa_service.initiate_stk_push(
            phone_number=payment_data.phone_number,
            amount=payment_data.amount,
            account_reference=payment_data.account_reference,
            transaction_desc=payment_data.transaction_desc
        )

        if mpesa_response.get("ResponseCode") != "0":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mpesa_response.get("ResponseDescription", "M-Pesa STK Push initiation failed")
            )

        checkout_request_id = mpesa_response["CheckoutRequestID"]
        
        new_transaction = Transaction(
            id=str(uuid.uuid4()), # Our internal transaction ID
            user_id=user_id,
            amount=payment_data.amount,
            currency=Currency.KES.value, # Assuming KES for M-Pesa
            transaction_type=TransactionType.FIAT_DEPOSIT.value,
            status=TransactionStatus.PENDING.value,
            external_id=checkout_request_id, # Store M-Pesa's CheckoutRequestID
            transaction_type="deposit" # Assuming this is a deposit
        )
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)

        return MpesaPaymentStatus(
            transaction_id=new_transaction.id,
            status=TransactionStatus.PENDING,
            amount=new_transaction.amount,
            phone_number=payment_data.phone_number,
            mpesa_checkout_request_id=checkout_request_id,
            message="M-Pesa STK Push initiated. Please complete the transaction on your phone."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to initiate M-Pesa payment: {e}")

def handle_mpesa_callback(db: Session, callback_data: MpesaPaymentCallback) -> MpesaPaymentCallback:
    # This function processes the callback from M-Pesa
    # In a real system, you'd validate the callback data (e.g., security credentials)
    # and then update the transaction status in your database.

    result_code = callback_data.ResultCode
    checkout_request_id = callback_data.CheckoutRequestID
    mpesa_receipt_number = None
    amount = None
    transaction_date = None
    phone_number = None

    if callback_data.CallbackMetadata and callback_data.CallbackMetadata.Item:
        for item in callback_data.CallbackMetadata.Item:
            if item.Name == "MpesaReceiptNumber":
                mpesa_receipt_number = item.Value
            elif item.Name == "Amount":
                amount = item.Value
            elif item.Name == "TransactionDate":
                transaction_date = item.Value
            elif item.Name == "PhoneNumber":
                phone_number = item.Value

    transaction = db.query(Transaction).filter(
        Transaction.external_id == checkout_request_id,
        Transaction.transaction_type == TransactionType.FIAT_DEPOSIT.value
    ).first()

    if not transaction:
        # Log this, it might be an invalid callback or a race condition
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found for M-Pesa callback")

    if result_code == 0: # Success
        transaction.status = TransactionStatus.COMPLETED.value
        transaction.external_id = mpesa_receipt_number # Update external_id to receipt number
        transaction.amount = amount if amount is not None else transaction.amount # Update amount from callback if provided
        # You might want to store transaction_date and phone_number as well
    else: # Failed or cancelled
        transaction.status = TransactionStatus.FAILED.value
        # Store error details if available
        transaction.metadata = {"ResultCode": result_code, "ResultDesc": callback_data.ResultDesc}

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return callback_data # Return the received callback data as confirmation

def get_mpesa_payment_status(db: Session, user_id: int, transaction_id: str) -> Optional[MpesaPaymentStatus]:
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.FIAT_DEPOSIT.value
    ).first()

    if not transaction:
        return None

    # In a real system, if status is PENDING, you might query M-Pesa API for latest status
    # using the stored external_id (CheckoutRequestID)
    
    # For simulation, we'll just return the stored status
    return MpesaPaymentStatus(
        transaction_id=transaction.id,
        status=TransactionStatus(transaction.status),
        amount=transaction.amount,
        phone_number="2547XXXXXXXX", # Placeholder, as we don't store it directly in Transaction model yet
        mpesa_checkout_request_id=transaction.external_id, # This might be receipt number if completed
        message=f"Current status: {transaction.status}"
    )

def get_mpesa_payment_history(db: Session, user_id: int) -> List[MpesaPaymentHistory]:
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.FIAT_DEPOSIT.value
    ).all()

    return [
        MpesaPaymentHistory(
            transaction_id=t.id,
            amount=t.amount,
            currency=Currency(t.currency), # Should be KES
            status=TransactionStatus(t.status),
            created_at=t.created_at,
            mpesa_receipt_number=t.external_id if t.status == TransactionStatus.COMPLETED.value else None # Assuming external_id is receipt for completed
        ) for t in transactions
    ]
