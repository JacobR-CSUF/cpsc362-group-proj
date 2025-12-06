#!/usr/bin/env python3
"""
XP-38 Comments API Test Script
Interactive testing tool for all comment endpoints
"""
import requests
import json
import sys
from typing import Optional
from datetime import datetime
from pathlib import Path

API_BASE_URL = "https://api.geeb.pp.ua"
COMMENTS_BASE = f"{API_BASE_URL}/comments"

class TestSession:
    jwt_token: Optional[str] = None
    post_id: Optional[str] = None
    created_comment_id: Optional[str] = None
    headers: dict = {}
    
    @classmethod
    def set_token(cls, token: str):
        cls.jwt_token = token
        cls.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    @classmethod
    def is_configured(cls) -> bool:
        return cls.jwt_token is not None


def print_banner():
    """Print welcome banner"""
    print("\n" + "="*60)
    print("  XP-38 Comments API Test Suite 💬")
    print("="*60)


def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("="*60 + "\n")


def print_response(response: requests.Response, verbose: bool = False):
    """Pretty print API response"""
    status_emoji = "✅" if 200 <= response.status_code < 300 else "❌"
    print(f"{status_emoji} Status: {response.status_code}")
    
    if verbose:
        try:
            data = response.json()
            print(json.dumps(data, indent=2))
        except:
            print(response.text)


def set_jwt_token():
    """Configure JWT token"""
    print_section("Set JWT Token 🔑")
    
    if TestSession.jwt_token:
        print(f"✓ Current token: {TestSession.jwt_token[:30]}...")
        replace = input("\nReplace? (y/n): ").strip().lower()
        if replace != 'y':
            return
    
    token = input("\nEnter JWT token: ").strip()
    
    if not token:
        print("❌ Token cannot be empty")
        return
    
    TestSession.set_token(token)
    print(f"✅ Token set: {token[:30]}...")


def set_post_id():
    """Configure post ID"""
    print_section("Set Post ID 📝")
    
    if TestSession.post_id:
        print(f"✓ Current post ID: {TestSession.post_id}")
        replace = input("\nReplace? (y/n): ").strip().lower()
        if replace != 'y':
            return
    
    post_id = input("\nEnter post UUID: ").strip()
    
    if not post_id:
        print("❌ Post ID cannot be empty")
        return
    
    TestSession.post_id = post_id
    print(f"✅ Post ID set: {post_id}")


def check_configuration() -> bool:
    """Check if required configuration is set"""
    if not TestSession.jwt_token:
        print("⚠️  JWT token not set. Use option [0] first.")
        return False
    
    if not TestSession.post_id:
        print("⚠️  Post ID not set. Use option [1] first.")
        return False
    
    return True


