#!/usr/bin/env python3
"""
Debug script to test defensive explosive/negative play calculations
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import calculate_play_explosiveness, calculate_play_efficiency

def test_defensive_calculations():
    """Test defensive explosive and negative play calculations"""
    
    print("🔍 Testing Defensive Play Calculations")
    print("=" * 40)
    
    # Test defensive explosive plays
    print("\n📊 DEFENSIVE EXPLOSIVE PLAY TESTS:")
    
    # Rushing explosive (≥10 yards allowed)
    explosive_rush = calculate_play_explosiveness('rusher', 12, None, 'defense')
    print(f"  Rush 12 yards allowed (defense): {explosive_rush} (should be True)")
    
    non_explosive_rush = calculate_play_explosiveness('rusher', 8, None, 'defense')
    print(f"  Rush 8 yards allowed (defense): {non_explosive_rush} (should be False)")
    
    # Passing explosive (≥15 yards allowed)
    explosive_pass = calculate_play_explosiveness('receiver', 18, None, 'defense')
    print(f"  Pass 18 yards allowed (defense): {explosive_pass} (should be True)")
    
    non_explosive_pass = calculate_play_explosiveness('receiver', 12, None, 'defense')
    print(f"  Pass 12 yards allowed (defense): {non_explosive_pass} (should be False)")
    
    # Test defensive efficiency (negative plays)
    print("\n📊 DEFENSIVE EFFICIENCY TESTS:")
    
    # Simulate play data for efficiency calculation
    test_play_data = {
        'down': 1,
        'distance': 10,
        'yards_gained': -2
    }
    
    # Negative play (loss of yards)
    efficient_def = calculate_play_efficiency(test_play_data, -2, None, 'defense')
    print(f"  1st & 10, -2 yards (defense): {efficient_def} (should be True - efficient for defense)")
    
    test_play_data['yards_gained'] = 8
    inefficient_def = calculate_play_efficiency(test_play_data, 8, None, 'defense')
    print(f"  1st & 10, 8 yards (defense): {inefficient_def} (should be False - inefficient for defense)")

def test_backend_data_structure():
    """Test what data structure is returned by get_box_stats"""
    
    print("\n🔍 Testing Backend Data Structure")
    print("=" * 35)
    
    try:
        # Import Flask app components
        from app import app, get_box_stats
        
        with app.app_context():
            # Simulate a request to get_box_stats
            print("Testing get_box_stats endpoint...")
            
            # This would normally be called via HTTP, but we can test the function directly
            # Note: This requires an active session, so may not work in isolation
            print("Note: Full backend test requires active game session")
            
    except Exception as e:
        print(f"Backend test error: {e}")
        print("This is expected if no active session exists")

if __name__ == "__main__":
    test_defensive_calculations()
    test_backend_data_structure()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Check if defensive plays are being entered correctly")
    print("2. Verify team_stats structure includes defense phase")
    print("3. Check browser console for JavaScript errors")
    print("4. Test with actual defensive play entry in live app")
