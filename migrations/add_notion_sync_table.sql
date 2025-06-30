-- Migration: Add Notion sync status table
-- This table tracks synchronization status between Cognie and Notion

CREATE TABLE IF NOT EXISTS notion_sync_status (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    notion_page_id TEXT NOT NULL,
    last_sync_time TIMESTAMP WITH TIME ZONE NOT NULL,
    sync_direction TEXT NOT NULL CHECK (sync_direction IN ('notion_to_cognie', 'cognie_to_notion', 'bidirectional')),
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'in_progress')),
    error_message TEXT,
    items_synced INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_notion_sync_user_id ON notion_sync_status(user_id);
CREATE INDEX IF NOT EXISTS idx_notion_sync_page_id ON notion_sync_status(notion_page_id);
CREATE INDEX IF NOT EXISTS idx_notion_sync_last_sync_time ON notion_sync_status(last_sync_time);

-- Create unique constraint to prevent duplicate sync records for same user/page
CREATE UNIQUE INDEX IF NOT EXISTS idx_notion_sync_user_page_unique ON notion_sync_status(user_id, notion_page_id);

-- Add RLS (Row Level Security) policies
ALTER TABLE notion_sync_status ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own sync status
CREATE POLICY "Users can view own notion sync status" ON notion_sync_status
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can insert their own sync status
CREATE POLICY "Users can insert own notion sync status" ON notion_sync_status
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own sync status
CREATE POLICY "Users can update own notion sync status" ON notion_sync_status
    FOR UPDATE USING (auth.uid() = user_id);

-- Policy: Users can delete their own sync status
CREATE POLICY "Users can delete own notion sync status" ON notion_sync_status
    FOR DELETE USING (auth.uid() = user_id);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_notion_sync_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_notion_sync_updated_at
    BEFORE UPDATE ON notion_sync_status
    FOR EACH ROW
    EXECUTE FUNCTION update_notion_sync_updated_at();

-- Add notion_api_key column to user_settings if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_settings' 
        AND column_name = 'notion_api_key'
    ) THEN
        ALTER TABLE user_settings ADD COLUMN notion_api_key TEXT;
    END IF;
END $$;

-- Add unique indexes to prevent duplicates and race conditions
CREATE UNIQUE INDEX IF NOT EXISTS idx_notion_connections_user_workspace 
ON notion_connections(user_id, workspace_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_notion_sync_status_user_page 
ON notion_sync_status(user_id, notion_page_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_flashcards_user_source 
ON flashcards(user_id, source_page_id) WHERE source_page_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_flashcards_user_source_db 
ON flashcards(user_id, source_database_id) WHERE source_database_id IS NOT NULL;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_notion_connections_workspace_id 
ON notion_connections(workspace_id);

CREATE INDEX IF NOT EXISTS idx_notion_sync_status_last_synced 
ON notion_sync_status(last_synced_ts);

CREATE INDEX IF NOT EXISTS idx_flashcards_source_page 
ON flashcards(source_page_id) WHERE source_page_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_flashcards_source_database 
ON flashcards(source_database_id) WHERE source_database_id IS NOT NULL; 