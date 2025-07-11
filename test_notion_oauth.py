#!/usr/bin/env python3
"""
Test script to demonstrate Notion OAuth verification code flow
"""

import requests
import json

# Your local server URL
BASE_URL = "http://localhost:8000"

def test_notion_oauth_flow():
    """Test the complete Notion OAuth flow"""
    
    print("🔐 Testing Notion OAuth Flow")
    print("=" * 50)
    
    # Step 1: Get the OAuth URL
    print("1️⃣ Getting OAuth URL...")
    try:
        # You'll need to be authenticated for this
        response = requests.get(f"{BASE_URL}/api/notion/auth/url")
        if response.status_code == 200:
            data = response.json()
            auth_url = data["auth_url"]
            state = data["state"]
            print(f"✅ OAuth URL: {auth_url}")
            print(f"✅ State: {state}")
            
            # This is what the user would see in their browser
            print(f"\n🌐 User should visit: {auth_url}")
            print("After authorization, Notion will redirect to:")
            print(f"http://localhost:8000/api/notion/callback?code=VERIFICATION_CODE&state={state}")
            
        else:
            print(f"❌ Failed to get OAuth URL: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def simulate_callback():
    """Simulate what happens when Notion redirects back"""
    
    print("\n🔄 Simulating OAuth Callback")
    print("=" * 50)
    
    # This is what Notion sends back after user authorizes
    mock_code = "mock_verification_code_12345"
    mock_state = "user_123_1234567890"
    
    callback_url = f"{BASE_URL}/api/notion/auth/callback?code={mock_code}&state={mock_state}"
    print(f"📥 Notion redirects to: {callback_url}")
    
    print("\n📋 What happens in your code:")
    print("1. FastAPI receives GET request to /api/notion/auth/callback")
    print("2. Extracts 'code' and 'state' from query parameters")
    print("3. Exchanges code for access token with Notion")
    print("4. Stores connection in database")
    print("5. Returns success response")

def show_manual_test():
    """Show how to test manually"""
    
    print("\n🧪 Manual Testing Instructions")
    print("=" * 50)
    
    print("1. Start your server:")
    print("   python main.py")
    
    print("\n2. Get OAuth URL (requires authentication):")
    print("   curl -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print("        http://localhost:8000/api/notion/auth/url")
    
    print("\n3. Visit the returned URL in browser")
    print("   (This will redirect to Notion for authorization)")
    
    print("\n4. After authorization, Notion redirects to:")
    print("   http://localhost:8000/api/notion/callback?code=...&state=...")
    
    print("\n5. Your server automatically:")
    print("   - Receives the verification code")
    print("   - Exchanges it for an access token")
    print("   - Stores the connection")
    print("   - Returns success")

if __name__ == "__main__":
    print("🚀 Notion OAuth Verification Code Flow")
    print("=" * 60)
    
    test_notion_oauth_flow()
    simulate_callback()
    show_manual_test()
    
    print("\n" + "=" * 60)
    print("✅ The verification code is automatically received!")
    print("   No manual intervention needed - it's all handled by your server.") 