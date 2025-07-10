-- Migration: Add primary_goals array field and migrate existing data
-- Date: 2024-01-XX

-- Add new primary_goals column as JSONB
ALTER TABLE user_profiles 
ADD COLUMN primary_goals JSONB DEFAULT '[]'::jsonb;

-- Migrate existing primary_goal data to primary_goals array
UPDATE user_profiles 
SET primary_goals = CASE 
    WHEN primary_goal IS NOT NULL AND primary_goal != '' 
    THEN json_build_array(primary_goal)
    ELSE '[]'::jsonb
END
WHERE primary_goal IS NOT NULL;

-- Drop the old primary_goal column (optional - keep for backward compatibility)
-- ALTER TABLE user_profiles DROP COLUMN primary_goal;

-- Add index for better query performance
CREATE INDEX idx_user_profiles_primary_goals ON user_profiles USING GIN (primary_goals);

-- Add comment for documentation
COMMENT ON COLUMN user_profiles.primary_goals IS 'Array of primary goals selected during onboarding'; 