#!/usr/bin/env python3
"""
Test script to verify Supabase save methods work correctly
"""
import os
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from supabase_config import supabase_manager

def test_supabase_saves():
    """Test the save methods directly"""
    
    print("🧪 Testing Supabase Save Methods")
    print("=" * 35)
    
    if not supabase_manager or not supabase_manager.is_connected():
        print("❌ Supabase not connected")
        return
    
    print("✅ Supabase connected")
    
    # Test user lookup
    print("\n1. Testing user lookup:")
    test_user = supabase_manager.get_user_by_username('admin')
    if test_user:
        user_id = test_user['id']
        print(f"✅ Found user 'admin' with ID: {user_id}")
    else:
        print("❌ Could not find user 'admin'")
        return
    
    # Test roster save
    print("\n2. Testing roster save:")
    test_roster_data = {
        'players': [
            {'name': 'Test Player 1', 'number': 1, 'position': 'QB'},
            {'name': 'Test Player 2', 'number': 2, 'position': 'RB'}
        ],
        'team_name': 'Test Team',
        'created_at': '2025-01-14'
    }
    
    roster_success = supabase_manager.save_roster(user_id, 'Test Roster', test_roster_data)
    if roster_success:
        print("✅ Roster save successful")
    else:
        print("❌ Roster save failed")
    
    # Test game session save
    print("\n3. Testing game session save:")
    test_game_data = {
        'game_date': '2025-01-14',
        'opponent': 'Test Opponent',
        'location': 'Test Stadium',
        'game_type': 'regular',
        'plays': [
            {'play_number': 1, 'play_type': 'run', 'yards_gained': 5},
            {'play_number': 2, 'play_type': 'pass', 'yards_gained': 12}
        ]
    }
    
    game_success = supabase_manager.save_game_session(user_id, 'Test Game', test_game_data)
    if game_success:
        print("✅ Game session save successful")
    else:
        print("❌ Game session save failed")
    
    # Verify saves
    print("\n4. Verifying saves in database:")
    try:
        # Check rosters
        rosters = supabase_manager.supabase.table('rosters').select('*').eq('user_id', user_id).execute()
        print(f"📋 Rosters for user: {len(rosters.data)}")
        
        # Check game sessions
        sessions = supabase_manager.supabase.table('game_sessions').select('*').eq('user_id', user_id).execute()
        print(f"🎮 Game sessions for user: {len(sessions.data)}")
        
    except Exception as e:
        print(f"❌ Error checking saves: {e}")

if __name__ == "__main__":
    test_supabase_saves()
