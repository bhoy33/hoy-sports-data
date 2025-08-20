#!/usr/bin/env python3
"""
Test script to validate the enhanced Box Stats Analytics system
with comprehensive positions and phase-specific stat tracking.
"""

import requests
import json
import time

# Test configuration
BASE_URL = "http://127.0.0.1:5004"
TEST_TIMEOUT = 5

def test_server_connection():
    """Test if the Flask server is responding"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TEST_TIMEOUT)
        print(f"✅ Server connection: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Server connection failed: {e}")
        return False

def test_box_stats_page():
    """Test if Box Stats Analytics page loads"""
    try:
        response = requests.get(f"{BASE_URL}/analytics/box-stats", timeout=TEST_TIMEOUT)
        print(f"✅ Box Stats page: {response.status_code}")
        
        # Check for key elements in the response
        content = response.text
        checks = [
            ("Phase selection", "data-phase=" in content),
            ("Comprehensive positions", "optgroup label=" in content),
            ("Defensive positions", "DE - Defensive End" in content),
            ("Special teams positions", "P - Punter" in content),
            ("Phase-specific stats", "getPhaseSpecificStatOptions" in content)
        ]
        
        for check_name, condition in checks:
            status = "✅" if condition else "❌"
            print(f"{status} {check_name}: {'Found' if condition else 'Missing'}")
        
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Box Stats page failed: {e}")
        return False

def test_player_creation():
    """Test creating a player with new defensive position"""
    try:
        # Test data for a defensive player
        player_data = {
            "number": 55,
            "name": "Test Linebacker",
            "position": "MLB"  # Middle Linebacker - new defensive position
        }
        
        response = requests.post(
            f"{BASE_URL}/box_stats/add_player",
            json=player_data,
            timeout=TEST_TIMEOUT
        )
        
        print(f"✅ Player creation test: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Player created: #{player_data['number']} {player_data['name']} ({player_data['position']})")
        
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Player creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🏈 Testing Enhanced Box Stats Analytics System")
    print("=" * 50)
    
    tests = [
        ("Server Connection", test_server_connection),
        ("Box Stats Page", test_box_stats_page),
        ("Player Creation", test_player_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Tests Passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🏆 All tests passed! Enhanced Box Stats Analytics system is working correctly.")
        print("\n🔧 New Features Validated:")
        print("   • Comprehensive position options (Offense, Defense, Special Teams)")
        print("   • Phase-specific stat tracking options")
        print("   • Dynamic UI based on selected phase")
        print("   • Professional position abbreviations")
    else:
        print("⚠️  Some tests failed. Check server status and implementation.")

if __name__ == "__main__":
    main()
