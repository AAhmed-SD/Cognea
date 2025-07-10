-- Migration: Add Exam Paper Upload and Processing Tables
-- This migration creates all necessary tables for the exam paper upload system

-- Table for uploaded exam papers
CREATE TABLE IF NOT EXISTS uploaded_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    processing_status VARCHAR(50) DEFAULT 'processing' CHECK (processing_status IN ('processing', 'completed', 'failed')),
    extracted_questions_count INTEGER DEFAULT 0,
    ai_enhanced BOOLEAN DEFAULT FALSE,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for extracted questions from exam papers
CREATE TABLE IF NOT EXISTS extracted_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES uploaded_papers(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    answer_text TEXT,
    question_number INTEGER,
    marks INTEGER DEFAULT 1,
    topic VARCHAR(100),
    difficulty INTEGER DEFAULT 2 CHECK (difficulty >= 1 AND difficulty <= 5),
    ai_solution TEXT,
    ai_hints TEXT,
    confidence_score DECIMAL(3,2) DEFAULT 0.8 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    needs_review BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for user question collections
CREATE TABLE IF NOT EXISTS user_question_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    questions_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Junction table for collection-question relationships
CREATE TABLE IF NOT EXISTS collection_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID NOT NULL REFERENCES user_question_collections(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES extracted_questions(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(collection_id, question_id)
);

-- Table for collection sharing
CREATE TABLE IF NOT EXISTS collection_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID NOT NULL REFERENCES user_question_collections(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for upload agreements (legal compliance)
CREATE TABLE IF NOT EXISTS upload_agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    terms_accepted BOOLEAN DEFAULT TRUE,
    accepted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_uploaded_papers_user_id ON uploaded_papers(user_id);
CREATE INDEX IF NOT EXISTS idx_uploaded_papers_status ON uploaded_papers(processing_status);
CREATE INDEX IF NOT EXISTS idx_uploaded_papers_upload_date ON uploaded_papers(upload_date);

CREATE INDEX IF NOT EXISTS idx_extracted_questions_paper_id ON extracted_questions(paper_id);
CREATE INDEX IF NOT EXISTS idx_extracted_questions_topic ON extracted_questions(topic);
CREATE INDEX IF NOT EXISTS idx_extracted_questions_difficulty ON extracted_questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_extracted_questions_confidence ON extracted_questions(confidence_score);

CREATE INDEX IF NOT EXISTS idx_user_collections_user_id ON user_question_collections(user_id);
CREATE INDEX IF NOT EXISTS idx_user_collections_public ON user_question_collections(is_public);
CREATE INDEX IF NOT EXISTS idx_user_collections_created_at ON user_question_collections(created_at);

CREATE INDEX IF NOT EXISTS idx_collection_questions_collection_id ON collection_questions(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_questions_question_id ON collection_questions(question_id);

CREATE INDEX IF NOT EXISTS idx_collection_shares_collection_id ON collection_shares(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_shares_active ON collection_shares(is_active);
CREATE INDEX IF NOT EXISTS idx_collection_shares_expires ON collection_shares(expires_at);

CREATE INDEX IF NOT EXISTS idx_upload_agreements_user_id ON upload_agreements(user_id);
CREATE INDEX IF NOT EXISTS idx_upload_agreements_accepted_at ON upload_agreements(accepted_at);

-- Create RLS (Row Level Security) policies
ALTER TABLE uploaded_papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_question_collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_agreements ENABLE ROW LEVEL SECURITY;

-- Policies for uploaded_papers
CREATE POLICY "Users can view their own uploaded papers" ON uploaded_papers
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own uploaded papers" ON uploaded_papers
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own uploaded papers" ON uploaded_papers
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own uploaded papers" ON uploaded_papers
    FOR DELETE USING (auth.uid() = user_id);

-- Policies for extracted_questions
CREATE POLICY "Users can view questions from their own papers" ON extracted_questions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM uploaded_papers 
            WHERE uploaded_papers.id = extracted_questions.paper_id 
            AND uploaded_papers.user_id = auth.uid()
        )
    );

CREATE POLICY "System can insert extracted questions" ON extracted_questions
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update questions from their own papers" ON extracted_questions
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM uploaded_papers 
            WHERE uploaded_papers.id = extracted_questions.paper_id 
            AND uploaded_papers.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete questions from their own papers" ON extracted_questions
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM uploaded_papers 
            WHERE uploaded_papers.id = extracted_questions.paper_id 
            AND uploaded_papers.user_id = auth.uid()
        )
    );

-- Policies for user_question_collections
CREATE POLICY "Users can view their own collections" ON user_question_collections
    FOR SELECT USING (auth.uid() = user_id OR is_public = true);

CREATE POLICY "Users can insert their own collections" ON user_question_collections
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own collections" ON user_question_collections
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own collections" ON user_question_collections
    FOR DELETE USING (auth.uid() = user_id);

-- Policies for collection_questions
CREATE POLICY "Users can view questions in their own collections" ON collection_questions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_question_collections 
            WHERE user_question_collections.id = collection_questions.collection_id 
            AND (user_question_collections.user_id = auth.uid() OR user_question_collections.is_public = true)
        )
    );

