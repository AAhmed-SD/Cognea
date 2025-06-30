-- Migration: Add flashcard cache table for cost control
-- This table caches generated flashcards to reduce OpenAI API costs

CREATE TABLE IF NOT EXISTS flashcard_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cache_key TEXT NOT NULL UNIQUE,
    flashcards JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 hours')
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_flashcard_cache_key ON flashcard_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_flashcard_cache_created_at ON flashcard_cache(created_at);
CREATE INDEX IF NOT EXISTS idx_flashcard_cache_expires_at ON flashcard_cache(expires_at);

-- Add RLS (Row Level Security) policies
ALTER TABLE flashcard_cache ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all authenticated users to read/write cache
CREATE POLICY "Allow authenticated users to access flashcard cache" ON flashcard_cache
    FOR ALL USING (auth.role() = 'authenticated');

-- Add trigger to automatically clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_flashcard_cache()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM flashcard_cache WHERE expires_at < NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_clean_expired_flashcard_cache
    AFTER INSERT ON flashcard_cache
    FOR EACH ROW
    EXECUTE FUNCTION clean_expired_flashcard_cache();

-- Create a function to manually clean expired cache (can be called periodically)
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM flashcard_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql; 