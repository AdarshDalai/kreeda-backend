-- Initialize PostgreSQL extensions for Kreeda backend
-- This script runs automatically when the database container starts for the first time

-- Enable UUID generation functions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable trigram similarity for fuzzy text search (useful for player/team search)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable pg_stat_statements for query performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Kreeda database extensions initialized successfully';
END $$;
