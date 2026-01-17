-- MindMoney Supabase Schema
-- Run this in your Supabase SQL Editor to create the required tables
-- ============================================================================
-- Conversation Turns Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS conversation_turns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    turn_number INTEGER NOT NULL,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    -- Intake metrics (from Gemini agent)
    intake_anxiety INTEGER CHECK (
        intake_anxiety >= 0
        AND intake_anxiety <= 10
    ),
    intake_shame INTEGER CHECK (
        intake_shame >= 0
        AND intake_shame <= 10
    ),
    safety_flag BOOLEAN DEFAULT FALSE,
    -- Strategy metrics (from Synthesizer)
    strategy_mode TEXT CHECK (
        strategy_mode IN (
            'de_escalation',
            'simplified',
            'full_plan',
            'crisis_support'
        )
    ),
    -- Financial metrics (from Anthropic agent)
    entities_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_session_turn UNIQUE (session_id, turn_number)
);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_session ON conversation_turns(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_created ON conversation_turns(created_at);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_safety ON conversation_turns(safety_flag)
WHERE safety_flag = TRUE;
-- ============================================================================
-- Agent Logs Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    turn_id UUID REFERENCES conversation_turns(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL CHECK (
        agent_name IN (
            'intake_specialist',
            'financial_planner',
            'synthesizer'
        )
    ),
    model_used TEXT,
    input_summary TEXT,
    output_summary TEXT,
    decision_made TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agent_logs_session ON agent_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_turn ON agent_logs(turn_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_agent ON agent_logs(agent_name);
-- ============================================================================
-- Sessions Table (Optional)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    first_message_at TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    total_turns INTEGER DEFAULT 0,
    avg_anxiety DECIMAL(3, 1),
    max_anxiety INTEGER,
    had_safety_flag BOOLEAN DEFAULT FALSE,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
-- ============================================================================
-- Row Level Security
-- ============================================================================
ALTER TABLE conversation_turns ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
-- Policies for development (adjust for production)
CREATE POLICY "Enable all access" ON conversation_turns FOR ALL USING (true);
CREATE POLICY "Enable all access" ON agent_logs FOR ALL USING (true);
CREATE POLICY "Enable all access" ON sessions FOR ALL USING (true);
-- ============================================================================
-- Useful Views
-- ============================================================================
CREATE OR REPLACE VIEW session_summaries AS
SELECT session_id,
    COUNT(*) as total_turns,
    MIN(created_at) as first_message,
    MAX(created_at) as last_message,
    AVG(intake_anxiety) as avg_anxiety,
    MAX(intake_anxiety) as max_anxiety,
    AVG(intake_shame) as avg_shame,
    BOOL_OR(safety_flag) as had_safety_flag,
    MODE() WITHIN GROUP (
        ORDER BY strategy_mode
    ) as most_common_strategy
FROM conversation_turns
GROUP BY session_id;
CREATE OR REPLACE VIEW agent_performance AS
SELECT agent_name,
    COUNT(*) as total_calls,
    AVG(duration_ms) as avg_duration_ms,
    MIN(duration_ms) as min_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (
        ORDER BY duration_ms
    ) as p95_duration_ms
FROM agent_logs
WHERE duration_ms IS NOT NULL
GROUP BY agent_name;
-- ============================================================================
-- Auto-update session stats trigger
-- ============================================================================
CREATE OR REPLACE FUNCTION update_session_stats() RETURNS TRIGGER AS $$ BEGIN
INSERT INTO sessions (
        session_id,
        first_message_at,
        last_message_at,
        total_turns,
        had_safety_flag
    )
VALUES (
        NEW.session_id,
        NEW.created_at,
        NEW.created_at,
        1,
        NEW.safety_flag
    ) ON CONFLICT (session_id) DO
UPDATE
SET last_message_at = NEW.created_at,
    total_turns = sessions.total_turns + 1,
    had_safety_flag = sessions.had_safety_flag
    OR NEW.safety_flag;
RETURN NEW;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trigger_update_session_stats ON conversation_turns;
CREATE TRIGGER trigger_update_session_stats
AFTER
INSERT ON conversation_turns FOR EACH ROW EXECUTE FUNCTION update_session_stats();