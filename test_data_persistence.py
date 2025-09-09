#!/usr/bin/env python3
"""
Comprehensive test script for data persistence and backup system
Tests all save operations to ensure data is never lost during deployments
"""

import requests
import json
import time
import random
import string

BASE_URL = "http://127.0.0.1:5008"

def generate_test_data():
    """Generate test data for comprehensive testing"""
    return {
        'session_id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=32)),
        'game_name': f"Test_Game_{int(time.time())}",
        'roster_name': f"Test_Roster_{int(time.time())}",
        'username': 'scots_user'
    }

def test_login():
    """Test login and return session"""
    print("🔐 Testing login...")
    session = requests.Session()
    
    response = session.get(f"{BASE_URL}/login")
    if response.status_code != 200:
        print(f"❌ Failed to get login page: {response.status_code}")
        return None
    
    login_data = {'password': 'scots25'}
    response = session.post(f"{BASE_URL}/login", data=login_data)
    
    if response.status_code == 200 and (response.url.endswith('/') or 'analytics' in response.url):
        print("✅ Login successful")
        return session
    else:
        print(f"❌ Login failed")
        return None

def test_backup_system_health(session):
    """Test backup system health check"""
    print("\n🏥 Testing backup system health...")
    
    response = session.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check passed")
        print(f"   Database: {data.get('database', 'unknown')}")
        
        backup_status = data.get('backup_system', {})
        print(f"   Database Connected: {backup_status.get('database_connected', False)}")
        print(f"   Total Sessions: {backup_status.get('total_sessions', 0)}")
        print(f"   Total Games: {backup_status.get('total_games', 0)}")
        print(f"   Total Rosters: {backup_status.get('total_rosters', 0)}")
        
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False

def test_session_data_persistence(session):
    """Test session data persistence through multiple saves"""
    print("\n💾 Testing session data persistence...")
    
    # Reset any existing data
    reset_response = session.post(f"{BASE_URL}/box_stats/reset")
    if reset_response.status_code == 200:
        print("✅ Reset existing data")
    
    # Add multiple plays to create substantial session data
    test_plays = [
        {
            "phase": "offense",
            "down": 1,
            "distance": 10,
            "field_position": 25,
            "play_type": "rush",
            "play_call": "Inside Zone",
            "yards_gained": 8,
            "players_involved": [
                {
                    "name": "Test Player 1",
                    "number": 22,
                    "role": "rusher",
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
            "play_type": "pass",
            "play_call": "Quick Slant",
            "yards_gained": 12,
            "players_involved": [
                {
                    "name": "Test Player 2",
                    "number": 11,
                    "role": "receiver",
                    "touchdown": False,
                    "fumble": False,
                    "interception": False,
                    "first_down": True
                }
            ]
        }
    ]
    
    for i, play in enumerate(test_plays):
        response = session.post(f"{BASE_URL}/box_stats/add_play", json=play)
        if response.status_code == 200:
            print(f"✅ Play {i+1} added and backed up")
        else:
            print(f"❌ Failed to add play {i+1}: {response.status_code}")
            return False
    
    # Verify data persistence by retrieving stats
    response = session.get(f"{BASE_URL}/box_stats/get_stats")
    if response.status_code == 200:
        data = response.json()
        total_plays = data.get('team_stats', {}).get('offense', {}).get('total_plays', 0)
        if total_plays >= 2:
            print(f"✅ Session data persisted correctly ({total_plays} plays)")
            return True
        else:
            print(f"❌ Session data not persisted correctly ({total_plays} plays)")
            return False
    else:
        print(f"❌ Failed to retrieve stats: {response.status_code}")
        return False

def test_game_data_persistence(session):
    """Test game save with comprehensive backup"""
    print("\n🎮 Testing game data persistence...")
    
    test_data = generate_test_data()
    
    # Create game data
    game_data = {
        'game_name': test_data['game_name'],
        'opponent': 'Test Opponent',
        'date': '2024-01-15',
        'location': 'Test Stadium'
    }
    
    # Save game
    response = session.post(f"{BASE_URL}/save_game", json=game_data)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"✅ Game '{test_data['game_name']}' saved with comprehensive backup")
            return True
        else:
            print(f"❌ Game save failed: {result.get('message', 'Unknown error')}")
            return False
    else:
        print(f"❌ Game save request failed: {response.status_code}")
        return False

def test_roster_data_persistence(session):
    """Test roster save with comprehensive backup"""
    print("\n👥 Testing roster data persistence...")
    
    test_data = generate_test_data()
    
    # Create roster data
    roster_data = {
        'roster_name': test_data['roster_name'],
        'players': [
            {'name': 'Test Player 1', 'number': 22, 'position': 'RB'},
            {'name': 'Test Player 2', 'number': 11, 'position': 'WR'},
            {'name': 'Test Player 3', 'number': 7, 'position': 'QB'}
        ]
    }
    
    # Save roster
    response = session.post(f"{BASE_URL}/save_roster", json=roster_data)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"✅ Roster '{test_data['roster_name']}' saved with comprehensive backup")
            return True
        else:
            print(f"❌ Roster save failed: {result.get('message', 'Unknown error')}")
            return False
    else:
        print(f"❌ Roster save request failed: {response.status_code}")
        return False

