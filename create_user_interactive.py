#!/usr/bin/env python3
"""
Interactive user creation script for Supabase
"""
import os
import hashlib
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Supabase
from supabase import create_client

def hash_password(password):
    """Hash password with salt - matches app authentication"""
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

def create_user(client, username, password, email=None, is_admin=False):
    """Create a new user in Supabase"""
    try:
        # Check if username exists
        result = client.table('users').select('username').eq('username', username).execute()
        if result.data:
            print(f"❌ User '{username}' already exists")
            return False
        
        # Create user
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
    print("🏈 Hoy Sports Data - User Creation Script")
    print("=" * 45)
    
    # Get credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Missing Supabase credentials in .env file")
        print("Make sure .env contains:")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_ANON_KEY=your_anon_key")
        return
    
    print("Connecting to Supabase...")
    try:
        client = create_client(url, key)
        # Test connection
        client.table('users').select('count').execute()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    print("\nReady to create users!")
    
    # Interactive user creation
    while True:
        print("\n" + "-" * 30)
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
        
        continue_input = input("\nCreate another user? (y/n): ").strip().lower()
        if continue_input not in ['y', 'yes', '1']:
            break
    
    print("\n👋 User creation complete!")

if __name__ == "__main__":
    main()
