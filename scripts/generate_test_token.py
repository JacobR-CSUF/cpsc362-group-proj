"""
JWT Token Generator for Testing
Generates test JWT tokens for authenticated endpoint testing
"""
import jwt
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
dotenv_path = project_root / ".env" 
load_dotenv(dotenv_path)

from apps.api.app.services.supabase_client import get_supabase_client


def generate_test_token(user_id: str, username: str, email: str, expires_in_hours: int = 24):
    """
    Generate a test JWT token for a user
    
    Args:
        user_id: User's UUID (string format)
        username: User's username
        email: User's email
        expires_in_hours: Token expiration time in hours (default: 24)
    
    Returns:
        str: JWT token
    """
    jwt_secret = os.getenv("JWT_SECRET", "super-secret-jwt-token-with-at-least-32-characters-long")
    
    # Token payload
    payload = {
        "sub": str(user_id),  # Subject (user UUID)
        "username": username,
        "email": email,
        "aud": "authenticated",  # Audience
        "iss": "supabase",  # Issuer
        "iat": datetime.utcnow(),  # Issued at
        "exp": datetime.utcnow() + timedelta(hours=expires_in_hours)  # Expiration
    }
    
    # Generate token
    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    
    return token


def decode_token(token: str):
    """
    Decode and verify a JWT token
    
    Args:
        token: JWT token to decode
        
    Returns:
        dict: Token payload
    """
    jwt_secret = os.getenv("JWT_SECRET", "super-secret-jwt-token-with-at-least-32-characters-long")
    
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"], audience="authenticated")
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError as e:
        return {"error": f"Invalid token: {str(e)}"}


def get_users_from_db():
    """Fetch users from database"""
    try:
        client = get_supabase_client()
        response = client.table("users").select("id, username, email").limit(10).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"⚠️  Could not fetch users from database: {e}")
        return []


def main():
    """Interactive token generator"""
    print("\n" + "="*60)
    print("  JWT Token Generator for Testing (UUID)")
    print("="*60 + "\n")
    
    print("Choose an option:")
    print("1. Generate token for a user (manual entry)")
    print("2. Decode existing token")
    print("3. Generate tokens from database users")
    print("4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        print("\nEnter user details:")
        user_id = input("User UUID (e.g., 550e8400-e29b-41d4-a716-446655440000): ").strip()
        username = input("Username: ").strip()
        email = input("Email: ").strip()
        hours = input("Expires in hours (default 24): ").strip() or "24"
        
        if not user_id or not username or not email:
            print("\n❌ All fields are required!")
            return
        
        try:
            token = generate_test_token(user_id, username, email, int(hours))
            
            print("\n" + "="*60)
            print("  Generated Token")
            print("="*60)
            print(f"\nToken: {token}\n")
            print("Use this token in your API requests:")
            print(f"\ncurl -H 'Authorization: Bearer {token}' \\")
            print("     http://localhost:8001/api/v1/users/me")
            print("\n" + "="*60 + "\n")
            
            # Decode and display
            payload = decode_token(token)
            if "error" not in payload:
                print("Token Payload:")
                for key, value in payload.items():
                    if key in ['iat', 'exp']:
                        dt = datetime.fromtimestamp(value)
                        print(f"  {key}: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    else:
                        print(f"  {key}: {value}")
                print()
            
        except ValueError as e:
            print(f"\n❌ Invalid input: {e}")
    
    elif choice == "2":
        token = input("\nEnter token to decode: ").strip()
        
        if not token:
            print("\n❌ Token is required!")
            return
        
        payload = decode_token(token)
        
        print("\n" + "="*60)
        print("  Decoded Token")
        print("="*60)
        
        if "error" in payload:
            print(f"\n❌ {payload['error']}\n")
        else:
            print("\nPayload:")
            for key, value in payload.items():
                if key in ['iat', 'exp']:
                    dt = datetime.fromtimestamp(value)
                    print(f"  {key}: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                else:
                    print(f"  {key}: {value}")
            print()
    
    elif choice == "3":
        # Fetch users from database
        print("\nFetching users from database...")
        
        users = get_users_from_db()
        
        if not users:
            print("\n❌ No users found in database!")
            print("Run the seed script first: python scripts/seed_database.py")
            return
        
        print(f"\nFound {len(users)} users in database\n")
        print("="*60)
        print("  Database User Tokens")
        print("="*60 + "\n")
        
        for user in users:
            token = generate_test_token(user["id"], user["username"], user["email"])
            print(f"User: {user['username']}")
            print(f"UUID: {user['id']}")
            print(f"Email: {user['email']}")
            print(f"Token: {token}")
            print()
        
        print("="*60)
        print("\nSave these tokens for testing!")
        print("\nExample usage:")
        print("\nexport TOKEN='<token_above>'")
        print("curl -H 'Authorization: Bearer $TOKEN' \\")
        print("     http://localhost:8001/api/v1/users/me\n")
        
        # Save to file option
        save = input("Save tokens to file? (y/n): ").strip().lower()
        if save == 'y':
            filename = project_root / "test_tokens.txt"
            with open(filename, 'w') as f:
                f.write("Test User JWT Tokens\n")
                f.write("="*60 + "\n\n")
                for user in users:
                    token = generate_test_token(user["id"], user["username"], user["email"])
                    f.write(f"User: {user['username']}\n")
                    f.write(f"UUID: {user['id']}\n")
                    f.write(f"Email: {user['email']}\n")
                    f.write(f"Token: {token}\n\n")
            print(f"\n✅ Tokens saved to: {filename}")
    
    elif choice == "4":
        print("\n👋 Goodbye!")
        return
    
    else:
        print("\n❌ Invalid option!")


if __name__ == "__main__":
    main()
