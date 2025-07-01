# Cognie Platform Schema Migration Guide

## Prerequisites

1. Ensure you have the required Supabase extensions:
   ```sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "pgcrypto";
   ```

2. Backup your existing database:
   ```bash
   # pg_dump -U your_user -d your_database > backup_before_migration.sql  # Use Supabase dashboard for backups
   ```

## Migration Steps

### 1. Create New Enum Types
```sql
-- Run these first as they're dependencies for other tables
CREATE TYPE energy_level AS ENUM ('low', 'medium', 'high');
CREATE TYPE mood_type AS ENUM ('very_happy', 'happy', 'neutral', 'sad', 'very_sad');
CREATE TYPE sync_direction AS ENUM ('push', 'pull', 'both');
CREATE TYPE sync_status AS ENUM ('pending', 'success', 'failed', 'conflict');
CREATE TYPE feature_mode AS ENUM ('focus', 'relax', 'study', 'work', 'custom');
CREATE TYPE resource_type AS ENUM ('article', 'video', 'book', 'course', 'tool');
CREATE TYPE resource_trust_level AS ENUM ('verified', 'peer_reviewed', 'community', 'unverified');
CREATE TYPE data_export_format AS ENUM ('csv', 'json', 'pdf');
```

### 2. Modify Existing Tables

#### Users Table
```sql
ALTER TABLE public.users
ADD COLUMN energy_curve JSONB DEFAULT '{}'::jsonb,
ADD COLUMN default_scheduling_rules JSONB DEFAULT '{}'::jsonb,
ADD COLUMN smart_planning_enabled BOOLEAN DEFAULT true,
ADD COLUMN encryption_enabled BOOLEAN DEFAULT false,
ADD COLUMN encryption_key TEXT,
ADD COLUMN gdpr_consent_log JSONB DEFAULT '[]'::jsonb;
```

### 3. Create New Tables

#### Journal System
```sql
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
```

#### Habits System
```sql
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
```

### 4. Enable Row Level Security

```sql
-- Enable RLS on all new tables
ALTER TABLE public.journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.journal_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.habits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.habit_logs ENABLE ROW LEVEL SECURITY;
-- ... (repeat for all new tables)
```

### 5. Create RLS Policies

```sql
-- Example for journal_entries (repeat for all tables)
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
```

### 6. Create Indexes

```sql
-- Create indexes for new tables
CREATE INDEX idx_journal_entries_user_id ON public.journal_entries(user_id);
CREATE INDEX idx_journal_entries_tags ON public.journal_entries USING GIN(tags);
CREATE INDEX idx_habits_user_id ON public.habits(user_id);
CREATE INDEX idx_habit_logs_habit_id ON public.habit_logs(habit_id);
-- ... (repeat for all new tables)
```

### 7. Create Triggers

```sql
-- Create triggers for new tables
CREATE TRIGGER update_journal_entries_updated_at
    BEFORE UPDATE ON public.journal_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_habits_updated_at
    BEFORE UPDATE ON public.habits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
-- ... (repeat for all new tables)
```

## Verification Steps

1. Check table creation:
   ```sql
   \dt public.*
   ```

2. Verify RLS policies:
   ```sql
   SELECT * FROM pg_policies WHERE schemaname = 'public';
   ```

3. Test indexes:
   ```sql
   SELECT schemaname, tablename, indexname, indexdef
   FROM pg_indexes
   WHERE schemaname = 'public';
   ```

4. Verify triggers:
   ```sql
   SELECT * FROM pg_trigger
   WHERE tgrelid IN (
       SELECT oid FROM pg_class
       WHERE relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
   );
   ```

## Rollback Plan

If issues occur during migration:

1. Stop all application traffic
2. Restore from backup:
   ```bash
   psql -U your_user -d your_database < backup_before_migration.sql
   ```
3. Verify data integrity
4. Resume application traffic

## Post-Migration Tasks

1. Update application code to use new schema
2. Test all new features
3. Monitor performance
4. Update documentation
5. Train team on new features

## Performance Considerations

1. Monitor query performance
2. Check index usage
3. Review RLS policy impact
4. Optimize JSON field queries
5. Set up appropriate vacuum policies

## Security Checklist

1. Verify RLS policies
2. Test encryption features
3. Review GDPR compliance
4. Check backup procedures
5. Validate user permissions

## Monitoring Setup

1. Set up performance monitoring
2. Configure error tracking
3. Implement usage analytics
4. Monitor sync operations
5. Track resource usage 