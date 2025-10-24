"""
Test script to verify XP-29 and XP-33 implementation
Run this after setting up your environment
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
dotenv_path = project_root / ".env" 
load_dotenv(dotenv_path)


async def test_supabase_connection():
    """Test XP-29: Supabase client integration"""
    print("\n=== Testing XP-29: Supabase Client Integration ===\n")
    
    try:
        from apps.api.app.services.supabase_client import SupabaseClient, get_supabase_client
        
        # Test 1: Get client instance
        print("✓ Test 1: Import successful")
        
        # Test 2: Initialize client
        client = get_supabase_client()
        print("✓ Test 2: Client initialized")
        
        # Test 3: Health check
        health = await SupabaseClient.health_check()
        if health["connected"]:
            print(f"✓ Test 3: Health check passed - {health['message']}")
        else:
            print(f"✗ Test 3: Health check failed - {health['error']}")
            return False
        
        # Test 4: Query users table
        try:
            response = client.table("users").select("id, username").limit(3).execute()
            print(f"✓ Test 4: Can query users table - Found {len(response.data)} users")
            if response.data:
                for user in response.data:
                    print(f"  - User ID: {user['id']}, Username: {user['username']}")
        except Exception as e:
            print(f"✗ Test 4: Query failed - {e}")
            return False
        
        # Test 5: Test helper functions
        try:
            # Test query helper
            result = SupabaseClient.query("users", "id, username").limit(1).execute()
            print(f"✓ Test 5: Helper functions work correctly")
        except Exception as e:
            print(f"✗ Test 5: Helper functions failed - {e}")
            return False
        
        print("\n✅ All XP-29 tests passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure you've installed all requirements: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_environment_variables():
    """Test environment configuration"""
    print("\n=== Testing Environment Configuration ===\n")
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "JWT_SECRET"
    ]
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                display_value = value[:20] + "..." if len(value) > 20 else value
            else:
                display_value = value
            print(f"✓ {var}: {display_value}")
        else:
            print(f"✗ {var}: NOT SET")
            all_present = False
    
    if all_present:
        print("\n✅ All environment variables configured!")
    else:
        print("\n⚠️  Missing environment variables. Check your .env file")
    
    return all_present


def test_user_endpoints_structure():
    """Test XP-33: User endpoints structure"""
    print("\n=== Testing XP-33: User CRUD Endpoints Structure ===\n")
    
    try:
        from apps.api.app.routers import users
        from fastapi import FastAPI
        
        print("✓ Test 1: User routes module imported successfully")
        
        # Check router exists
        assert hasattr(users, 'router'), "Router not found"
        print("✓ Test 2: Router defined")
        
        # Check all endpoints exist
        app = FastAPI()
        app.include_router(users.router)
        
        routes = [route.path for route in app.routes]
        expected_routes = [
            "/users/me",
            "/users/{user_id}"
        ]
        
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"✓ Test 3: Endpoint {route} exists")
            else:
                print(f"✗ Test 3: Endpoint {route} missing")
                return False
        
        # Check Pydantic models
        models = [
            'UserPublicProfile',
            'UserPrivateProfile',
            'UserUpdateRequest',
            'UserResponse'
        ]
        
        for model in models:
            if hasattr(users, model):
                print(f"✓ Test 4: Model {model} defined")
            else:
                print(f"⚠️  Model {model} not found (might be correct if not exported)")
        
        print("\n✅ All XP-33 structure tests passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  XP-29 & XP-33 Implementation Test Suite")
    print("="*60)
    
    # Test 1: Environment
    env_ok = test_environment_variables()
    
    if not env_ok:
        print("\n⚠️  Please configure your .env file before continuing")
        return
    
    # Test 2: Supabase connection (XP-29)
    supabase_ok = await test_supabase_connection()
    
    # Test 3: User endpoints structure (XP-33)
    endpoints_ok = test_user_endpoints_structure()
    
    # Summary
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60)
    print(f"Environment Configuration: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"XP-29 (Supabase Client):   {'✅ PASS' if supabase_ok else '❌ FAIL'}")
    print(f"XP-33 (User Endpoints):    {'✅ PASS' if endpoints_ok else '❌ FAIL'}")
    
    if env_ok and supabase_ok and endpoints_ok:
        print("\n🎉 All tests passed! You're ready to go!")
        print("\nNext steps:")
        print("1. Start your FastAPI server: python -m uvicorn apps.api.app.main:app --reload --port 8989")
        print("2. Visit http://localhost:8989/docs for API documentation")
        print("3. Test endpoints using the Swagger UI")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
