#!/usr/bin/env python3
"""
Setup Supabase tables for the Personal Agent application.
"""
from services.supabase import supabase


def create_audit_logs_table() -> None:
    """Create the audit_logs table in Supabase."""
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255),
            action VARCHAR(50) NOT NULL,
            resource VARCHAR(100) NOT NULL,
            resource_id VARCHAR(255),
            ip_address VARCHAR(45),
            user_agent TEXT,
            details JSONB,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
        """

        result = supabase.rpc("exec_sql", {"sql": sql}).execute()  # noqa: F841
        print("✅ audit_logs table created successfully!")
        return True

    except Exception as e:
        print(f"❌ Error creating audit_logs table: {e}")
        # Try alternative approach using direct SQL
        try:
            supabase.table("audit_logs").select("id").limit(1).execute()
            print("✅ Audit logs table exists")
            return True
        except Exception as e2:
            print(f"❌ Table does not exist and cannot be created: {e2}")
            return False


def create_diary_entries_table() -> None:
    """Create the diary_entries table in Supabase."""
    try:
        # SQL to create the diary_entries table
        sql = """
        CREATE TABLE IF NOT EXISTS diary_entries (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            mood VARCHAR(50) NOT NULL,
            tags JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create index on user_id for better performance
        CREATE INDEX IF NOT EXISTS idx_diary_entries_user_id ON diary_entries(user_id);
        
        -- Create index on created_at for sorting
        CREATE INDEX IF NOT EXISTS idx_diary_entries_created_at ON diary_entries(created_at DESC);
        """

        # Execute the SQL using Supabase's RPC (Remote Procedure Call)
        result = supabase.rpc("exec_sql", {"sql": sql}).execute()  # noqa: F841
        print("✅ diary_entries table created successfully!")
        return True

    except Exception as e:
        print(f"❌ Error creating diary_entries table: {e}")
        # Try alternative approach using direct SQL
        try:
            # This might work if RPC is not available
            supabase.table("diary_entries").select("id").limit(1).execute()
            print("✅ Diary entries table exists")
            return True
        except Exception as e2:
            print(f"❌ Table does not exist and cannot be created: {e2}")
            return False


def create_users_table() -> None:
    """Create the users table in Supabase."""
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            name VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """

        result = supabase.rpc("exec_sql", {"sql": sql}).execute()  # noqa: F841
        print("✅ users table created successfully!")
        return True

    except Exception as e:
        print(f"❌ Error creating users table: {e}")
        return False


def setup_row_level_security() -> None:
    """Setup Row Level Security (RLS) for data protection."""
    try:
        sql = """
        -- Enable RLS on diary_entries table
        ALTER TABLE diary_entries ENABLE ROW LEVEL SECURITY;
        
        -- Create policy for users to see only their own diary entries
        CREATE POLICY "Users can view own diary entries" ON diary_entries
            FOR SELECT USING (auth.uid()::text = user_id::text);
            
        CREATE POLICY "Users can insert own diary entries" ON diary_entries
            FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
            
        CREATE POLICY "Users can update own diary entries" ON diary_entries
            FOR UPDATE USING (auth.uid()::text = user_id::text);
            
        CREATE POLICY "Users can delete own diary entries" ON diary_entries
            FOR DELETE USING (auth.uid()::text = user_id::text);
        """

        result = supabase.rpc("exec_sql", {"sql": sql}).execute()  # noqa: F841
        print("✅ Row Level Security enabled!")
        return True

    except Exception as e:
        print(f"⚠️  RLS setup failed (this is optional): {e}")
        return False


def main() -> None:
    """Main setup function."""
    print("🚀 Setting up Supabase tables...")
    print("=" * 40)

    # Create tables
    users_ok = create_users_table()
    diary_ok = create_diary_entries_table()
    audit_ok = create_audit_logs_table()

    # Setup security (optional)
    rls_ok = setup_row_level_security()  # noqa: F841

    if users_ok and diary_ok and audit_ok:
        print("\n🎉 Database setup completed successfully!")
        print("Your Supabase database is ready to use.")
    else:
        print("\n⚠️  Some tables could not be created.")
        print("You may need to create them manually in the Supabase dashboard.")


if __name__ == "__main__":
    main()
