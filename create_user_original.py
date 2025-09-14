#!/usr/bin/env python3
"""
Original user creation script based on the working app_minimal.py implementation
This is the script that was successfully used two days ago to create users in Supabase
"""
import os
import hashlib
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import Supabase with error handling
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Supabase not available: {e}")
    SUPABASE_AVAILABLE = False
    exit(1)

def hash_password(password):
    """Hash password with salt - same method as app_minimal.py"""
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

def check_password(hashed_password, user_password):
    """Check if password matches hash - same method as app_minimal.py"""
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()

def create_supabase_client():
    """Initialize Supabase client"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials:")
        print("   SUPABASE_URL:", "set" if supabase_url else "missing")
        print("   SUPABASE_ANON_KEY:", "set" if supabase_key else "missing")
        print("\nPlease set these environment variables or create a .env file")
        return None
    
    try:
        client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client initialized successfully")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        return None

def test_supabase_connection(client):
    """Test Supabase connection"""
    try:
        # Simple test query
        result = client.table('users').select('count').execute()
        print("✅ Supabase connection test successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection test failed: {e}")
        return False

def create_user(client, username, password, email=None, is_admin=False):
    """Create a new user in Supabase using the original method"""
    try:
        # Check if username exists
        result = client.table('users').select('username').eq('username', username).execute()
        
        if result.data and len(result.data) > 0:
            print(f"❌ Username '{username}' already exists")
            return False
        
        # Create new user with original hash method
        user_data = {
            'username': username,
            'password_hash': hash_password(password),
            'email': email,
            'is_admin': is_admin,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = client.table('users').insert(user_data).execute()
        
        if result.data:
            user = result.data[0]
            print(f"✅ User '{username}' created successfully!")
            print(f"   User ID: {user['id']}")
            print(f"   Admin: {user.get('is_admin', False)}")
            return True
        else:
            print(f"❌ Failed to create user '{username}'")
            return False
            
    except Exception as e:
        print(f"❌ Error creating user '{username}': {e}")
        return False

def main():
    """Main function - interactive user creation"""
    print("🏈 Hoy Sports Data - Original User Creation Script")
    print("=" * 55)
    print("This is the same script that worked two days ago")
    print()
    
    # Initialize Supabase client
    client = create_supabase_client()
    if not client:
        exit(1)
    
    # Test connection
    if not test_supabase_connection(client):
        exit(1)
    
    print()
    print("Ready to create users!")
    print()
    
    # Interactive user creation loop
    while True:
        print("-" * 40)
        username = input("Enter username (or 'quit' to exit): ").strip()
        
        if username.lower() == 'quit':
            break
        
        if not username:
            print("❌ Username cannot be empty")
            continue
        
        password = input("Enter password: ").strip()
        if not password:
            print("❌ Password cannot be empty")
            continue
        
        email = input("Enter email (optional): ").strip()
        if not email:
            email = None
        
        is_admin_input = input("Is admin user? (y/n): ").strip().lower()
        is_admin = is_admin_input in ['y', 'yes', '1', 'true']
        
        print(f"\nCreating user '{username}'...")
        success = create_user(client, username, password, email, is_admin)
        
        if success:
            print(f"🎉 User '{username}' can now login to the Railway app!")
        
        print()
        continue_input = input("Create another user? (y/n): ").strip().lower()
        if continue_input not in ['y', 'yes', '1']:
            break
    
    print("\n👋 User creation complete!")
    print("Users can now login to your Railway app with their username/password")

if __name__ == "__main__":
    main()
