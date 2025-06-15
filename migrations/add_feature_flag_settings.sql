-- Add user_type column to users table
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS user_type TEXT DEFAULT 'student' NOT NULL;

-- Create feature_flag_settings table
CREATE TABLE IF NOT EXISTS public.feature_flag_settings (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    feature_name TEXT NOT NULL,
    description TEXT,
    is_globally_enabled BOOLEAN DEFAULT false NOT NULL,
    rollout_percentage INTEGER DEFAULT 0 NOT NULL,
    target_user_types TEXT[] DEFAULT '{}' NOT NULL,
    conditions JSONB DEFAULT '{}'::jsonb NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create index on feature_name
CREATE INDEX IF NOT EXISTS idx_feature_flag_settings_name ON public.feature_flag_settings(feature_name);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_feature_flag_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_feature_flag_settings_updated_at
    BEFORE UPDATE ON public.feature_flag_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_feature_flag_settings_updated_at(); 