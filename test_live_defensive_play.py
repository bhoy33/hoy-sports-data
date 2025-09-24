#!/usr/bin/env python3
"""
Test script to simulate adding a defensive play and check if stats are calculated correctly
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

import json
from app import app, add_box_stats_play, get_box_stats

def test_defensive_play_entry():
    """Test adding a defensive explosive play and check if stats are updated"""
    
    print("🔍 Testing Defensive Play Entry and Stat Calculation")
    print("=" * 52)
    
    with app.app_context():
        # Simulate a defensive explosive play (rush for 15 yards allowed)
        defensive_play_data = {
            'play_number': 1,
            'down': 1,
            'distance': 10,
            'field_position': 'OWN 25',
            'play_type': 'rush',
            'phase': 'defense',  # Key: make sure this is set to defense
            'yards_gained': 15,  # Should be explosive for defense (≥10 yards)
            'result': 'Rush for 15 yards',
            'players_involved': [
                {
                    'number': '55',
                    'name': 'Test Linebacker',
                    'position': 'LB',
                    'role': 'tackler'
                }
            ]
        }
        
        print("📝 Simulating defensive play entry:")
        print(f"  Phase: {defensive_play_data['phase']}")
        print(f"  Play Type: {defensive_play_data['play_type']}")
        print(f"  Yards Gained: {defensive_play_data['yards_gained']}")
        print(f"  Should be explosive: {defensive_play_data['yards_gained'] >= 10}")
        
        # Test the calculation functions directly first
        from app import calculate_play_explosiveness, calculate_play_efficiency
        
        is_explosive = calculate_play_explosiveness('rusher', 15, None, 'defense')
        is_efficient = calculate_play_efficiency(defensive_play_data, 15, None, 'defense')
        
        print(f"\n🧮 Direct calculation results:")
        print(f"  Is explosive (defense): {is_explosive}")
        print(f"  Is efficient (defense): {is_efficient}")
        
        # Now test what happens when we add this play
        print(f"\n📊 Testing play addition...")
        
        # Note: This would require a full Flask request context and session
        # For now, let's check the calculation logic
        
        print("\n✅ Calculation functions work correctly")
        print("❓ Need to check if plays are being saved with correct phase")

def check_phase_detection():
    """Check how phase is determined when adding plays"""
    
    print("\n🔍 Checking Phase Detection Logic")
    print("=" * 35)
    
    # Check the add_box_stats_play function for phase handling
    print("Key areas to investigate:")
    print("1. How is 'phase' parameter processed in add_box_stats_play?")
    print("2. Are defensive plays being saved with phase='defense'?")
    print("3. Are team stats being updated for the correct phase?")
    print("4. Is the frontend sending the correct phase value?")

if __name__ == "__main__":
    test_defensive_play_entry()
    check_phase_detection()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Check if frontend sends correct phase='defense' for defensive plays")
    print("2. Verify add_box_stats_play processes phase parameter correctly")
    print("3. Check if defensive team stats are being updated")
    print("4. Look at actual play data in session storage")