def test_create_comment(auto_mode: bool = False):
    """Test: Create a new comment"""
    print_section("TEST: Create Comment 💬")
    
    if not check_configuration():
        return False
    
    url = f"{COMMENTS_BASE}/posts/{TestSession.post_id}/comments"
    
    if auto_mode:
        content = f"Test comment created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    else:
        print("Enter comment content (or press Enter for auto-generated):")
        content = input("> ").strip()
        
        if not content:
            content = f"Test comment created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            print(f"Using: {content}")
    
    payload = {"content": content}
    
    print(f"\n📤 POST {url}")
    print(f"📦 Content: {content}\n")
    
    try:
        response = requests.post(url, headers=TestSession.headers, json=payload)
        print_response(response)
        
        if response.status_code == 201:
            data = response.json()
            if data.get("success"):
                TestSession.created_comment_id = data["data"]["id"]
                print(f"\n✅ Comment created!")
                print(f"   ID: {TestSession.created_comment_id}")
                print(f"   Content: {data['data']['content']}")
                print(f"   Author: {data['data']['author']['username']}")
                return True
            else:
                print("\n❌ Failed to create comment")
                return False
        else:
            print("\n❌ Request failed")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', 'Unknown error')}")
            except:
                pass
            return False
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_get_comments(auto_mode: bool = False):
    """Test: Get all comments for a post"""
    print_section("TEST: Get Comments (Paginated) 📋")
    
    if not TestSession.post_id:
        print("⚠️  Post ID not set. Use option [1] first.")
        return False
    
    if auto_mode:
        page, page_size = 1, 50
    else:
        try:
            page = int(input("Page number (default 1): ").strip() or "1")
            page_size = int(input("Page size (default 50): ").strip() or "50")
        except ValueError:
            print("❌ Invalid input, using defaults")
            page, page_size = 1, 50
    
    url = f"{COMMENTS_BASE}/posts/{TestSession.post_id}/comments"
    params = {"page": page, "page_size": page_size}
    
    print(f"\n📤 GET {url}")
    print(f"📦 Params: page={page}, page_size={page_size}\n")
    
    try:
        response = requests.get(url, params=params)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                comments = data.get("data", [])
                print(f"\n✅ Retrieved {len(comments)} comments")
                print(f"   Total: {data.get('total', 0)}")
                print(f"   Page: {data.get('page')}/{data.get('page_size')}")
                print(f"   Has next: {data.get('has_next')}")
                
                if comments:
                    print("\n📝 Comments:")
                    for i, comment in enumerate(comments[:5], 1):
                        print(f"   {i}. @{comment['author']['username']}: {comment['content'][:50]}...")
                    
                    if len(comments) > 5:
                        print(f"   ... and {len(comments) - 5} more")
                return True
            else:
                print("\n❌ Failed to get comments")
                return False
        else:
            print("\n❌ Request failed")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', 'Unknown error')}")
            except:
                pass
            return False
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_update_comment(auto_mode: bool = False):
    """Test: Update own comment"""
    print_section("TEST: Update Comment ✏️")
    
    if not TestSession.jwt_token:
        print("⚠️  JWT token not set. Use option [0] first.")
        return False
    
    if auto_mode:
        if not TestSession.created_comment_id:
            print("⚠️  No comment created yet. Run create test first.")
            return False
        comment_id = TestSession.created_comment_id
    else:
        if TestSession.created_comment_id:
            print(f"✓ Using last created comment: {TestSession.created_comment_id}")
            use_last = input("Use this comment? (y/n, default y): ").strip().lower() or 'y'
            if use_last == 'y':
                comment_id = TestSession.created_comment_id
            else:
                comment_id = input("Enter comment UUID: ").strip()
        else:
            comment_id = input("Enter comment UUID: ").strip()
        
        if not comment_id:
            print("❌ Comment ID cannot be empty")
            return False
    
    if auto_mode:
        content = f"Updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    else:
        print("\nEnter new comment content (or press Enter for auto-generated):")
        content = input("> ").strip()
        
        if not content:
            content = f"Updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            print(f"Using: {content}")
    
    payload = {"content": content}
    url = f"{COMMENTS_BASE}/{comment_id}"
    
    print(f"\n📤 PUT {url}")
    print(f"📦 Content: {content}\n")
    
    try:
        response = requests.put(url, headers=TestSession.headers, json=payload)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"\n✅ Comment updated!")
                print(f"   ID: {data['data']['id']}")
                print(f"   Content: {data['data']['content']}")
                print(f"   Updated: {data['data']['updated_at']}")
                return True
            else:
                print("\n❌ Failed to update comment")
                return False
        else:
            print("\n❌ Request failed")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', 'Unknown error')}")
            except:
                pass
            return False
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_delete_comment(auto_mode: bool = False):
    """Test: Delete own comment (soft delete)"""
    print_section("TEST: Delete Comment (Soft Delete) 🗑️")
    
    if not TestSession.jwt_token:
        print("⚠️  JWT token not set. Use option [0] first.")
        return False
    
    if auto_mode:
        if not TestSession.created_comment_id:
            print("⚠️  No comment created yet. Run create test first.")
            return False
        comment_id = TestSession.created_comment_id
    else:
        if TestSession.created_comment_id:
            print(f"✓ Using last created comment: {TestSession.created_comment_id}")
            use_last = input("Delete this comment? (y/n, default y): ").strip().lower() or 'y'
            if use_last == 'y':
                comment_id = TestSession.created_comment_id
            else:
                comment_id = input("Enter comment UUID: ").strip()
        else:
            comment_id = input("Enter comment UUID: ").strip()
        
        if not comment_id:
            print("❌ Comment ID cannot be empty")
            return False
        
        confirm = input("\n⚠️  Really delete? (yes/no, default yes): ").strip().lower() or 'yes'
        if confirm != 'yes':
            print("❌ Cancelled")
            return False
    
    url = f"{COMMENTS_BASE}/{comment_id}"
    
    print(f"\n📤 DELETE {url}\n")
    
    try:
        response = requests.delete(url, headers=TestSession.headers)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"\n✅ Comment deleted!")
                print(f"   The comment is soft-deleted (deleted_at timestamp set)")
                print(f"   It won't appear in GET requests but remains in database")
                
                if comment_id == TestSession.created_comment_id:
                    TestSession.created_comment_id = None
                return True
            else:
                print("\n❌ Failed to delete comment")
                return False
        else:
            print("\n❌ Request failed")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', 'Unknown error')}")
            except:
                pass
            return False
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_error_cases():
    """Test: Error handling and validation"""
    print_section("TEST: Error Cases & Validation 🧪")
    
    if not check_configuration():
        return False
    
    print("Running error case tests...\n")
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Invalid UUID format
    print("1️⃣  Invalid UUID format...")
    url = f"{COMMENTS_BASE}/posts/invalid-uuid/comments"
    payload = {"content": "Test"}
    response = requests.post(url, headers=TestSession.headers, json=payload)
    
    if response.status_code == 400:
        print("   ✅ Correctly rejected with 400")
        tests_passed += 1
    else:
        print(f"   ❌ Expected 400, got {response.status_code}")
        tests_failed += 1
    
    # Test 2: Empty content
    print("\n2️⃣  Empty content (whitespace only)...")
    url = f"{COMMENTS_BASE}/posts/{TestSession.post_id}/comments"
    payload = {"content": "   "}
    response = requests.post(url, headers=TestSession.headers, json=payload)
    
    if response.status_code == 422:
        print("   ✅ Correctly rejected with 422")
        tests_passed += 1
    else:
        print(f"   ❌ Expected 422, got {response.status_code}")
        tests_failed += 1
    
    # Test 3: Content too long
    print("\n3️⃣  Content over 500 characters...")
    payload = {"content": "a" * 501}
    response = requests.post(url, headers=TestSession.headers, json=payload)
    
    if response.status_code == 422:
        print("   ✅ Correctly rejected with 422")
        tests_passed += 1
    else:
        print(f"   ❌ Expected 422, got {response.status_code}")
        tests_failed += 1
    
    # Test 4: Non-existent comment
    print("\n4️⃣  Update non-existent comment...")
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    url = f"{COMMENTS_BASE}/{fake_uuid}"
    payload = {"content": "Test"}
    response = requests.put(url, headers=TestSession.headers, json=payload)
    
    if response.status_code == 404:
        print("   ✅ Correctly rejected with 404")
        tests_passed += 1
    else:
        print(f"   ❌ Expected 404, got {response.status_code}")
        tests_failed += 1
    
    # Test 5: No authentication
    print("\n5️⃣  Create comment without auth...")
    url = f"{COMMENTS_BASE}/posts/{TestSession.post_id}/comments"
    payload = {"content": "Test"}
    response = requests.post(url, json=payload)  # No headers
    
    if response.status_code == 401 or response.status_code == 403:
        print("   ✅ Correctly rejected with 401/403")
        tests_passed += 1
    else:
        print(f"   ❌ Expected 401/403, got {response.status_code}")
        tests_failed += 1
    
    # Summary
    print(f"\n{'='*40}")
    print(f"Results: {tests_passed} passed, {tests_failed} failed")
    print("="*40)
    
    return tests_failed == 0


