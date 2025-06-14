-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- For encryption support

-- Create enum types
CREATE TYPE priority_level AS ENUM ('low', 'medium', 'high');
CREATE TYPE feedback_frequency AS ENUM ('daily', 'weekly', 'monthly');
CREATE TYPE notification_type AS ENUM ('reminder', 'alert', 'system');
CREATE TYPE notification_category AS ENUM ('task', 'goal', 'system', 'alert');
CREATE TYPE repeat_interval AS ENUM ('daily', 'weekly', 'monthly', 'custom');
CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'completed', 'cancelled');
CREATE TYPE command_action AS ENUM ('summarize_notes', 'create_flashcards', 'unknown');
CREATE TYPE energy_level AS ENUM ('low', 'medium', 'high');
CREATE TYPE mood_type AS ENUM ('very_happy', 'happy', 'neutral', 'sad', 'very_sad');
CREATE TYPE sync_direction AS ENUM ('push', 'pull', 'both');
CREATE TYPE sync_status AS ENUM ('pending', 'success', 'failed', 'conflict');
CREATE TYPE feature_mode AS ENUM ('focus', 'relax', 'study', 'work', 'custom');
CREATE TYPE resource_type AS ENUM ('article', 'video', 'book', 'course', 'tool');
CREATE TYPE resource_trust_level AS ENUM ('verified', 'peer_reviewed', 'community', 'unverified');
CREATE TYPE data_export_format AS ENUM ('csv', 'json', 'pdf');

-- Create users table (extends Supabase auth.users)
CREATE TABLE public.users (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    preferences JSONB DEFAULT '{}'::jsonb,
    energy_curve JSONB DEFAULT '{}'::jsonb,
    default_scheduling_rules JSONB DEFAULT '{}'::jsonb,
    smart_planning_enabled BOOLEAN DEFAULT true,
    encryption_enabled BOOLEAN DEFAULT false,
    encryption_key TEXT,
    gdpr_consent_log JSONB DEFAULT '[]'::jsonb
);

-- Create tasks table
CREATE TABLE public.tasks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status task_status DEFAULT 'pending',
    due_date TIMESTAMP WITH TIME ZONE,
    priority priority_level DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create goals table
