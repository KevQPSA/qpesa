# Backend (FastAPI)

This directory contains the FastAPI backend application for the Kenya Crypto-Fiat Payment Processor.

## Technologies Used

*   **Framework**: FastAPI
*   **Database**: PostgreSQL (via SQLAlchemy and AsyncPG)
*   **ORM**: SQLAlchemy 2.0 (async)
*   **Dependency Management**: Poetry
*   **Authentication**: JWT (JSON Web Tokens)
*   **Validation**: Pydantic
*   **Testing**: Pytest, httpx, pytest-asyncio, coverage
*   **Code Quality**: Black (formatter), Ruff (linter), MyPy (type checker), Bandit (security scanner)
*   **Database Migrations**: Alembic

## Development Setup

1.  **Navigate to the backend directory**:
    \`\`\`bash
    cd backend
    \`\`\`

2.  **Install Poetry**:
    If you don't have Poetry installed, follow the instructions on their official website: [https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation)

3.  **Install Dependencies**:
    \`\`\`bash
    poetry install
    \`\`\`
    This will install all project dependencies, including development ones.

4.  **Environment Variables**:
    Create a `.env` file in this directory based on `.env.example`.
    \`\`\`bash
    cp .env.example .env
    # Open .env and configure your database URL, JWT secret, M-Pesa credentials, etc.
    \`\`\`
    Ensure your `DATABASE_URL` points to your development PostgreSQL instance. If using Docker Compose for development, it will be `postgresql+asyncpg://kcb_user:kcb_password_secure@db:5432/kcb_crypto_fiat_dev_db`.

5.  **Database Setup (using Docker Compose for local DB)**:
    From the project root directory (one level up from `backend`), run:
    \`\`\`bash
    docker-compose -f docker-compose.dev.yml up --build -d db
    \`\`\`
    This will start a PostgreSQL container for development.

6.  **Run Database Migrations**:
    After the database container is up, apply the migrations to create tables:
    \`\`\`bash
    poetry run alembic upgrade head
    \`\`\`

7.  **Seed Database (Optional)**:
    If you need initial data for development:
    \`\`\`bash
    poetry run python scripts/seed_database.py
    \`\`\`

8.  **Run the Application**:
    \`\`\`bash
    poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    \`\`\`
    The API will be accessible at `http://localhost:8000`.
    Interactive API documentation (Swagger UI) will be available at `http://localhost:8000/api/docs`.

## Testing

The `run_tests.py` script provides a comprehensive suite for checking code quality and functionality.

To run all tests and checks:
\`\`\`bash
poetry run python run_tests.py
\`\`\`

Individual test commands (also part of `run_tests.py`):

*   **Run all Pytest tests**:
    \`\`\`bash
    poetry run pytest tests/
    \`\`\`
*   **Run specific test file**:
    \`\`\`bash
    poetry run pytest tests/test_auth_api.py
    \`\`\`
*   **Run tests with coverage report**:
    \`\`\`bash
    poetry run pytest --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml tests/
    \`\`\`
*   **Linting**:
    \`\`\`bash
    poetry run ruff check app/ tests/
    \`\`\`
*   **Formatting check**:
    \`\`\`bash
    poetry run black --check --diff app/ tests/
    \`\`\`
*   **Type checking**:
    \`\`\`bash
    poetry run mypy app/
    \`\`\`
*   **Security scan**:
    \`\`\`bash
    poetry run bandit -r app/ -f json -o bandit_report.json
    \`\`\`

## Database Migrations (Alembic)

Alembic is used for database schema migrations.

*   **Generate a new migration**:
    After making changes to your SQLAlchemy models (`app/models/`), run:
    \`\`\`bash
    poetry run alembic revision --autogenerate -m "descriptive_message_for_changes"
    \`\`\`
*   **Apply migrations**:
    To apply pending migrations to your database:
    \`\`\`bash
    poetry run alembic upgrade head
    \`\`\`
*   **Revert migrations**:
    To revert the last migration:
    \`\`\`bash
    poetry run alembic downgrade -1
    \`\`\`

## Docker

Dockerfiles are provided for different environments:

*   `Dockerfile`: Production build (optimized for size and performance).
*   `Dockerfile.dev`: Development build (includes hot-reloading, dev dependencies).
*   `Dockerfile.test`: Test environment build (includes test dependencies).

You can build images manually:
\`\`\`bash
docker build -f Dockerfile.dev -t kcb-backend-dev .
\`\`\`

## API Endpoints

(This section will be expanded with detailed API endpoint documentation as the project progresses.)

## Contributing

Contributions are welcome! Please follow the standard GitHub flow: fork the repository, create a feature branch, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License.
\`\`\`

```python file="backend/scripts/seed_database.py"
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
