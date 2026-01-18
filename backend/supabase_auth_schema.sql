-- MindMoney Auth Schema Additions
-- Run this AFTER the initial supabase_schema.sql
-- ============================================================================
-- Update conversation_turns to include user_id
-- ============================================================================
ALTER TABLE conversation_turns
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_user ON conversation_turns(user_id);
-- ============================================================================
-- Update sessions table to include user_id
-- ============================================================================
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
-- ============================================================================
-- Update agent_logs to include user_id (optional, for analytics)
-- ============================================================================
ALTER TABLE agent_logs
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);
-- ============================================================================
-- User Profiles Table (extends Supabase auth.users)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    display_name TEXT,
    avatar_url TEXT,
    -- User preferences
    preferred_tone TEXT DEFAULT 'supportive' CHECK (
        preferred_tone IN ('supportive', 'direct', 'balanced')
    ),
    show_agent_panel BOOLEAN DEFAULT false,
    -- Aggregated stats
    total_sessions INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
-- ============================================================================
-- Row Level Security Policies for User Data
-- ============================================================================
-- Drop old permissive policies
DROP POLICY IF EXISTS "Enable all access" ON conversation_turns;
DROP POLICY IF EXISTS "Enable all access" ON sessions;
DROP POLICY IF EXISTS "Enable all access" ON agent_logs;
-- Conversation turns: Users can only see their own
CREATE POLICY "Users can view own conversation turns" ON conversation_turns FOR
SELECT USING (
        auth.uid() = user_id
        OR user_id IS NULL
    );
CREATE POLICY "Users can insert own conversation turns" ON conversation_turns FOR
INSERT WITH CHECK (
        auth.uid() = user_id
        OR user_id IS NULL
    );
-- Sessions: Users can only see their own
CREATE POLICY "Users can view own sessions" ON sessions FOR
SELECT USING (
        auth.uid() = user_id
        OR user_id IS NULL
    );
CREATE POLICY "Users can insert own sessions" ON sessions FOR
INSERT WITH CHECK (
        auth.uid() = user_id
        OR user_id IS NULL
    );
CREATE POLICY "Users can update own sessions" ON sessions FOR
UPDATE USING (
        auth.uid() = user_id
        OR user_id IS NULL
    );
-- Agent logs: Users can only see their own
CREATE POLICY "Users can view own agent logs" ON agent_logs FOR
SELECT USING (
        auth.uid() = user_id
        OR user_id IS NULL
    );
CREATE POLICY "Users can insert own agent logs" ON agent_logs FOR
INSERT WITH CHECK (
        auth.uid() = user_id
        OR user_id IS NULL
    );
-- User profiles: Users can only manage their own
CREATE POLICY "Users can view own profile" ON user_profiles FOR
SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON user_profiles FOR
UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON user_profiles FOR
INSERT WITH CHECK (auth.uid() = id);
-- ============================================================================
-- Function: Auto-create user profile on signup
-- ============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user() RETURNS TRIGGER AS $$ BEGIN
INSERT INTO public.user_profiles (id, email, display_name)
VALUES (
        NEW.id,
        NEW.email,
        COALESCE(
            NEW.raw_user_meta_data->>'display_name',
            split_part(NEW.email, '@', 1)
        )
    );
RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
-- Trigger: Create profile when user signs up
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
AFTER
INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
-- ============================================================================
-- Function: Update user stats
-- ============================================================================
CREATE OR REPLACE FUNCTION update_user_stats() RETURNS TRIGGER AS $$ BEGIN
UPDATE user_profiles
SET total_messages = total_messages + 1,
    updated_at = NOW()
WHERE id = NEW.user_id;
RETURN NEW;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trigger_update_user_stats ON conversation_turns;
CREATE TRIGGER trigger_update_user_stats
AFTER
INSERT ON conversation_turns FOR EACH ROW
    WHEN (NEW.user_id IS NOT NULL) EXECUTE FUNCTION update_user_stats();