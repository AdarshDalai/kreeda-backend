-- Initialize Kreeda Database
-- This script runs automatically when the database is first created

-- Ensure required extensions are available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the main database if it doesn't exist
-- (This is handled by docker-compose environment variables)

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sport VARCHAR(50) NOT NULL,
    logo_url TEXT,
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tournaments table
CREATE TABLE IF NOT EXISTS tournaments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sport VARCHAR(50) NOT NULL,
    tournament_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'upcoming',
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(id),
    max_teams INTEGER,
    entry_fee DECIMAL(10,2) DEFAULT 0,
    prize_pool DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tournament_id UUID REFERENCES tournaments(id),
    team_a_id UUID REFERENCES teams(id),
    team_b_id UUID REFERENCES teams(id),
    sport VARCHAR(50) NOT NULL,
    match_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    venue VARCHAR(255),
    weather_conditions JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scores table
CREATE TABLE IF NOT EXISTS scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES matches(id),
    team_id UUID REFERENCES teams(id),
    sport VARCHAR(50) NOT NULL,
    score_data JSONB NOT NULL,
    innings INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_teams_sport ON teams(sport);
CREATE INDEX IF NOT EXISTS idx_tournaments_sport ON tournaments(sport);
CREATE INDEX IF NOT EXISTS idx_tournaments_status ON tournaments(status);
CREATE INDEX IF NOT EXISTS idx_matches_tournament_id ON matches(tournament_id);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_scores_match_id ON scores(match_id);

-- Insert some sample data for development
INSERT INTO users (id, email, username, full_name, phone) VALUES 
    (uuid_generate_v4(), 'admin@kreeda.com', 'admin', 'Kreeda Admin', '+91-9999999999')
ON CONFLICT (email) DO NOTHING;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Kreeda database initialized successfully! 🏏';
END $$;