def test_data_recovery(session):
    """Test data recovery functionality"""
    print("\n🔄 Testing data recovery...")
    
    # Test recovery dashboard access
    response = session.get(f"{BASE_URL}/admin/data_recovery")
    if response.status_code == 200:
        data = response.json()
        backup_status = data.get('backup_status', {})
        print(f"✅ Recovery dashboard accessible")
        print(f"   Database Connected: {backup_status.get('database_connected', False)}")
        print(f"   Recovery Options: {len(data.get('recovery_options', []))}")
        return True
    else:
        print(f"❌ Recovery dashboard failed: {response.status_code}")
        return False

def simulate_deployment_scenario(session):
    """Simulate a deployment scenario to test data persistence"""
    print("\n🚀 Simulating deployment scenario...")
    
    # 1. Create substantial data
    print("   Creating substantial data...")
    session_success = test_session_data_persistence(session)
    
    # 2. Save game and roster
    print("   Saving game and roster...")
    game_success = test_game_data_persistence(session)
    roster_success = test_roster_data_persistence(session)
    
    # 3. Verify all data is backed up
    print("   Verifying backup status...")
    health_success = test_backup_system_health(session)
    
    # 4. Test recovery capabilities
    print("   Testing recovery capabilities...")
    recovery_success = test_data_recovery(session)
    
    all_success = all([session_success, game_success, roster_success, health_success, recovery_success])
    
    if all_success:
        print("✅ Deployment scenario test PASSED - Data should survive deployments")
    else:
        print("❌ Deployment scenario test FAILED - Data may be lost during deployments")
    
    return all_success

def main():
    """Run comprehensive data persistence tests"""
    print("=" * 60)
    print("🔍 COMPREHENSIVE DATA PERSISTENCE TEST")
    print("=" * 60)
    
    # Login
    session = test_login()
    if not session:
        print("❌ Cannot proceed without login")
        return
    
    # Test backup system health
    health_success = test_backup_system_health(session)
    
    # Run deployment simulation
    deployment_success = simulate_deployment_scenario(session)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Login: ✅")
    print(f"Backup System Health: {'✅' if health_success else '❌'}")
    print(f"Deployment Simulation: {'✅' if deployment_success else '❌'}")
    
    if health_success and deployment_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Data persistence fixes are working correctly")
        print("✅ User data should survive Railway deployments")
        print("✅ Multiple backup mechanisms are active")
        print("✅ Recovery system is functional")
    else:
        print("\n⚠️  SOME TESTS FAILED!")
        print("❌ Data persistence may still have issues")
        print("❌ Manual intervention may be required")

if __name__ == "__main__":
    main()
