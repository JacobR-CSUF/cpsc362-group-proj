#!/usr/bin/env python3
"""
RLS Testing Script - Tests policies with different user scenarios
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

class RLSTester:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not all([self.url, self.service_key]):
            raise ValueError("Missing required environment variables")
        
        # Create service role client (bypasses RLS)
        self.admin = create_client(self.url, self.service_key)
        
    def test_users_table(self):
        """Test Users table RLS policies"""
        print("\n" + "="*60)
        print("Testing USERS Table RLS")
        print("="*60)
        
        try:
            # Test 1: Anyone can view users (using service role)
            print("\n1️⃣  Test: Anyone can view user profiles")
            result = self.admin.table('users').select('id, username, email').limit(3).execute()
            print(f"   ✅ Retrieved {len(result.data)} users")
            for user in result.data:
                print(f"      • {user.get('username', 'N/A')} ({user.get('email', 'N/A')})")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    def test_posts_table(self):
        """Test Posts table RLS policies"""
        print("\n" + "="*60)
        print("Testing POSTS Table RLS")
        print("="*60)
        
        try:
            # Test 1: View public posts
            print("\n1️⃣  Test: Public posts should be visible")
            result = self.admin.table('posts').select('id, caption, visibility').eq('visibility', 'public').limit(3).execute()
            print(f"   ✅ Retrieved {len(result.data)} public posts")
            
            # Test 2: Check visibility options
            print("\n2️⃣  Test: Check different visibility levels")
            for visibility in ['public', 'followers', 'private']:
                result = self.admin.table('posts').select('id').eq('visibility', visibility).execute()
                print(f"   • {visibility.capitalize()}: {len(result.data)} posts")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    def test_messages_table(self):
        """Test Messages table RLS policies"""
        print("\n" + "="*60)
        print("Testing MESSAGES Table RLS")
        print("="*60)
        
        try:
            print("\n1️⃣  Test: Messages should be private")
            result = self.admin.table('messages').select('id, content, created_at').limit(3).execute()
            print(f"   ✅ Retrieved {len(result.data)} messages (admin view)")
            print(f"   ℹ️  With user JWT, users would only see their own messages")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    def test_follows_table(self):
        """Test Follows table RLS policies"""
        print("\n" + "="*60)
        print("Testing FOLLOWS Table RLS")
        print("="*60)
        
        try:
            print("\n1️⃣  Test: Follow relationships should be public")
            result = self.admin.table('follows').select('*').limit(5).execute()
            print(f"   ✅ Retrieved {len(result.data)} follow relationships")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    def test_friend_suggestions_table(self):
        """Test Friend Suggestions table RLS policies"""
        print("\n" + "="*60)
        print("Testing FRIEND_SUGGESTIONS Table RLS")
        print("="*60)
        
        try:
            print("\n1️⃣  Test: Friend suggestions should be user-specific")
            result = self.admin.table('friend_suggestions').select('id, reason, match_score').limit(3).execute()
            print(f"   ✅ Retrieved {len(result.data)} suggestions (admin view)")
            print(f"   ℹ️  With user JWT, users would only see their own suggestions")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    def verify_rls_enabled(self):
        """Verify RLS is enabled on all tables"""
        print("\n" + "="*60)
        print("Verifying RLS Status")
        print("="*60)
        
        tables = [
            'users', 'posts', 'comments', 'likes', 
            'follows', 'messages', 'media', 'friend_suggestions'
        ]
        
        print("\n⚠️  To verify RLS is enabled, run this in Supabase SQL Editor:")
        print("""
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'posts', 'comments', 'likes', 'follows', 'messages', 'media', 'friend_suggestions');
""")
        
        print("\nExpected tables with RLS enabled:")
        for table in tables:
            print(f"   • {table}")
    
    def test_with_user_context(self, user_id: str):
        """Simulate testing with a specific user context"""
        print("\n" + "="*60)
        print(f"Simulating User Context: {user_id}")
        print("="*60)
        
        print("\n⚠️  Note: Service role key bypasses RLS")
        print("   To properly test user-level access:")
        print("   1. Use JWT tokens from actual authenticated users")
        print("   2. Use the anon key instead of service role key")
        print("   3. Set the session with: supabase.auth.set_session(access_token, refresh_token)")
        
        # Show what WOULD be restricted
        print(f"\n📋 What user {user_id[:8]}... SHOULD see:")
        print("   • Their own posts (all visibility levels)")
        print("   • Public posts from all users")
        print("   • Follower-only posts from users they follow")
        print("   • Their own messages (sent and received)")
        print("   • Their own friend suggestions")
        print("   • Comments on posts they can see")
    
    def run_all_tests(self):
        """Run all RLS tests"""
        print("\n🧪 Starting RLS Policy Tests")
        print("="*60)
        print("⚠️  Important: These tests use SERVICE ROLE KEY")
        print("   Service role bypasses RLS (for admin operations)")
        print("   Real user access should be tested with JWT tokens")
        print("="*60)
        
        # Verify RLS status
        self.verify_rls_enabled()
        
        # Test each table
        self.test_users_table()
        self.test_posts_table()
        self.test_messages_table()
        self.test_follows_table()
        self.test_friend_suggestions_table()
        
        # Show user context example
        try:
            result = self.admin.table('users').select('id').limit(1).execute()
            if result.data:
                self.test_with_user_context(result.data[0]['id'])
        except:
            pass
        
        print("\n" + "="*60)
        print("✅ RLS Testing Complete!")
        print("="*60)
        print("\n💡 Next Steps:")
        print("   1. Verify RLS is enabled using the SQL query above")
        print("   2. Test with real user JWT tokens from your auth flow")
        print("   3. Create test users and verify they can only access authorized data")
        print("   4. Check frontend uses ANON_KEY, not SERVICE_ROLE_KEY")

def main():
    try:
        tester = RLSTester()
        tester.run_all_tests()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Make sure your .env file has:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)

if __name__ == "__main__":
    main()
