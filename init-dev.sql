-- Development database initialization
-- This script is executed when the PostgreSQL development container starts for the first time.
-- It's similar to init.sql but for the development database.

-- Create a new database for the development environment
CREATE DATABASE kcb_crypto_fiat_dev_db;

-- Create a user for the application with a strong password
CREATE USER kcb_user WITH PASSWORD 'kcb_password_secure';

-- Grant all privileges on the new database to the new user
GRANT ALL PRIVILEGES ON DATABASE kcb_crypto_fiat_dev_db TO kcb_user;

-- Set timezone to UTC for consistency
SET timezone = 'UTC';

-- Create extensions for UUID and other utilities
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create development-specific functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Set up proper permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kcb_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kcb_user;

-- Create development seed data (will be added by migrations)
