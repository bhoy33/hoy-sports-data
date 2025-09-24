#!/usr/bin/env python3
"""
Check what game sessions are saved in Supabase vs local files
"""
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Supabase
from supabase import create_client

def main():
    print("🔍 Checking Saved Game Sessions")
    print("=" * 40)
    
    # Get credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')  # Try anon key first
    if not key:
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Fallback to service role
    
    if not url or not key:
        print("❌ Missing Supabase credentials")
        return
    
    print("Connecting to Supabase...")
    client = create_client(url, key)
    
    try:
        # Check game_sessions table
        print("\n📊 SUPABASE GAME SESSIONS:")
        result = client.table('game_sessions').select('*').execute()
        
        if result.data:
            print(f"   Found {len(result.data)} game sessions in Supabase:")
            for session in result.data:
                print(f"   - ID: {session.get('id')}")
                print(f"     Name: {session.get('session_name')}")
                print(f"     User ID: {session.get('user_id')}")
                print(f"     Created: {session.get('created_at')}")
                print(f"     Status: {session.get('status')}")
                
                # Check if box_stats has data
                box_stats = session.get('box_stats', {})
                plays_count = len(box_stats.get('plays', [])) if isinstance(box_stats, dict) else 0
                players_count = len(box_stats.get('players', {})) if isinstance(box_stats, dict) else 0
                print(f"     Plays: {plays_count}, Players: {players_count}")
                print()
        else:
            print("   No game sessions found in Supabase")
            
    except Exception as e:
        print(f"❌ Error checking Supabase: {e}")
    
    # Check local saved games
    print("\n💾 LOCAL SAVED GAMES:")
    saved_games_dir = "/Users/braydenhoy/CascadeProjects/hoy-sports-data/saved_games"
    
    if os.path.exists(saved_games_dir):
        total_files = 0
        for user_dir in os.listdir(saved_games_dir):
            user_path = os.path.join(saved_games_dir, user_dir)
            if os.path.isdir(user_path):
                print(f"   User directory: {user_dir}")
                files = [f for f in os.listdir(user_path) if f.endswith('.json')]
                total_files += len(files)
                
                for filename in files:
                    filepath = os.path.join(user_path, filename)
                    try:
                        with open(filepath, 'r') as f:
                            game_data = json.load(f)
                        
                        actual_data = game_data.get('game_data', game_data)
                        plays_count = len(actual_data.get('plays', []))
                        players_count = len(actual_data.get('players', {}))
                        
                        print(f"     - {filename}")
                        print(f"       Name: {game_data.get('game_name', 'Unknown')}")
                        print(f"       Saved: {game_data.get('saved_at', 'Unknown')}")
                        print(f"       Plays: {plays_count}, Players: {players_count}")
                        
                    except Exception as e:
                        print(f"     - {filename} (ERROR: {e})")
                
        print(f"\n   Total local game files: {total_files}")
    else:
        print("   No local saved games directory found")
    
    # Check users table for reference
    print("\n👥 USERS IN SUPABASE:")
    try:
        result = client.table('users').select('id, username, created_at').execute()
        if result.data:
            for user in result.data:
                print(f"   - {user.get('username')} (ID: {user.get('id')})")
        else:
            print("   No users found")
    except Exception as e:
        print(f"❌ Error checking users: {e}")

if __name__ == "__main__":
    main()
