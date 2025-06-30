"""
Supabase client configuration for the application.
"""
import os
from supabase import create_client, Client

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_supabase_client() -> Client:
    """Get the Supabase client instance."""
    return supabase

def test_connection():
    """Test the Supabase connection."""
    try:
        # Try to query a table to test connection
        result = supabase.table("diary_entries").select("id").limit(1).execute()
        print("✅ Supabase connection successful!")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False 