-- Database initialization script for Kreeda Backend
-- This script sets up the database with necessary extensions and initial configurations

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create database user if it doesn't exist (for development)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'kreeda_user') THEN
        CREATE ROLE kreeda_user WITH LOGIN PASSWORD 'kreeda_password';
    END IF;
END
$$;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE kreeda_dev TO kreeda_user;
GRANT USAGE ON SCHEMA public TO kreeda_user;
GRANT CREATE ON SCHEMA public TO kreeda_user;

-- Set default search path
ALTER DATABASE kreeda_dev SET search_path TO public;

-- Create indexes for performance (these will be created by Alembic migrations as well)
-- This is just to ensure database is ready for development

-- Log successful initialization
INSERT INTO pg_stat_statements_info (dealloc) VALUES (0) ON CONFLICT DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Kreeda database initialized successfully';
END
$$;