def test_all():
    """Run all tests in sequence (auto mode - no prompts)"""
    print_section("Running All Tests 🚀")
    
    if not check_configuration():
        print("\n⚠️  Please configure token and post ID first!")
        input("\n⏸️  Press Enter to return to menu...")
        return
    
    results = []
    
    # Run tests in auto mode
    print("Starting test sequence...\n")
    
    print("▶️  Test 1/5: Create Comment")
    results.append(("Create", test_create_comment(auto_mode=True)))
    
    print("\n▶️  Test 2/5: Get Comments")
    results.append(("Get", test_get_comments(auto_mode=True)))
    
    print("\n▶️  Test 3/5: Update Comment")
    results.append(("Update", test_update_comment(auto_mode=True)))
    
    print("\n▶️  Test 4/5: Error Cases")
    results.append(("Errors", test_error_cases()))
    
    print("\n▶️  Test 5/5: Delete Comment")
    results.append(("Delete", test_delete_comment(auto_mode=True)))
    
    # Summary
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name:.<20} {status}")
    
    print(f"\n  Total: {passed}/{len(results)} passed")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
    
    print("="*60)


def show_status():
    """Show current configuration status"""
    print_section("Current Configuration ⚙️")
    
    print(f"JWT Token:  {'✅ Set' if TestSession.jwt_token else '❌ Not set'}")
    if TestSession.jwt_token:
        print(f"            {TestSession.jwt_token[:40]}...")
    
    print(f"\nPost ID:    {'✅ Set' if TestSession.post_id else '❌ Not set'}")
    if TestSession.post_id:
        print(f"            {TestSession.post_id}")
    
    print(f"\nLast Comment: {'✅ ' + TestSession.created_comment_id if TestSession.created_comment_id else '❌ None created yet'}")
    
    print(f"\nAPI Base:   {COMMENTS_BASE}")


