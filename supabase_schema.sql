-- Supabase Schema for Hoy Sports Data App
-- This schema supports user management, game sessions, plays, and comprehensive analytics

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for authentication and user management
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Game sessions table - each game/practice session
CREATE TABLE game_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_name VARCHAR(255),
    game_date DATE,
    opponent VARCHAR(255),
    location VARCHAR(255),
    weather_conditions TEXT,
    game_type VARCHAR(50) DEFAULT 'regular', -- regular, playoff, practice, scrimmage
    status VARCHAR(20) DEFAULT 'active', -- active, completed, archived
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Players table for roster management
CREATE TABLE players (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    number INTEGER NOT NULL,
    position VARCHAR(50),
    class_year VARCHAR(20), -- freshman, sophomore, junior, senior
    height VARCHAR(10),
    weight INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, number) -- Each user can have only one player with each number
);

-- Plays table - individual plays within game sessions
CREATE TABLE plays (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    play_number INTEGER NOT NULL,
    quarter INTEGER,
    down INTEGER,
    distance INTEGER,
    yard_line INTEGER,
    play_type VARCHAR(50), -- pass, rush, punt, kickoff, field_goal, etc.
    play_call VARCHAR(255),
    phase VARCHAR(20) NOT NULL, -- offense, defense, special_teams
    yards_gained INTEGER DEFAULT 0,
    result VARCHAR(50), -- completion, incompletion, touchdown, etc.
    time_remaining VARCHAR(10),
    score_home INTEGER DEFAULT 0,
    score_away INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Player involvement in plays (many-to-many relationship)
CREATE TABLE play_players (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    play_id UUID REFERENCES plays(id) ON DELETE CASCADE,
    player_id UUID REFERENCES players(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- rusher, passer, receiver, defender, etc.
    yards_gained INTEGER DEFAULT 0,
    is_touchdown BOOLEAN DEFAULT FALSE,
    is_fumble BOOLEAN DEFAULT FALSE,
    is_interception BOOLEAN DEFAULT FALSE,
    is_first_down BOOLEAN DEFAULT FALSE,
    is_penalty BOOLEAN DEFAULT FALSE,
    penalty_type VARCHAR(100),
    penalty_yards INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Team statistics aggregated by session and phase
CREATE TABLE team_stats (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    phase VARCHAR(20) NOT NULL, -- offense, defense, special_teams, overall
    total_plays INTEGER DEFAULT 0,
    total_yards INTEGER DEFAULT 0,
    passing_yards INTEGER DEFAULT 0,
    rushing_yards INTEGER DEFAULT 0,
    passing_plays INTEGER DEFAULT 0,
    rushing_plays INTEGER DEFAULT 0,
    touchdowns INTEGER DEFAULT 0,
    turnovers INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    fumbles INTEGER DEFAULT 0,
    first_downs INTEGER DEFAULT 0,
    efficient_plays INTEGER DEFAULT 0,
    explosive_plays INTEGER DEFAULT 0,
    negative_plays INTEGER DEFAULT 0,
    passing_efficient_plays INTEGER DEFAULT 0,
    passing_explosive_plays INTEGER DEFAULT 0,
    passing_negative_plays INTEGER DEFAULT 0,
    rushing_efficient_plays INTEGER DEFAULT 0,
    rushing_explosive_plays INTEGER DEFAULT 0,
    rushing_negative_plays INTEGER DEFAULT 0,
    efficiency_rate DECIMAL(5,2) DEFAULT 0.0,
    explosive_rate DECIMAL(5,2) DEFAULT 0.0,
    negative_rate DECIMAL(5,2) DEFAULT 0.0,
    passing_efficiency_rate DECIMAL(5,2) DEFAULT 0.0,
    passing_explosive_rate DECIMAL(5,2) DEFAULT 0.0,
    passing_negative_rate DECIMAL(5,2) DEFAULT 0.0,
    rushing_efficiency_rate DECIMAL(5,2) DEFAULT 0.0,
    rushing_explosive_rate DECIMAL(5,2) DEFAULT 0.0,
    rushing_negative_rate DECIMAL(5,2) DEFAULT 0.0,
    nee_score DECIMAL(6,2) DEFAULT 0.0,
    passing_nee_score DECIMAL(6,2) DEFAULT 0.0,
    rushing_nee_score DECIMAL(6,2) DEFAULT 0.0,
    avg_yards_per_play DECIMAL(5,2) DEFAULT 0.0,
    passing_avg_yards DECIMAL(5,2) DEFAULT 0.0,
    rushing_avg_yards DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, phase)
);

-- Player statistics aggregated by session
CREATE TABLE player_stats (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    player_id UUID REFERENCES players(id) ON DELETE CASCADE,
    total_plays INTEGER DEFAULT 0,
    rushing_yards INTEGER DEFAULT 0,
    passing_yards INTEGER DEFAULT 0,
    receiving_yards INTEGER DEFAULT 0,
    touchdowns INTEGER DEFAULT 0,
    fumbles INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    first_downs INTEGER DEFAULT 0,
    efficient_plays INTEGER DEFAULT 0,
    explosive_plays INTEGER DEFAULT 0,
    negative_plays INTEGER DEFAULT 0,
    efficiency_rate DECIMAL(5,2) DEFAULT 0.0,
    explosive_rate DECIMAL(5,2) DEFAULT 0.0,
    negative_rate DECIMAL(5,2) DEFAULT 0.0,
    nee_score DECIMAL(6,2) DEFAULT 0.0,
    avg_yards_per_play DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, player_id)
);

-- Play call analytics - track effectiveness of different play calls
CREATE TABLE play_call_stats (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    phase VARCHAR(20) NOT NULL,
    play_call VARCHAR(255) NOT NULL,
    total_plays INTEGER DEFAULT 0,
    total_yards INTEGER DEFAULT 0,
    touchdowns INTEGER DEFAULT 0,
    turnovers INTEGER DEFAULT 0,
    first_downs INTEGER DEFAULT 0,
    efficient_plays INTEGER DEFAULT 0,
    explosive_plays INTEGER DEFAULT 0,
    negative_plays INTEGER DEFAULT 0,
    efficiency_rate DECIMAL(5,2) DEFAULT 0.0,
    explosive_rate DECIMAL(5,2) DEFAULT 0.0,
    negative_rate DECIMAL(5,2) DEFAULT 0.0,
    nee_score DECIMAL(6,2) DEFAULT 0.0,
    avg_yards_per_play DECIMAL(5,2) DEFAULT 0.0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, phase, play_call)
);

