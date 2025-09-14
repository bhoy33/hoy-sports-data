#!/usr/bin/env python3
"""
Simple user creation script - no interactive prompts, just creates one user
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
    """Hash password with salt"""
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

def main():
    print("🏈 Simple User Creation")
    print("======================")
    
    # Get credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Missing credentials")
        return
    
    print("Creating Supabase client...")
    client = create_client(url, key)
    
    print("Testing connection...")
    try:
        result = client.table('users').select('count').execute()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Create a test user
    username = "testuser"
    password = "testpass123"
    
    print(f"Creating user '{username}'...")
    
    try:
        # Check if user exists
        result = client.table('users').select('username').eq('username', username).execute()
        if result.data:
            print(f"❌ User '{username}' already exists")
            return
        
        # Create user
        user_data = {
            'username': username,
            'password_hash': hash_password(password),
            'email': None,
            'is_admin': False,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = client.table('users').insert(user_data).execute()
        
        if result.data:
            print(f"✅ User '{username}' created successfully!")
            print(f"   Password: {password}")
            print("   You can now login to the Railway app")
        else:
            print("❌ Failed to create user")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