def show_menu():
    """Display main menu"""
    print("\n" + "="*60)
    print("  Options")
    print("="*60)
    print("\n Configuration:")
    print("  [0] Set JWT Token 🔑")
    print("  [1] Set Post ID 📝")
    print("\n Individual Tests:")
    print("  [2] Test Create Comment 💬")
    print("  [3] Test Get Comments 📋")
    print("  [4] Test Update Comment ✏️")
    print("  [5] Test Delete Comment 🗑️")
    print("  [6] Test Error Cases 🧪")
    print("\n Batch:")
    print("  [7] Run All Tests 🚀")
    print("\n Other:")
    print("  [8] Show Status ⚙️")
    print("  [9] Exit 👋")
    
    choice = input("\nSelect option: ").strip()
    return choice


def main():
    """Main entry point"""
    print_banner()
    
    if len(sys.argv) > 1:
        TestSession.set_token(sys.argv[1])
        print(f"✓ Token loaded from argument")
    
    if len(sys.argv) > 2:
        TestSession.post_id = sys.argv[2]
        print(f"✓ Post ID loaded from argument")
    
    while True:
        choice = show_menu()
        
        if choice == "0":
            set_jwt_token()
        elif choice == "1":
            set_post_id()
        elif choice == "2":
            test_create_comment()
        elif choice == "3":
            test_get_comments()
        elif choice == "4":
            test_update_comment()
        elif choice == "5":
            test_delete_comment()
        elif choice == "6":
            test_error_cases()
        elif choice == "7":
            test_all()
        elif choice == "8":
            show_status()
        elif choice == "9":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid option")
        
        input("\n⏸️  Press Enter to continue...")


if __name__ == "__main__":
    main()
