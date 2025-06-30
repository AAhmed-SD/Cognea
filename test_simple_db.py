#!/usr/bin/env python3
"""
Simple test to verify basic database connectivity.
"""
import os
from dotenv import load_dotenv
from services.supabase import get_supabase_client

# Load environment variables
load_dotenv()

def test_basic_connectivity():
    """Test basic Supabase connectivity."""
    print("🧪 Testing Basic Database Connectivity")
    print("=" * 40)
    
    try:
        supabase = get_supabase_client()
        
        # Test 1: Check if we can connect
        print("\n1. Testing connection...")
        result = supabase.table("tasks").select("id").limit(1).execute()
        print("✅ Successfully connected to Supabase")
        print(f"   Found {len(result.data)} existing tasks")
        
        # Test 2: Check if we can read from goals table
        print("\n2. Testing goals table access...")
        result = supabase.table("goals").select("id").limit(1).execute()
        print("✅ Successfully accessed goals table")
        print(f"   Found {len(result.data)} existing goals")
        
        # Test 3: Check environment variables
        print("\n3. Checking environment variables...")
        print(f"   SUPABASE_URL: {'✅ Set' if os.getenv('SUPABASE_URL') else '❌ Missing'}")
        print(f"   SUPABASE_ANON_KEY: {'✅ Set' if os.getenv('SUPABASE_ANON_KEY') else '❌ Missing'}")
        print(f"   SUPABASE_SERVICE_KEY: {'✅ Set' if os.getenv('SUPABASE_SERVICE_KEY') else '❌ Missing (needed for admin operations)'}")
        
        print("\n🎉 Basic connectivity test passed!")
        print("\n📝 Note: To test full CRUD operations, you need to:")
        print("   1. Add SUPABASE_SERVICE_KEY to your .env file")
        print("   2. Or test with authenticated user requests")
        
        return True
        
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_connectivity()
    exit(0 if success else 1) 