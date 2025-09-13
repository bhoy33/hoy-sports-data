#!/usr/bin/env python3
"""
Script to create new users in Supabase for the Football Analytics app
"""
import os
import sys
import bcrypt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Supabase manager
try:
    from supabase_config import supabase_manager
    print("✅ Supabase manager loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import Supabase manager: {e}")
    sys.exit(1)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_new_user(username: str, password: str, email: str = None, is_admin: bool = False):
    """Create a new user in Supabase"""
    print(f"\n🔄 Creating user: {username}")
    
    # Check if Supabase is connected
    if not supabase_manager.is_connected():
        print("❌ Supabase is not connected. Check environment variables:")
        print(f"   SUPABASE_URL: {'set' if os.getenv('SUPABASE_URL') else 'missing'}")
        print(f"   SUPABASE_ANON_KEY: {'set' if os.getenv('SUPABASE_ANON_KEY') else 'missing'}")
        return False
    
    # Test connection
    if not supabase_manager.test_connection():
        print("❌ Supabase connection test failed")
        return False
    
    # Check if user already exists
    existing_user = supabase_manager.get_user_by_username(username)
    if existing_user:
        print(f"❌ User '{username}' already exists")
        return False
    
    # Hash the password
    password_hash = hash_password(password)
    
    # Create the user
    user_data = supabase_manager.create_user(
        username=username,
        password_hash=password_hash,
        email=email,
        is_admin=is_admin
    )
    
    if user_data:
        print(f"✅ User '{username}' created successfully!")
        print(f"   User ID: {user_data.get('id')}")
        print(f"   Admin: {user_data.get('is_admin', False)}")
        return True
    else:
        print(f"❌ Failed to create user '{username}'")
        return False

def main():
    """Main function to create users"""
    print("🏈 Football Analytics - User Creation Script")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_ANON_KEY'):
        print("❌ Missing required environment variables:")
        print("   SUPABASE_URL")
        print("   SUPABASE_ANON_KEY")
        print("\nPlease set these in your .env file or environment")
        sys.exit(1)
    
    # Interactive user creation
    while True:
        print("\n" + "=" * 30)
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
        
        # Create the user
        success = create_new_user(username, password, email, is_admin)
        
        if success:
            print(f"\n🎉 User '{username}' is ready to use the Football Analytics app!")
        
        continue_input = input("\nCreate another user? (y/n): ").strip().lower()
        if continue_input not in ['y', 'yes', '1']:
            break
    
    print("\n👋 User creation complete!")

if __name__ == "__main__":
    main()