-- Down and distance analytics
CREATE TABLE down_distance_stats (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    phase VARCHAR(20) NOT NULL,
    down INTEGER NOT NULL,
    distance_category VARCHAR(20) NOT NULL, -- short (1-3), medium (4-7), long (8+)
    total_plays INTEGER DEFAULT 0,
    total_yards INTEGER DEFAULT 0,
    touchdowns INTEGER DEFAULT 0,
    turnovers INTEGER DEFAULT 0,
    first_downs INTEGER DEFAULT 0,
    efficient_plays INTEGER DEFAULT 0,
    explosive_plays INTEGER DEFAULT 0,
    negative_plays INTEGER DEFAULT 0,
    passing_plays INTEGER DEFAULT 0,
    rushing_plays INTEGER DEFAULT 0,
    passing_efficient INTEGER DEFAULT 0,
    passing_explosive INTEGER DEFAULT 0,
    passing_negative INTEGER DEFAULT 0,
    rushing_efficient INTEGER DEFAULT 0,
    rushing_explosive INTEGER DEFAULT 0,
    rushing_negative INTEGER DEFAULT 0,
    efficiency_rate DECIMAL(5,2) DEFAULT 0.0,
    explosive_rate DECIMAL(5,2) DEFAULT 0.0,
    negative_rate DECIMAL(5,2) DEFAULT 0.0,
    nee_score DECIMAL(6,2) DEFAULT 0.0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, phase, down, distance_category)
);

