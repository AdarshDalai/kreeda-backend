-- Kreeda Database Initialization Script
-- This creates the initial database structure

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant permissions (already handled by postgres image)
-- GRANT ALL PRIVILEGES ON DATABASE kreeda_db TO kreeda_user;

-- The tables will be created by Alembic migrations
