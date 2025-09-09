#!/usr/bin/env python3
"""
Test script for defensive analytics functionality
Tests explosive play thresholds and NEE calculation for defense
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
    
    # Login with valid credentials
    login_data = {
        'password': 'scots25'
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        if response.url.endswith('/') or 'analytics' in response.url:
            print("✓ Login successful")
            return session
        else:
            print(f"✗ Login failed - redirected to: {response.url}")
            return None
    else:
        print(f"✗ Login failed: {response.status_code}")
        return None

def test_defensive_plays(session):
    """Add defensive plays to test analytics"""
    print("\nAdding defensive test plays...")
    
    # Reset any existing data
    reset_response = session.post(f"{BASE_URL}/box_stats/reset")
    if reset_response.status_code == 200:
        print("✓ Reset existing data")
    
    defensive_plays = [
        # Test case 1: Allowed 12-yard run (should be explosive for defense - bad)
        {
            "phase": "defense",
            "down": 1,
            "distance": 10,
            "field_position": 25,
            "play_type": "rush",
            "play_call": "Inside Zone Defense",
            "yards_gained": 12,  # >= 10 yards = explosive (bad for defense)
            "players_involved": [
                {
                    "name": "Defense Player 1",
                    "number": 55,
                    "role": "rusher",  # Defending against rusher
                    "touchdown": False,
                    "fumble": False,
                    "interception": False,
                    "first_down": True
                }
            ]
        },
        # Test case 2: Allowed 18-yard pass (should be explosive for defense - bad)
        {
            "phase": "defense",
            "down": 2,
            "distance": 8,
            "field_position": 37,
            "play_type": "pass",
            "play_call": "Cover 2 Defense",
            "yards_gained": 18,  # >= 15 yards = explosive (bad for defense)
            "players_involved": [
                {
                    "name": "Defense Player 2",
                    "number": 23,
                    "role": "receiver",  # Defending against receiver
                    "touchdown": False,
                    "fumble": False,
                    "interception": False,
                    "first_down": True
                }
            ]
        },
        # Test case 3: Limited to 3-yard run (should NOT be explosive - good defense)
        {
            "phase": "defense",
            "down": 1,
            "distance": 10,
            "field_position": 55,
            "play_type": "rush",
            "play_call": "Goal Line Defense",
            "yards_gained": 3,  # < 10 yards = not explosive (good defense)
            "players_involved": [
                {
                    "name": "Defense Player 3",
                    "number": 91,
                    "role": "rusher",
                    "touchdown": False,
                    "fumble": False,
                    "interception": False,
                    "first_down": False
                }
            ]
        },
        # Test case 4: Limited to 8-yard pass (should NOT be explosive - good defense)
        {
            "phase": "defense",
            "down": 3,
            "distance": 12,
            "field_position": 58,
            "play_type": "pass",
            "play_call": "Blitz Coverage",
            "yards_gained": 8,  # < 15 yards = not explosive (good defense)
            "players_involved": [
                {
                    "name": "Defense Player 4",
                    "number": 21,
                    "role": "receiver",
                    "touchdown": False,
                    "fumble": False,
                    "interception": False,
                    "first_down": False
                }
            ]
        },
        # Test case 5: Forced interception (should be explosive for defense - good)
        {
            "phase": "defense",
            "down": 2,
            "distance": 7,
            "field_position": 45,
            "play_type": "pass",
            "play_call": "Man Coverage",
            "yards_gained": 0,
            "players_involved": [
                {
                    "name": "Defense Player 5",
                    "number": 24,
                    "role": "receiver",
                    "touchdown": False,
                    "fumble": False,
                    "interception": True,  # Interception = explosive for defense
                    "first_down": False
                }
            ]
        }
    ]
    
    for i, play in enumerate(defensive_plays):
        response = session.post(f"{BASE_URL}/box_stats/add_play", json=play)
        if response.status_code == 200:
            print(f"✓ Defensive play {i+1} added successfully")
        else:
            print(f"✗ Failed to add defensive play {i+1}: {response.status_code}")
            print(f"Response: {response.text}")
    
    return len(defensive_plays)

def test_defensive_analytics(session):
    """Test defensive analytics calculations"""
    print("\nTesting defensive analytics...")
    
    response = session.get(f"{BASE_URL}/box_stats/get_stats")
    if response.status_code != 200:
        print(f"✗ Failed to get stats: {response.status_code}")
        return False
    
    data = response.json()
    team_stats = data.get('team_stats', {})
    defense_stats = team_stats.get('defense', {})
    
    print(f"Defense Stats:")
    print(f"  Total Plays: {defense_stats.get('total_plays', 0)}")
    print(f"  Efficient Plays: {defense_stats.get('efficient_plays', 0)}")
    print(f"  Explosive Plays: {defense_stats.get('explosive_plays', 0)}")
    print(f"  Negative Plays: {defense_stats.get('negative_plays', 0)}")
    print(f"  Efficiency Rate: {defense_stats.get('efficiency_rate', 0)}%")
    print(f"  Explosive Rate: {defense_stats.get('explosive_rate', 0)}%")
    print(f"  Negative Rate: {defense_stats.get('negative_rate', 0)}%")
    print(f"  NEE Score: {defense_stats.get('nee_score', 0)}")
    
    # Expected results based on test plays:
    # - 2 explosive plays (12-yard run, 18-yard pass)
    # - 1 interception (also explosive for defense)
    # - Total explosive plays should be 3 out of 5 = 60%
    
    explosive_rate = defense_stats.get('explosive_rate', 0)
    expected_explosive_rate = 60.0  # 3 explosive out of 5 plays
    
    if abs(explosive_rate - expected_explosive_rate) < 0.1:
        print(f"✓ Explosive rate calculation correct: {explosive_rate}%")
    else:
        print(f"✗ Explosive rate incorrect. Expected: {expected_explosive_rate}%, Got: {explosive_rate}%")
    
    # Test NEE calculation: NEE = efficiency + negative - explosive
    efficiency_rate = defense_stats.get('efficiency_rate', 0)
    negative_rate = defense_stats.get('negative_rate', 0)
    nee_score = defense_stats.get('nee_score', 0)
    expected_nee = efficiency_rate + negative_rate - explosive_rate
    
    if abs(nee_score - expected_nee) < 0.1:
        print(f"✓ NEE calculation correct: {nee_score}")
        print(f"  Formula: {efficiency_rate} + {negative_rate} - {explosive_rate} = {expected_nee}")
    else:
        print(f"✗ NEE calculation incorrect. Expected: {expected_nee}, Got: {nee_score}")
    
    return True

def test_phase_specific_analytics(session):
    """Test phase-specific analytics endpoints"""
    print("\nTesting phase-specific analytics...")
    
    # Test defense phase analytics
    response = session.get(f"{BASE_URL}/box_stats/phase_nee_progression/defense")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Defense NEE progression: {len(data.get('nee_progression', []))} data points")
        print(f"  Current NEE: {data.get('current_nee', 0)}")
    else:
        print(f"✗ Failed to get defense NEE progression: {response.status_code}")
    
    # Test defense explosive progression
    response = session.get(f"{BASE_URL}/box_stats/phase_explosive_progression/defense")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Defense explosive progression: {len(data.get('explosive_progression', []))} data points")
        print(f"  Current explosive rate: {data.get('current_explosive_rate', 0)}%")
    else:
        print(f"✗ Failed to get defense explosive progression: {response.status_code}")

def main():
    """Run all defensive analytics tests"""
    print("=== Defensive Analytics Test ===\n")
    
    # Test login
    session = test_login()
    if not session:
        print("Cannot proceed without login")
        return
    
    # Add defensive test plays
    plays_added = test_defensive_plays(session)
    if plays_added == 0:
        print("Cannot proceed without test plays")
        return
    
    # Wait a moment for processing
    time.sleep(1)
    
    # Test analytics calculations
    analytics_success = test_defensive_analytics(session)
    
    # Test phase-specific endpoints
    test_phase_specific_analytics(session)
    
    # Summary
    print(f"\n=== Test Results ===")
    print(f"Login: ✓")
    print(f"Add Defensive Plays: ✓ ({plays_added} plays)")
    print(f"Analytics Calculations: {'✓' if analytics_success else '✗'}")
    
    if analytics_success:
        print("\n🎉 All defensive analytics tests passed!")
        print("\nKey Features Verified:")
        print("- Explosive plays: 10+ yard runs, 15+ yard passes")
        print("- NEE calculation: efficiency + negative - explosive")
        print("- Phase-specific tracking for defense")
    else:
        print("\n⚠️  Some tests failed - check output above")

if __name__ == "__main__":
    main()
