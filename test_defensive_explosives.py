#!/usr/bin/env python3
"""
Test script to verify defensive explosive play tracking is working correctly
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import calculate_play_explosiveness

def test_defensive_explosives():
    """Test defensive explosive play calculations"""
    
    print("🧪 Testing Defensive Explosive Play Analytics")
    print("=" * 45)
    
    # Test cases for defensive explosive plays
    test_cases = [
        # (role, yards_gained, phase, expected_result, description)
        ('rusher', 10, 'defense', True, 'Defense allows 10-yard rush (explosive)'),
        ('rusher', 9, 'defense', False, 'Defense allows 9-yard rush (not explosive)'),
        ('rusher', 15, 'defense', True, 'Defense allows 15-yard rush (explosive)'),
        
        ('receiver', 15, 'defense', True, 'Defense allows 15-yard pass (explosive)'),
        ('receiver', 14, 'defense', False, 'Defense allows 14-yard pass (not explosive)'),
        ('receiver', 20, 'defense', True, 'Defense allows 20-yard pass (explosive)'),
        
        ('passer', 15, 'defense', True, 'Defense allows 15-yard pass completion (explosive)'),
        ('passer', 10, 'defense', False, 'Defense allows 10-yard pass completion (not explosive)'),
        
        # Compare with offensive explosive plays
        ('rusher', 10, 'offense', True, 'Offense gains 10-yard rush (explosive)'),
        ('receiver', 15, 'offense', True, 'Offense gains 15-yard pass (explosive)'),
        
        # Edge cases
        ('rusher', 0, 'defense', False, 'Defense allows no gain (not explosive)'),
        ('receiver', -5, 'defense', False, 'Defense forces loss (not explosive)'),
    ]
    
    print("\nTest Results:")
    print("-" * 80)
    
    all_passed = True
    for role, yards, phase, expected, description in test_cases:
        result = calculate_play_explosiveness(role, yards, None, phase)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result != expected:
            all_passed = False
        
        print(f"{status} | {description}")
        print(f"      Role: {role}, Yards: {yards}, Phase: {phase}")
        print(f"      Expected: {expected}, Got: {result}")
        print()
    
    print("=" * 45)
    if all_passed:
        print("✅ All defensive explosive play tests PASSED")
        print("\nDefensive explosive play tracking is working correctly:")
        print("• Rush plays ≥10 yards = explosive against defense")
        print("• Pass plays ≥15 yards = explosive against defense")
    else:
        print("❌ Some tests FAILED - defensive explosive tracking needs fixes")
    
    return all_passed

if __name__ == "__main__":
    test_defensive_explosives()
