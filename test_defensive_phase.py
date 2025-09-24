#!/usr/bin/env python3

import requests
import json

# Test script to verify defensive phase detection and stat calculation

BASE_URL = "http://localhost:5008"

def test_defensive_play_entry():
    """Test adding a defensive play and verify phase detection"""
    
    # First, create a session (login)
    session = requests.Session()
    
    # Login
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        return
    
    print("✓ Login successful")
    
    # Set game info instead of creating new game
    game_info_data = {
        'opponent': 'Test Opponent',
        'date': '2024-01-15',
        'location': 'Test Stadium'
    }
    
    response = session.post(f"{BASE_URL}/box_stats/set_game_info", data=game_info_data)
    if response.status_code != 200:
        print(f"Set game info failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("✓ Game info set")
    
    # Add a defensive explosive play (15+ yard pass allowed)
    defensive_play_data = {
        'down': '1',
        'distance': '10',
        'field_position': 'OWN 25',
        'play_type': 'pass_defense',
        'play_call': 'Cover 2',
        'result': 'Completion allowed for 20 yards',
        'phase': 'defense',  # This should be processed as defensive
        'players': json.dumps([
            {
                'number': '21',
                'role': 'receiver',  # Player who caught the pass (opponent)
                'yards_gained': '20',
                'touchdown': False,
                'fumble': False,
                'interception': False
            },
            {
                'number': '25',
                'role': 'defender',  # Our defensive player
                'yards_gained': '0',
                'touchdown': False,
                'fumble': False,
                'interception': False
            }
        ])
    }
    
    print(f"\n🏈 Adding defensive play with phase='{defensive_play_data['phase']}'")
    print(f"   Play: {defensive_play_data['result']}")
    
    response = session.post(f"{BASE_URL}/box_stats/add_play", data=defensive_play_data)
    if response.status_code != 200:
        print(f"Failed to add defensive play: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("✓ Defensive play added successfully")
    
    # Get box stats to check if defensive stats were calculated
    response = session.get(f"{BASE_URL}/box_stats/get_stats")
    if response.status_code != 200:
        print(f"Failed to get box stats: {response.status_code}")
        print(f"Response text: {response.text}")
        return
    
    try:
        data = response.json()
    except Exception as e:
        print(f"Failed to parse JSON response: {e}")
        print(f"Response text: {response.text}")
        return
    
    # Check team stats
    team_stats = data.get('team_stats', {})
    defense_stats = team_stats.get('defense', {})
    overall_stats = team_stats.get('overall', {})
    
    print(f"\n📊 DEFENSIVE STATS CHECK:")
    print(f"   Defense total plays: {defense_stats.get('total_plays', 0)}")
    print(f"   Defense total yards: {defense_stats.get('total_yards', 0)}")
    print(f"   Defense explosive plays: {defense_stats.get('explosive_plays', 0)}")
    print(f"   Defense efficient plays: {defense_stats.get('efficient_plays', 0)}")
    
    print(f"\n📊 OVERALL STATS CHECK:")
    print(f"   Overall total plays: {overall_stats.get('total_plays', 0)}")
    print(f"   Overall explosive plays: {overall_stats.get('explosive_plays', 0)}")
    
    # Verify the play was recorded correctly
    plays = data.get('plays', [])
    if plays:
        last_play = plays[-1]
        print(f"\n🔍 LAST PLAY VERIFICATION:")
        print(f"   Play phase: {last_play.get('phase', 'NOT SET')}")
        print(f"   Play type: {last_play.get('play_type', 'NOT SET')}")
        print(f"   Yards gained: {last_play.get('yards_gained', 'NOT SET')}")
    
    # Check if defensive stats are non-zero
    if defense_stats.get('total_plays', 0) > 0:
        print("\n✅ SUCCESS: Defensive plays are being recorded!")
        if defense_stats.get('explosive_plays', 0) > 0:
            print("✅ SUCCESS: Defensive explosive plays are being calculated!")
        else:
            print("❌ ISSUE: Defensive explosive plays not calculated (should be 1)")
    else:
        print("\n❌ ISSUE: No defensive plays recorded - phase detection may be failing")
    
    return data

if __name__ == "__main__":
    print("🧪 Testing Defensive Phase Detection and Stats Calculation")
    print("=" * 60)
    
    try:
        result = test_defensive_play_entry()
        if result:
            print("\n" + "=" * 60)
            print("✅ Test completed - check results above")
        else:
            print("\n❌ Test failed")
    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
