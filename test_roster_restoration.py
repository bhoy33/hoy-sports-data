#!/usr/bin/env python3
"""
Test script to verify roster restoration from Supabase works correctly
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from supabase_config import SupabaseManager

def test_roster_restoration():
    """Test that rosters can be retrieved from Supabase"""
    
    print("🧪 Testing Roster Restoration from Supabase")
    print("=" * 45)
    
    # Initialize Supabase manager
    supabase_manager = SupabaseManager()
    
    # Test getting rosters for a known user
    test_user_id = "1dbb2518-a1b1-469b-81e3-c0a5da26f106"  # mcscots user from check
    
    print(f"Testing roster retrieval for user: {test_user_id}")
    
    # Get rosters
    rosters = supabase_manager.get_user_rosters(test_user_id)
    
    print(f"✅ Retrieved {len(rosters)} rosters from Supabase")
    
    if rosters:
        for i, roster in enumerate(rosters, 1):
            print(f"\nRoster {i}:")
            print(f"  ID: {roster.get('id')}")
            print(f"  Name: {roster.get('roster_name', 'Unnamed')}")
            print(f"  Created: {roster.get('created_at')}")
            
            roster_data = roster.get('roster_data', {})
            players = roster_data.get('players', {})
            print(f"  Players: {len(players)} players")
            
            # Show first few players as sample
            if players:
                sample_players = list(players.items())[:3]
                for player_id, player_data in sample_players:
                    print(f"    - #{player_data.get('number', 'N/A')} {player_data.get('name', 'Unknown')}")
    else:
        print("⚠️  No rosters found for this user")
    
    print("\n" + "=" * 45)
    print("✅ Roster restoration test complete")
    
    return len(rosters) > 0

if __name__ == "__main__":
    test_roster_restoration()
