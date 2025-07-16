-- init-test.sql
-- This script is executed when the PostgreSQL test container starts for the first time.
-- It's specifically for the test database.

-- Create a new database for the test environment
CREATE DATABASE kcb_crypto_fiat_test_db;

-- Create a user for the application with a strong password
CREATE USER kcb_user WITH PASSWORD 'kcb_password_secure';

-- Grant all privileges on the new database to the new user
GRANT ALL PRIVILEGES ON DATABASE kcb_crypto_fiat_test_db TO kcb_user;

-- Enable uuid-ossp extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
