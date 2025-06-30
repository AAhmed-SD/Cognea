-- Add last_synced_ts to flashcards and notes tables
ALTER TABLE flashcards ADD COLUMN IF NOT EXISTS last_synced_ts TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE notes ADD COLUMN IF NOT EXISTS last_synced_ts TIMESTAMP WITH TIME ZONE DEFAULT NOW();
-- Index for fast lookup
CREATE INDEX IF NOT EXISTS idx_flashcards_last_synced_ts ON flashcards(last_synced_ts);
CREATE INDEX IF NOT EXISTS idx_notes_last_synced_ts ON notes(last_synced_ts);

-- Migration: Add last_synced_ts column to notion_sync_status table
-- This column is used for echo prevention in webhooks

-- Add last_synced_ts column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'notion_sync_status' 
        AND column_name = 'last_synced_ts'
    ) THEN
        ALTER TABLE notion_sync_status ADD COLUMN last_synced_ts TIMESTAMP WITH TIME ZONE;
        
        -- Update existing records to have last_synced_ts = last_sync_time
        UPDATE notion_sync_status 
        SET last_synced_ts = last_sync_time 
        WHERE last_synced_ts IS NULL;
        
        -- Make the column NOT NULL after updating existing records
        ALTER TABLE notion_sync_status ALTER COLUMN last_synced_ts SET NOT NULL;
    END IF;
END $$;

-- Create index for echo prevention queries
CREATE INDEX IF NOT EXISTS idx_notion_sync_last_synced_ts 
ON notion_sync_status(last_synced_ts); 