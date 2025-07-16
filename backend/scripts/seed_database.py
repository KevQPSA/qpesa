"""
Script to seed the database with initial data for development and testing.
This includes sample users, wallets, and potentially transactions.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine, Base
from app.models.user import User, UserRole, KYCStatus
from app.models.wallet import Wallet
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.schemas.auth import UserRegistration
from app.services.auth import AuthService
from app.services.wallet import WalletService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def seed_data():
    """Seeds the database with sample users, wallets, and transactions."""
    logger.info("Starting database seeding...")

    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        wallet_service = WalletService(session)

        # Check if data already exists to prevent duplicates on re-run
        existing_users_count = (await session.execute(select(User))).scalar_one_or_none()
        if existing_users_count:
            logger.info("Database already contains data. Skipping seeding.")
            return

        # Create Admin User
        logger.info("Creating admin user...")
        admin_user_data = UserRegistration(
            email="admin@kcb.com",
            phone="+254700000000",
            password="AdminPassword123!",
            first_name="Admin",
            last_name="User"
        )
        admin_token_response = await auth_service.register_user(admin_user_data)
        admin_user_id = admin_token_response.user_id
        
        # Update admin user role directly (as registration defaults to CUSTOMER)
        admin_user_obj = (await session.execute(select(User).where(User.id == admin_user_id))).scalar_one()
        admin_user_obj.role = UserRole.ADMIN
        admin_user_obj.kyc_status = KYCStatus.VERIFIED
        admin_user_obj.is_verified = True
        await session.commit()
        await session.refresh(admin_user_obj)
        logger.info(f"Admin user '{admin_user_obj.email}' created and updated to role {admin_user_obj.role.value}")

        # Create Customer User
        logger.info("Creating customer user...")
        customer_user_data = UserRegistration(
            email="customer@kcb.com",
            phone="+254711111111",
            password="CustomerPassword123!",
            first_name="Customer",
            last_name="User"
        )
        customer_token_response = await auth_service.register_user(customer_user_data)
        customer_user_id = customer_token_response.user_id
        
        customer_user_obj = (await session.execute(select(User).where(User.id == customer_user_id))).scalar_one()
        customer_user_obj.kyc_status = KYCStatus.VERIFIED
        customer_user_obj.is_verified = True
        await session.commit()
        await session.refresh(customer_user_obj)
        logger.info(f"Customer user '{customer_user_obj.email}' created and verified.")

        # Create Merchant User
        logger.info("Creating merchant user...")
        merchant_user_data = UserRegistration(
            email="merchant@kcb.com",
            phone="+254722222222",
            password="MerchantPassword123!",
            first_name="Merchant",
            last_name="User"
        )
        merchant_token_response = await auth_service.register_user(merchant_user_data)
        merchant_user_id = merchant_token_response.user_id
        
        merchant_user_obj = (await session.execute(select(User).where(User.id == merchant_user_id))).scalar_one()
        merchant_user_obj.role = UserRole.MERCHANT # Role will be updated by merchant registration service
        merchant_user_obj.kyc_status = KYCStatus.VERIFIED
        merchant_user_obj.is_verified = True
        await session.commit()
        await session.refresh(merchant_user_obj)
        logger.info(f"Merchant user '{merchant_user_obj.email}' created and verified.")

        # Create Wallets for Customer
        logger.info("Creating wallets for customer...")
        await wallet_service.create_wallet(customer_user_id, {"currency": "KES", "name": "KES Wallet"})
        await wallet_service.create_wallet(customer_user_id, {"currency": "BTC", "name": "Bitcoin Wallet"})
        await wallet_service.create_wallet(customer_user_id, {"currency": "USDT", "name": "USDT Wallet"})
        
        # Fund customer KES wallet for testing
        customer_kes_wallet = (await session.execute(select(Wallet).where(Wallet.user_id == customer_user_id, Wallet.currency == "KES"))).scalar_one()
        customer_kes_wallet.balance = Decimal('50000.00')
        await session.commit()
        await session.refresh(customer_kes_wallet)
        logger.info(f"Customer KES wallet funded with {customer_kes_wallet.balance} KES.")

        # Create Wallets for Merchant
        logger.info("Creating wallets for merchant...")
        await wallet_service.create_wallet(merchant_user_id, {"currency": "KES", "name": "Merchant KES Wallet"})
        await wallet_service.create_wallet(merchant_user_id, {"currency": "USDT", "name": "Merchant USDT Wallet"})

        # Create Sample Transactions for Customer
        logger.info("Creating sample transactions for customer...")
        crypto_deposit_tx = Transaction(
            user_id=customer_user_id,
            transaction_type=TransactionType.CRYPTO_DEPOSIT,
            amount=0.005,
            currency="BTC",
            status=TransactionStatus.COMPLETED,
            network="bitcoin",
            blockchain_hash="0x" + "a" * 64,
            payment_address="1BitcoinAddressExample",
            confirmations=6,
            notes="Initial BTC deposit",
            completed_at=datetime.utcnow() - timedelta(days=5)
        )
        mpesa_deposit_tx = Transaction(
            user_id=customer_user_id,
            transaction_type=TransactionType.MPESA_DEPOSIT,
            amount=2500.00,
            currency="KES",
            status=TransactionStatus.COMPLETED,
            mpesa_phone="+254711111111",
            mpesa_reference="MPESA_REF_12345",
            mpesa_receipt="ABCDEF123",
            notes="M-Pesa top-up",
            completed_at=datetime.utcnow() - timedelta(days=2)
        )
        pending_crypto_tx = Transaction(
            user_id=customer_user_id,
            transaction_type=TransactionType.CRYPTO_DEPOSIT,
            amount=0.0001,
            currency="USDT",
            status=TransactionStatus.PENDING,
            network="ethereum",
            payment_address="0xEthereumAddressExample",
            notes="Pending USDT deposit",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

        session.add_all([crypto_deposit_tx, mpesa_deposit_tx, pending_crypto_tx])
        await session.commit()
        logger.info("Sample transactions created.")

    logger.info("Database seeding completed successfully.")

async def main():
    """Main function to run the seeding process."""
    # Ensure tables are created before seeding
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await seed_data()

if __name__ == "__main__":
    asyncio.run(main())
