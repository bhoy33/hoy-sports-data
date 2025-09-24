#!/usr/bin/env python3
"""
Test script to verify Supabase game session saving functionality
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project directory to Python path
sys.path.append('/Users/braydenhoy/CascadeProjects/hoy-sports-data')

from supabase_config import supabase_manager

def test_save_game_session():
    print("🧪 Testing Supabase Game Session Save")
    print("=" * 40)
    
    if not supabase_manager or not supabase_manager.is_connected():
        print("❌ Supabase not connected")
        return
    
    # Test with a known user
    test_username = "testuser"
    user = supabase_manager.get_user_by_username(test_username)
    
    if not user:
        print(f"❌ User '{test_username}' not found")
        return
    
    user_id = user['id']
    print(f"✓ Found user: {test_username} (ID: {user_id})")
    
    # Create test game data
    test_game_data = {
        'plays': [
            {
                'play_number': 1,
                'quarter': 1,
                'down': 1,
                'distance': 10,
                'yards_gained': 5,
                'play_type': 'rush'
            }
        ],
        'players': {
            'John_Doe_1': {
                'name': 'John Doe',
                'number': 1,
                'position': 'RB',
                'rushing_yards': 5,
                'total_plays': 1
            }
        },
        'team_stats': {
            'offense': {
                'total_plays': 1,
                'total_yards': 5,
                'explosive_plays': 0,
                'negative_plays': 0
            }
        },
        'game_info': {
            'name': 'Test Game',
            'opponent': 'Test Opponent',
            'date': datetime.now().date().isoformat()
        }
    }
    
    # Test saving with corrected function signature
    game_name = f"Test_Game_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\n🎮 Attempting to save game: {game_name}")
    
    success = supabase_manager.save_game_session(user_id, game_name, test_game_data)
    
    if success:
        print(f"✅ Game '{game_name}' saved successfully!")
        
        # Verify by retrieving
        print("\n🔍 Verifying saved game...")
        sessions = supabase_manager.get_user_game_sessions(user_id)
        
        found_game = None
        for session in sessions:
            if session.get('session_name') == game_name:
                found_game = session
                break
        
        if found_game:
            print(f"✅ Game found in Supabase!")
            print(f"   Session ID: {found_game.get('id')}")
            print(f"   Name: {found_game.get('session_name')}")
            print(f"   Created: {found_game.get('created_at')}")
            
            box_stats = found_game.get('box_stats', {})
            print(f"   Plays: {len(box_stats.get('plays', []))}")
            print(f"   Players: {len(box_stats.get('players', {}))}")
        else:
            print(f"❌ Game not found after saving")
    else:
        print(f"❌ Failed to save game")

if __name__ == "__main__":
    test_save_game_session()