CREATE POLICY "Users can manage questions in their own collections" ON collection_questions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_question_collections 
            WHERE user_question_collections.id = collection_questions.collection_id 
            AND user_question_collections.user_id = auth.uid()
        )
    );

-- Policies for collection_shares
CREATE POLICY "Users can view their own share links" ON collection_shares
    FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can view active share links for public collections" ON collection_shares
    FOR SELECT USING (
        is_active = true AND (
            auth.uid() = created_by OR
            EXISTS (
                SELECT 1 FROM user_question_collections 
                WHERE user_question_collections.id = collection_shares.collection_id 
                AND user_question_collections.is_public = true
            )
        )
    );

CREATE POLICY "Users can create share links for their own collections" ON collection_shares
    FOR INSERT WITH CHECK (
        auth.uid() = created_by AND
        EXISTS (
            SELECT 1 FROM user_question_collections 
            WHERE user_question_collections.id = collection_shares.collection_id 
            AND user_question_collections.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their own share links" ON collection_shares
    FOR UPDATE USING (auth.uid() = created_by);

-- Policies for upload_agreements
CREATE POLICY "Users can view their own upload agreements" ON upload_agreements
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own upload agreements" ON upload_agreements
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_uploaded_papers_updated_at 
    BEFORE UPDATE ON uploaded_papers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_extracted_questions_updated_at 
    BEFORE UPDATE ON extracted_questions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_collections_updated_at 
    BEFORE UPDATE ON user_question_collections 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update collection question count
CREATE OR REPLACE FUNCTION update_collection_question_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE user_question_collections 
        SET questions_count = questions_count + 1 
        WHERE id = NEW.collection_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE user_question_collections 
        SET questions_count = questions_count - 1 
        WHERE id = OLD.collection_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Create triggers for automatic collection count updates
CREATE TRIGGER update_collection_count_insert
    AFTER INSERT ON collection_questions
    FOR EACH ROW EXECUTE FUNCTION update_collection_question_count();

CREATE TRIGGER update_collection_count_delete
    AFTER DELETE ON collection_questions
    FOR EACH ROW EXECUTE FUNCTION update_collection_question_count();

-- Add TaskType enum for exam questions if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_type') THEN
        CREATE TYPE task_type AS ENUM (
            'general',
            'study_planning',
            'flashcard_generation',
            'goal_setting',
            'habit_tracking',
            'exam_question'
        );
    END IF;
END $$;

-- Grant necessary permissions
GRANT ALL ON uploaded_papers TO authenticated;
GRANT ALL ON extracted_questions TO authenticated;
GRANT ALL ON user_question_collections TO authenticated;
GRANT ALL ON collection_questions TO authenticated;
GRANT ALL ON collection_shares TO authenticated;
GRANT ALL ON upload_agreements TO authenticated;

-- Create uploads directory if it doesn't exist
-- Note: This is handled by the application code, but we can add a note here
COMMENT ON TABLE uploaded_papers IS 'Stores uploaded exam paper files. Physical files are stored in uploads/{user_id}/ directory.'; 