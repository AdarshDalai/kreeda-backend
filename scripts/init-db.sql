#!/bin/bash
# Database initialization script for PostgreSQL

set -e

# Create extensions if they don't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable UUID extension for generating UUIDs
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    
    -- Enable pgcrypto for password hashing
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    
    -- Enable citext for case-insensitive text
    CREATE EXTENSION IF NOT EXISTS "citext";
    
    -- Create initial schema if needed
    CREATE SCHEMA IF NOT EXISTS public;
    
    -- Grant permissions
    GRANT ALL PRIVILEGES ON DATABASE kreeda TO kreeda;
    GRANT ALL PRIVILEGES ON SCHEMA public TO kreeda;
EOSQL

echo "Database initialization completed successfully!"