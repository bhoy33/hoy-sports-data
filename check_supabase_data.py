#!/usr/bin/env python3
"""
Script to check Supabase data backup status for games and rosters
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def check_supabase_tables():
    """Check what tables exist in Supabase and their data"""
    
    # Get credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Missing Supabase credentials")
        return
    
    print("🔍 Checking Supabase Data Backup Status")
    print("=" * 45)
    
    try:
        client = create_client(url, key)
        print("✅ Connected to Supabase")
        print()
        
        # Check users table
        print("👥 USERS TABLE:")
        try:
            result = client.table('users').select('*').execute()
            print(f"   Records: {len(result.data)}")
            if result.data:
                for user in result.data:
                    print(f"   - {user['username']} (ID: {user['id']}) Admin: {user.get('is_admin', False)}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Check for game sessions table
        print("🎮 GAME SESSIONS TABLE:")
        try:
            result = client.table('game_sessions').select('*').execute()
            print(f"   Records: {len(result.data)}")
            if result.data:
                for session in result.data[:5]:  # Show first 5
                    print(f"   - {session.get('session_name', 'Unnamed')} (User: {session.get('user_id')})")
            if len(result.data) > 5:
                print(f"   ... and {len(result.data) - 5} more")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Check for rosters table
        print("📋 ROSTERS TABLE:")
        try:
            result = client.table('rosters').select('*').execute()
            print(f"   Records: {len(result.data)}")
            if result.data:
                for roster in result.data[:5]:  # Show first 5
                    print(f"   - {roster.get('roster_name', 'Unnamed')} (User: {roster.get('user_id')})")
            if len(result.data) > 5:
                print(f"   ... and {len(result.data) - 5} more")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Check for players table
        print("🏃 PLAYERS TABLE:")
        try:
            result = client.table('players').select('*').execute()
            print(f"   Records: {len(result.data)}")
            if result.data:
                for player in result.data[:5]:  # Show first 5
                    print(f"   - {player.get('name', 'Unknown')} #{player.get('number', '?')} (User: {player.get('user_id')})")
            if len(result.data) > 5:
                print(f"   ... and {len(result.data) - 5} more")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Check for plays table
        print("⚡ PLAYS TABLE:")
        try:
            result = client.table('plays').select('*').execute()
            print(f"   Records: {len(result.data)}")
            if result.data:
                for play in result.data[:3]:  # Show first 3
                    print(f"   - {play.get('play_type', 'Unknown')} (Session: {play.get('session_id')})")
            if len(result.data) > 3:
                print(f"   ... and {len(result.data) - 3} more")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Check for statistics table
        print("📊 STATISTICS TABLE:")
        try:
            result = client.table('statistics').select('*').execute()
            print(f"   Records: {len(result.data)}")
            if result.data:
                print(f"   - Statistics for {len(set(stat.get('player_id') for stat in result.data))} players")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        print("🔍 DATA BACKUP STATUS:")
        
        # Check if app is actually saving to Supabase
        try:
            users_count = len(client.table('users').select('*').execute().data)
            sessions_count = len(client.table('game_sessions').select('*').execute().data)
            rosters_count = len(client.table('rosters').select('*').execute().data)
            
            if users_count > 0:
                print("✅ Users are being saved to Supabase")
            else:
                print("⚠️  No users found in Supabase")
            
            if sessions_count > 0:
                print("✅ Game sessions are being saved to Supabase")
            else:
                print("⚠️  No game sessions found - create a game to test")
            
            if rosters_count > 0:
                print("✅ Rosters are being saved to Supabase")
            else:
                print("⚠️  No rosters found - upload a roster to test")
                
        except Exception as e:
            print(f"❌ Error checking backup status: {e}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    check_supabase_tables()
