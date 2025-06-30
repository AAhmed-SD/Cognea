-- Add last_synced_ts to flashcards and notes tables
ALTER TABLE flashcards ADD COLUMN IF NOT EXISTS last_synced_ts TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE notes ADD COLUMN IF NOT EXISTS last_synced_ts TIMESTAMP WITH TIME ZONE DEFAULT NOW();
-- Index for fast lookup
CREATE INDEX IF NOT EXISTS idx_flashcards_last_synced_ts ON flashcards(last_synced_ts);
CREATE INDEX IF NOT EXISTS idx_notes_last_synced_ts ON notes(last_synced_ts); 