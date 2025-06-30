"""
Supabase client configuration for the application.
"""
import os
from supabase import create_client, Client
from config.security import security_config

# Get Supabase credentials from security config
SUPABASE_URL = security_config.SUPABASE_URL
SUPABASE_ANON_KEY = security_config.SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY = security_config.SUPABASE_SERVICE_ROLE_KEY

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set")

# Create Supabase client
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_supabase_client() -> Client:
    """Get the Supabase client instance."""
    return supabase_client

def get_supabase_service_client() -> Client:
    """Get the Supabase service role client for admin operations."""
    if not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable must be set for admin operations")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def test_connection():
    """Test the Supabase connection."""
    try:
        # Try to query a table to test connection
        result = supabase_client.table("users").select("id").limit(1).execute()
        print("✅ Supabase connection successful!")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False 