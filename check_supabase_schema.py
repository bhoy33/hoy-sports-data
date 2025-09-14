#!/usr/bin/env python3
"""
Check the actual Supabase table schema to understand what columns exist
"""
import os
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from supabase import create_client

def check_schema():
    """Check the actual schema of Supabase tables"""
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Missing Supabase credentials")
        return
    
    client = create_client(url, key)
    
    print("🔍 Checking Supabase Table Schema")
    print("=" * 35)
    
    # Check rosters table structure
    print("\n📋 ROSTERS TABLE:")
    try:
        result = client.table('rosters').select('*').limit(1).execute()
        if result.data:
            columns = list(result.data[0].keys())
            print(f"   Columns: {', '.join(columns)}")
        else:
            print("   No data to determine columns")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check game_sessions table structure  
    print("\n🎮 GAME_SESSIONS TABLE:")
    try:
        result = client.table('game_sessions').select('*').limit(1).execute()
        if result.data:
            columns = list(result.data[0].keys())
            print(f"   Columns: {', '.join(columns)}")
        else:
            print("   No data to determine columns")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check users table structure
    print("\n👥 USERS TABLE:")
    try:
        result = client.table('users').select('*').limit(1).execute()
        if result.data:
            columns = list(result.data[0].keys())
            print(f"   Columns: {', '.join(columns)}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    check_schema()