-- Progressive analytics - track how stats change throughout the game
CREATE TABLE progressive_stats (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    phase VARCHAR(20) NOT NULL,
    play_number INTEGER NOT NULL,
    quarter INTEGER,
    efficiency_rate DECIMAL(5,2) DEFAULT 0.0,
    explosive_rate DECIMAL(5,2) DEFAULT 0.0,
    negative_rate DECIMAL(5,2) DEFAULT 0.0,
    nee_score DECIMAL(6,2) DEFAULT 0.0,
    total_plays INTEGER DEFAULT 0,
    total_yards INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data backup tracking table
CREATE TABLE data_backups (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    backup_type VARCHAR(50) NOT NULL, -- database, file, emergency
    backup_path TEXT,
    backup_size INTEGER,
    backup_status VARCHAR(20) DEFAULT 'active', -- active, archived, corrupted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_game_sessions_user_id ON game_sessions(user_id);
CREATE INDEX idx_game_sessions_status ON game_sessions(status);
CREATE INDEX idx_plays_session_id ON plays(session_id);
CREATE INDEX idx_plays_phase ON plays(phase);
CREATE INDEX idx_play_players_play_id ON play_players(play_id);
CREATE INDEX idx_play_players_player_id ON play_players(player_id);
CREATE INDEX idx_team_stats_session_id ON team_stats(session_id);
CREATE INDEX idx_player_stats_session_id ON player_stats(session_id);
CREATE INDEX idx_player_stats_player_id ON player_stats(player_id);
CREATE INDEX idx_progressive_stats_session_id ON progressive_stats(session_id);

-- Create updated_at triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_game_sessions_updated_at BEFORE UPDATE ON game_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_plays_updated_at BEFORE UPDATE ON plays FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_team_stats_updated_at BEFORE UPDATE ON team_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_player_stats_updated_at BEFORE UPDATE ON player_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies for multi-tenant data isolation
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE plays ENABLE ROW LEVEL SECURITY;
ALTER TABLE play_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE play_call_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE down_distance_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE progressive_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_backups ENABLE ROW LEVEL SECURITY;

-- Create policies for user data isolation
CREATE POLICY "Users can view own data" ON users FOR SELECT USING (auth.uid()::text = id::text);
CREATE POLICY "Users can update own data" ON users FOR UPDATE USING (auth.uid()::text = id::text);

CREATE POLICY "Users can view own sessions" ON game_sessions FOR SELECT USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can insert own sessions" ON game_sessions FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
CREATE POLICY "Users can update own sessions" ON game_sessions FOR UPDATE USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can delete own sessions" ON game_sessions FOR DELETE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can view own players" ON players FOR SELECT USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can insert own players" ON players FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
CREATE POLICY "Users can update own players" ON players FOR UPDATE USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can delete own players" ON players FOR DELETE USING (auth.uid()::text = user_id::text);

-- Policies for plays and related tables (access through session ownership)
CREATE POLICY "Users can view plays from own sessions" ON plays FOR SELECT 
USING (session_id IN (SELECT id FROM game_sessions WHERE user_id::text = auth.uid()::text));

CREATE POLICY "Users can insert plays to own sessions" ON plays FOR INSERT 
WITH CHECK (session_id IN (SELECT id FROM game_sessions WHERE user_id::text = auth.uid()::text));

CREATE POLICY "Users can update plays in own sessions" ON plays FOR UPDATE 
USING (session_id IN (SELECT id FROM game_sessions WHERE user_id::text = auth.uid()::text));

CREATE POLICY "Users can delete plays from own sessions" ON plays FOR DELETE 
USING (session_id IN (SELECT id FROM game_sessions WHERE user_id::text = auth.uid()::text));

-- Similar policies for all related tables
CREATE POLICY "Users can access play_players from own sessions" ON play_players FOR ALL 
USING (play_id IN (SELECT id FROM plays WHERE session_id IN (SELECT id FROM game_sessions WHERE user_id::text = auth.uid()::text)));

CREATE POLICY "Users can access team_stats from own sessions" ON team_stats FOR ALL 
USING (session_id IN (SELECT id FROM game_sessions WHERE user_id::text = auth.uid()::text));

CREATE POLICY "Users can access player_stats from own sessions" ON player_stats FOR ALL 
USING (session_id IN (SELECT id FROM game_sessions WHERE user_id::text = auth.uid()::text));

CREATE POLICY "Users can access play_call_stats from own sessions" ON play_call_stats FOR ALL 
USING (session_id IN (SELECT id FROM game_sessions WHERE user_id::text = auth.uid()::text));

CREATE POLICY "Users can access down_distance_stats from own sessions" ON down_distance_stats FOR ALL 
USING (session_id IN (SELECT id FROM game_sessions WHERE user_id::text = auth.uid()::text));

CREATE POLICY "Users can access progressive_stats from own sessions" ON progressive_stats FOR ALL 
USING (session_id IN (SELECT id FROM game_sessions WHERE user_id::text = auth.uid()::text));

CREATE POLICY "Users can access data_backups from own sessions" ON data_backups FOR ALL 
USING (session_id IN (SELECT id FROM game_sessions WHERE user_id::text = auth.uid()::text));

-- Insert default admin user (password should be hashed in production)
INSERT INTO users (username, password_hash, email, is_admin) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO5S8VyDe', 'admin@hoysportsdata.com', TRUE);

-- Create views for common queries
CREATE VIEW session_summary AS
SELECT 
    gs.id,
    gs.session_name,
    gs.game_date,
    gs.opponent,
    u.username,
    COUNT(p.id) as total_plays,
    SUM(CASE WHEN p.phase = 'offense' THEN 1 ELSE 0 END) as offensive_plays,
    SUM(CASE WHEN p.phase = 'defense' THEN 1 ELSE 0 END) as defensive_plays,
    SUM(CASE WHEN p.phase = 'special_teams' THEN 1 ELSE 0 END) as special_teams_plays,
    gs.status,
    gs.created_at
FROM game_sessions gs
LEFT JOIN users u ON gs.user_id = u.id
LEFT JOIN plays p ON gs.id = p.session_id
GROUP BY gs.id, gs.session_name, gs.game_date, gs.opponent, u.username, gs.status, gs.created_at;

CREATE VIEW player_performance_summary AS
SELECT 
    p.id,
    p.name,
    p.number,
    p.position,
    gs.session_name,
    ps.total_plays,
    ps.rushing_yards,
    ps.passing_yards,
    ps.receiving_yards,
    ps.touchdowns,
    ps.efficiency_rate,
    ps.explosive_rate,
    ps.negative_rate,
    ps.nee_score
FROM players p
LEFT JOIN player_stats ps ON p.id = ps.player_id
LEFT JOIN game_sessions gs ON ps.session_id = gs.id
WHERE p.is_active = TRUE;

-- Comments for documentation
COMMENT ON TABLE users IS 'User authentication and profile management';
COMMENT ON TABLE game_sessions IS 'Individual game or practice sessions';
COMMENT ON TABLE players IS 'Player roster and profile information';
COMMENT ON TABLE plays IS 'Individual plays within game sessions';
COMMENT ON TABLE play_players IS 'Many-to-many relationship between plays and players';
COMMENT ON TABLE team_stats IS 'Aggregated team statistics by phase and session';
COMMENT ON TABLE player_stats IS 'Aggregated player statistics by session';
COMMENT ON TABLE play_call_stats IS 'Analytics for different play calls and their effectiveness';
COMMENT ON TABLE down_distance_stats IS 'Performance analytics by down and distance situations';
COMMENT ON TABLE progressive_stats IS 'How statistics evolve throughout the game';
COMMENT ON TABLE data_backups IS 'Tracking of data backup operations for reliability';
