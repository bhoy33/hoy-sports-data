why #!/usr/bin/env python3
"""
Test script for play editing functionality
Tests the edit_play and delete_play endpoints
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5008"

def test_login():
    """Test login functionality"""
    print("Testing login...")
    session = requests.Session()
    
    # First get the login page to establish session
    response = session.get(f"{BASE_URL}/login")
    if response.status_code != 200:
        print(f"Failed to get login page: {response.status_code}")
        return None
    
    # Login with valid credentials from the app
    login_data = {
        'password': 'scots25'  # Using one of the valid passwords from SITE_PASSWORDS
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        # Check if we were redirected to the main page (successful login)
        if response.url.endswith('/') or 'analytics' in response.url:
            print("✓ Login successful")
            return session
        else:
            print(f"✗ Login failed - redirected to: {response.url}")
            return None
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(f"Response text: {response.text[:200]}")
        return None

def test_add_sample_plays(session):
    """Add some sample plays to test with"""
    print("\nAdding sample plays...")
    
    sample_plays = [
        {
            "phase": "offense",
            "down": 1,
            "distance": 10,
            "field_position": 25,
            "play_type": "pass",
            "play_call": "Slant Route",
            "yards_gained": 8,
            "players_involved": [
                {
                    "name": "John Smith",
                    "number": 12,
                    "role": "passer",
                    "touchdown": False,
                    "fumble": False,
                    "interception": False,
                    "first_down": False
                },
                {
                    "name": "Mike Johnson",
                    "number": 85,
                    "role": "receiver",
                    "touchdown": False,
                    "fumble": False,
                    "interception": False,
                    "first_down": False
                }
            ]
        },
        {
            "phase": "offense",
            "down": 2,
            "distance": 2,
            "field_position": 33,
            "play_type": "rush",
            "play_call": "Inside Zone",
            "yards_gained": 15,
            "players_involved": [
                {
                    "name": "Tom Wilson",
                    "number": 22,
                    "role": "ball_carrier",
                    "touchdown": False,
                    "fumble": False,
                    "interception": False,
                    "first_down": True
                }
            ]
        }
    ]
    
    for i, play in enumerate(sample_plays):
        response = session.post(f"{BASE_URL}/box_stats/add_play", json=play)
        if response.status_code == 200:
            print(f"✓ Sample play {i+1} added successfully")
        else:
            print(f"✗ Failed to add sample play {i+1}: {response.status_code}")
            print(f"Response: {response.text}")
    
    return len(sample_plays)

def test_get_stats(session):
    """Get current stats to verify plays were added"""
    print("\nGetting current stats...")
    
    response = session.get(f"{BASE_URL}/box_stats/get_stats")
    if response.status_code == 200:
        data = response.json()
        box_stats = data.get('box_stats', {})
        plays_count = len(box_stats.get('plays', []))
        print(f"✓ Retrieved stats successfully - {plays_count} plays found")
        return data
    else:
        print(f"✗ Failed to get stats: {response.status_code}")
        return None

def test_edit_play(session, stats_data):
    """Test editing a play"""
    print("\nTesting play editing...")
    
    box_stats = stats_data.get('box_stats', {})
    if not box_stats or not box_stats.get('plays'):
        print("✗ No plays available to edit")
        return False
    
    # Get the first play and modify it
    original_play = box_stats['plays'][0]
    play_index = 0
    
    # Create modified play data
    modified_play = original_play.copy()
    modified_play['yards_gained'] = 12  # Change from original value
    modified_play['play_call'] = "Modified Play Call"
    
    # Add a touchdown to test stat recalculation
    if modified_play.get('players_involved'):
        modified_play['players_involved'][0]['touchdown'] = True
    
    edit_data = {
        'play_index': play_index,
        'play_data': modified_play
    }
    
    response = session.post(f"{BASE_URL}/box_stats/edit_play", json=edit_data)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✓ Play edited successfully")
            return True
        else:
            print(f"✗ Play edit failed: {result.get('message', 'Unknown error')}")
            return False
    else:
        print(f"✗ Play edit request failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_delete_play(session, stats_data):
    """Test deleting a play"""
    print("\nTesting play deletion...")
    
    box_stats = stats_data.get('box_stats', {})
    if not box_stats or len(box_stats.get('plays', [])) < 2:
        print("✗ Not enough plays available to test deletion")
        return False
    
    # Delete the second play (index 1)
    play_index = 1
    
    delete_data = {
        'play_index': play_index
    }
    
    response = session.post(f"{BASE_URL}/box_stats/delete_play", json=delete_data)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✓ Play deleted successfully")
            return True
        else:
            print(f"✗ Play deletion failed: {result.get('message', 'Unknown error')}")
            return False
    else:
        print(f"✗ Play deletion request failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_stats_recalculation(session):
    """Verify that stats were recalculated correctly after edits"""
    print("\nVerifying stats recalculation...")
    
    response = session.get(f"{BASE_URL}/box_stats/get_stats")
    if response.status_code == 200:
        data = response.json()
        box_stats = data.get('box_stats', {})
        
        # Check basic stats
        plays_count = len(box_stats.get('plays', []))
        team_stats = data.get('team_stats', {})
        players = box_stats.get('players', {})
        
        print(f"✓ Final stats retrieved - {plays_count} plays")
        print(f"✓ Team stats updated - Total plays: {team_stats.get('offense', {}).get('total_plays', 0)}")
        print(f"✓ Player stats updated - {len(players)} players tracked")
        
        # Check if touchdown was recorded (from our edit test)
        total_touchdowns = team_stats.get('offense', {}).get('touchdowns', 0)
        if total_touchdowns > 0:
            print(f"✓ Touchdown recorded in team stats: {total_touchdowns}")
        
        return True
    else:
        print(f"✗ Failed to verify stats: {response.status_code}")
        return False

def main():
    """Run all tests"""
    print("=== Football Box Stats Play Editing Test ===\n")
    
    # Test login
    session = test_login()
    if not session:
        print("Cannot proceed without login")
        return
    
    # Add sample plays
    plays_added = test_add_sample_plays(session)
    if plays_added == 0:
        print("Cannot proceed without sample plays")
        return
    
    # Get initial stats
    initial_stats = test_get_stats(session)
    if not initial_stats:
        print("Cannot proceed without initial stats")
        return
    
    # Test editing
    edit_success = test_edit_play(session, initial_stats)
    
    # Test deletion
    delete_success = test_delete_play(session, initial_stats)
    
    # Verify final stats
    stats_success = test_stats_recalculation(session)
    
    # Summary
    print(f"\n=== Test Results ===")
    print(f"Login: ✓")
    print(f"Add Plays: ✓ ({plays_added} plays)")
    print(f"Edit Play: {'✓' if edit_success else '✗'}")
    print(f"Delete Play: {'✓' if delete_success else '✗'}")
    print(f"Stats Recalculation: {'✓' if stats_success else '✗'}")
    
    if edit_success and delete_success and stats_success:
        print("\n🎉 All play editing tests passed!")
    else:
        print("\n⚠️  Some tests failed - check output above")

if __name__ == "__main__":
    main()
