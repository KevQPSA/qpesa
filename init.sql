-- init.sql
-- This script is for initializing the production database.
-- It should be run once to create the database and user.
-- For schema migrations, Alembic should be used.

-- Create the database if it doesn't exist
SELECT 'CREATE DATABASE kcb_crypto_fiat_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'kcb_crypto_fiat_db')\gexec

-- Create a dedicated user for the application
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
      CREATE USER app_user WITH PASSWORD 'your_strong_password_here';
   END IF;
END
$do$;

-- Grant privileges to the user on the database
GRANT ALL PRIVILEGES ON DATABASE kcb_crypto_fiat_db TO app_user;

-- Connect to the newly created database to set up schema ownership
\c kcb_crypto_fiat_db;

-- Grant all privileges on future tables to the app_user
ALTER DEFAULT PRIVILEGES FOR USER app_user IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES FOR USER app_user IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO app_user;
ALTER DEFAULT PRIVILEGES FOR USER app_user IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO app_user;

-- Ensure the app_user is the owner of the schema
ALTER SCHEMA public OWNER TO app_user;

-- Optional: Create extensions if needed (e.g., for UUIDs)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