CREATE TABLE public.goals (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    due_date TIMESTAMP WITH TIME ZONE,
    priority priority_level DEFAULT 'medium',
    status TEXT DEFAULT 'Not Started',
    progress INTEGER DEFAULT 0,
    is_starred BOOLEAN DEFAULT false,
    analytics JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create schedule_blocks table
CREATE TABLE public.schedule_blocks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    context TEXT DEFAULT 'Work',
    goal_id UUID REFERENCES public.goals(id),
    is_fixed BOOLEAN DEFAULT false,
    is_rescheduled BOOLEAN DEFAULT false,
    rescheduled_count INTEGER DEFAULT 0,
    color_code TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create flashcards table
CREATE TABLE public.flashcards (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    tags TEXT[],
    deck_id UUID,
    deck_name TEXT,
    last_reviewed_at TIMESTAMP WITH TIME ZONE,
    next_review_date TIMESTAMP WITH TIME ZONE,
    ease_factor FLOAT DEFAULT 2.5,
    interval INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create notifications table
CREATE TABLE public.notifications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    send_time TIMESTAMP WITH TIME ZONE NOT NULL,
    type notification_type DEFAULT 'reminder',
    category notification_category DEFAULT 'task',
    is_sent BOOLEAN DEFAULT false,
    is_read BOOLEAN DEFAULT false,
    repeat_interval repeat_interval,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create user_settings table
CREATE TABLE public.user_settings (
    user_id UUID REFERENCES public.users(id) PRIMARY KEY,
    feedback_topics TEXT[],
    feedback_frequency feedback_frequency DEFAULT 'weekly',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create feedback_history table
CREATE TABLE public.feedback_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    feedback TEXT NOT NULL,
    suggestions TEXT[],
    acknowledgment_status BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create ai_commands table
CREATE TABLE public.ai_commands (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    command TEXT NOT NULL,
    action command_action NOT NULL,
    context JSONB DEFAULT '{}'::jsonb,
    result JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create notion_sync table
CREATE TABLE public.notion_sync (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    last_sync_time TIMESTAMP WITH TIME ZONE,
    sync_status TEXT DEFAULT 'pending',
    sync_type TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create journal_entries table
CREATE TABLE public.journal_entries (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    content TEXT NOT NULL,
    encrypted_content TEXT,
    mood mood_type,
    tags TEXT[],
    sentiment_score FLOAT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create journal_versions table
CREATE TABLE public.journal_versions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    entry_id UUID REFERENCES public.journal_entries(id) NOT NULL,
    content TEXT NOT NULL,
    version INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create habits table
CREATE TABLE public.habits (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    streak_count INTEGER DEFAULT 0,
    streak_freeze_count INTEGER DEFAULT 0,
    energy_level energy_level DEFAULT 'medium',
    impact_score FLOAT DEFAULT 0,
    reminders JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create habit_logs table
CREATE TABLE public.habit_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    habit_id UUID REFERENCES public.habits(id) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    mood_before mood_type,
    mood_after mood_type,
    energy_level energy_level,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create mood_logs table
CREATE TABLE public.mood_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    mood mood_type NOT NULL,
    emoji TEXT,
    notes TEXT,
    voice_memo_url TEXT,
    image_url TEXT,
    prompt_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create mood_prompts table
CREATE TABLE public.mood_prompts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    prompt_text TEXT NOT NULL,
    frequency TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create analytics_reports table
CREATE TABLE public.analytics_reports (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    report_type TEXT NOT NULL,
    report_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create feature_preferences table
CREATE TABLE public.feature_preferences (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    feature_name TEXT NOT NULL,
    is_enabled BOOLEAN DEFAULT true,
    mode feature_mode,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create resources table
CREATE TABLE public.resources (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    type resource_type NOT NULL,
    trust_level resource_trust_level DEFAULT 'unverified',
    url TEXT,
    tags TEXT[],
    difficulty_level INTEGER,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create resource_engagements table
CREATE TABLE public.resource_engagements (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    resource_id UUID REFERENCES public.resources(id) NOT NULL,
    engagement_type TEXT NOT NULL,
    duration INTEGER,
    completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create fitness_logs table
CREATE TABLE public.fitness_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    activity_type TEXT NOT NULL,
    duration INTEGER,
    intensity INTEGER,
    calories_burned INTEGER,
    steps INTEGER,
    sleep_duration INTEGER,
    source TEXT,
    source_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create sync_logs table
CREATE TABLE public.sync_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    service TEXT NOT NULL,
    direction sync_direction NOT NULL,
    status sync_status NOT NULL,
    error_message TEXT,
    items_synced INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create data_exports table
CREATE TABLE public.data_exports (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    format data_export_format NOT NULL,
    data_types TEXT[] NOT NULL,
    file_url TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create RLS (Row Level Security) policies
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.schedule_blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.flashcards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedback_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_commands ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notion_sync ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.journal_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.habits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.habit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mood_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mood_prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analytics_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feature_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resource_engagements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fitness_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sync_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_exports ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
CREATE POLICY "Users can view their own data"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own data"
    ON public.users FOR UPDATE
    USING (auth.uid() = id);

-- Create policies for tasks table
CREATE POLICY "Users can view their own tasks"
    ON public.tasks FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own tasks"
    ON public.tasks FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own tasks"
    ON public.tasks FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own tasks"
    ON public.tasks FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for goals table
CREATE POLICY "Users can view their own goals"
    ON public.goals FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own goals"
    ON public.goals FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own goals"
    ON public.goals FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own goals"
    ON public.goals FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for schedule_blocks table
CREATE POLICY "Users can view their own schedule blocks"
    ON public.schedule_blocks FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own schedule blocks"
    ON public.schedule_blocks FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own schedule blocks"
    ON public.schedule_blocks FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own schedule blocks"
    ON public.schedule_blocks FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for flashcards table
CREATE POLICY "Users can view their own flashcards"
    ON public.flashcards FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own flashcards"
    ON public.flashcards FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own flashcards"
    ON public.flashcards FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own flashcards"
    ON public.flashcards FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for notifications table
CREATE POLICY "Users can view their own notifications"
    ON public.notifications FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own notifications"
    ON public.notifications FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own notifications"
    ON public.notifications FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own notifications"
    ON public.notifications FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for user_settings table
CREATE POLICY "Users can view their own settings"
    ON public.user_settings FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own settings"
    ON public.user_settings FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own settings"
    ON public.user_settings FOR UPDATE
    USING (auth.uid() = user_id);

-- Create policies for feedback_history table
CREATE POLICY "Users can view their own feedback history"
    ON public.feedback_history FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own feedback history"
    ON public.feedback_history FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Create policies for ai_commands table
CREATE POLICY "Users can view their own ai commands"
    ON public.ai_commands FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own ai commands"
    ON public.ai_commands FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Create policies for notion_sync table
CREATE POLICY "Users can view their own notion syncs"
    ON public.notion_sync FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own notion syncs"
    ON public.notion_sync FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Create policies for journal_entries table
CREATE POLICY "Users can view their own journal entries"
    ON public.journal_entries FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own journal entries"
    ON public.journal_entries FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own journal entries"
    ON public.journal_entries FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own journal entries"
    ON public.journal_entries FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for journal_versions table
CREATE POLICY "Users can view their own journal versions"
    ON public.journal_versions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own journal versions"
    ON public.journal_versions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own journal versions"
    ON public.journal_versions FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own journal versions"
    ON public.journal_versions FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for habits table
CREATE POLICY "Users can view their own habits"
    ON public.habits FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own habits"
    ON public.habits FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own habits"
    ON public.habits FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own habits"
    ON public.habits FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for habit_logs table
CREATE POLICY "Users can view their own habit logs"
    ON public.habit_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own habit logs"
    ON public.habit_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own habit logs"
    ON public.habit_logs FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own habit logs"
    ON public.habit_logs FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for mood_logs table
CREATE POLICY "Users can view their own mood logs"
    ON public.mood_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own mood logs"
    ON public.mood_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own mood logs"
    ON public.mood_logs FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own mood logs"
    ON public.mood_logs FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for mood_prompts table
CREATE POLICY "Users can view their own mood prompts"
    ON public.mood_prompts FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own mood prompts"
    ON public.mood_prompts FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own mood prompts"
    ON public.mood_prompts FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own mood prompts"
    ON public.mood_prompts FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for analytics_reports table
CREATE POLICY "Users can view their own analytics reports"
    ON public.analytics_reports FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own analytics reports"
    ON public.analytics_reports FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own analytics reports"
    ON public.analytics_reports FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own analytics reports"
    ON public.analytics_reports FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for feature_preferences table
CREATE POLICY "Users can view their own feature preferences"
    ON public.feature_preferences FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own feature preferences"
    ON public.feature_preferences FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own feature preferences"
    ON public.feature_preferences FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own feature preferences"
    ON public.feature_preferences FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for resources table
CREATE POLICY "Users can view their own resources"
    ON public.resources FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own resources"
    ON public.resources FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own resources"
    ON public.resources FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own resources"
    ON public.resources FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for resource_engagements table
CREATE POLICY "Users can view their own resource engagements"
    ON public.resource_engagements FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own resource engagements"
    ON public.resource_engagements FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own resource engagements"
    ON public.resource_engagements FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own resource engagements"
    ON public.resource_engagements FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for fitness_logs table
CREATE POLICY "Users can view their own fitness logs"
    ON public.fitness_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own fitness logs"
    ON public.fitness_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own fitness logs"
    ON public.fitness_logs FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own fitness logs"
    ON public.fitness_logs FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for sync_logs table
CREATE POLICY "Users can view their own sync logs"
    ON public.sync_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sync logs"
    ON public.sync_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own sync logs"
    ON public.sync_logs FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own sync logs"
    ON public.sync_logs FOR DELETE
    USING (auth.uid() = user_id);

-- Create policies for data_exports table
CREATE POLICY "Users can view their own data exports"
    ON public.data_exports FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own data exports"
    ON public.data_exports FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own data exports"
    ON public.data_exports FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own data exports"
    ON public.data_exports FOR DELETE
    USING (auth.uid() = user_id);

-- Create indexes for better query performance
CREATE INDEX idx_tasks_user_id ON public.tasks(user_id);
CREATE INDEX idx_goals_user_id ON public.goals(user_id);
CREATE INDEX idx_schedule_blocks_user_id ON public.schedule_blocks(user_id);
CREATE INDEX idx_flashcards_user_id ON public.flashcards(user_id);
CREATE INDEX idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX idx_feedback_history_user_id ON public.feedback_history(user_id);
CREATE INDEX idx_ai_commands_user_id ON public.ai_commands(user_id);
CREATE INDEX idx_notion_sync_user_id ON public.notion_sync(user_id);
CREATE INDEX idx_tasks_due_date ON public.tasks(due_date);
CREATE INDEX idx_goals_due_date ON public.goals(due_date);
CREATE INDEX idx_schedule_blocks_dates ON public.schedule_blocks(start_time, end_time);
CREATE INDEX idx_flashcards_next_review ON public.flashcards(next_review_date);
CREATE INDEX idx_notifications_send_time ON public.notifications(send_time);
CREATE INDEX idx_journal_entries_user_id ON public.journal_entries(user_id);
CREATE INDEX idx_journal_entries_tags ON public.journal_entries USING GIN(tags);
CREATE INDEX idx_habits_user_id ON public.habits(user_id);
CREATE INDEX idx_habit_logs_habit_id ON public.habit_logs(habit_id);
CREATE INDEX idx_mood_logs_user_id ON public.mood_logs(user_id);
CREATE INDEX idx_analytics_reports_user_id ON public.analytics_reports(user_id);
CREATE INDEX idx_feature_preferences_user_id ON public.feature_preferences(user_id);
CREATE INDEX idx_resources_tags ON public.resources USING GIN(tags);
CREATE INDEX idx_resource_engagements_user_id ON public.resource_engagements(user_id);
CREATE INDEX idx_fitness_logs_user_id ON public.fitness_logs(user_id);
CREATE INDEX idx_sync_logs_user_id ON public.sync_logs(user_id);
CREATE INDEX idx_data_exports_user_id ON public.data_exports(user_id);

-- Create functions for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updating timestamps
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON public.tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_goals_updated_at
    BEFORE UPDATE ON public.goals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_schedule_blocks_updated_at
    BEFORE UPDATE ON public.schedule_blocks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_flashcards_updated_at
    BEFORE UPDATE ON public.flashcards
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notifications_updated_at
    BEFORE UPDATE ON public.notifications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at
    BEFORE UPDATE ON public.user_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feedback_history_updated_at
    BEFORE UPDATE ON public.feedback_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_commands_updated_at
    BEFORE UPDATE ON public.ai_commands
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notion_sync_updated_at
    BEFORE UPDATE ON public.notion_sync
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_journal_entries_updated_at
    BEFORE UPDATE ON public.journal_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_journal_versions_updated_at
    BEFORE UPDATE ON public.journal_versions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_habits_updated_at
    BEFORE UPDATE ON public.habits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_habit_logs_updated_at
    BEFORE UPDATE ON public.habit_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mood_logs_updated_at
    BEFORE UPDATE ON public.mood_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mood_prompts_updated_at
    BEFORE UPDATE ON public.mood_prompts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analytics_reports_updated_at
    BEFORE UPDATE ON public.analytics_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feature_preferences_updated_at
    BEFORE UPDATE ON public.feature_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resources_updated_at
    BEFORE UPDATE ON public.resources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resource_engagements_updated_at
    BEFORE UPDATE ON public.resource_engagements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fitness_logs_updated_at
    BEFORE UPDATE ON public.fitness_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sync_logs_updated_at
    BEFORE UPDATE ON public.sync_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_exports_updated_at
    BEFORE UPDATE ON public.data_exports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add new columns to users table
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users') THEN
        ALTER TABLE public.users
        ADD COLUMN IF NOT EXISTS energy_curve JSONB DEFAULT '{}'::jsonb,
        ADD COLUMN IF NOT EXISTS default_scheduling_rules JSONB DEFAULT '{}'::jsonb,
        ADD COLUMN IF NOT EXISTS smart_planning_enabled BOOLEAN DEFAULT true,
        ADD COLUMN IF NOT EXISTS encryption_enabled BOOLEAN DEFAULT false,
        ADD COLUMN IF NOT EXISTS encryption_key TEXT,
        ADD COLUMN IF NOT EXISTS gdpr_consent_log JSONB DEFAULT '[]'::jsonb;
    END IF;
END $$;

-- Add JSON validation to prevent invalid JSON
ALTER TABLE public.users
ADD CONSTRAINT valid_energy_curve CHECK (energy_curve IS NULL OR jsonb_typeof(energy_curve) = 'object'),
ADD CONSTRAINT valid_scheduling_rules CHECK (default_scheduling_rules IS NULL OR jsonb_typeof(default_scheduling_rules) = 'object'),
ADD CONSTRAINT valid_gdpr_consent_log CHECK (gdpr_consent_log IS NULL OR jsonb_typeof(gdpr_consent_log) = 'array');

-- Add array validation
ALTER TABLE public.journal_entries
ADD CONSTRAINT valid_tags CHECK (tags IS NULL OR array_length(tags, 1) > 0);

ALTER TABLE public.resources
ADD CONSTRAINT valid_tags CHECK (tags IS NULL OR array_length(tags, 1) > 0); 