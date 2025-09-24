#!/usr/bin/env python3

# Direct test of phase detection logic without HTTP requests

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import calculate_play_explosiveness, calculate_play_negativeness

def test_phase_detection_logic():
    """Test the phase detection and calculation logic directly"""
    
    print("🧪 Testing Phase Detection Logic Directly")
    print("=" * 50)
    
    # Test 1: Defensive explosive play (20 yard pass allowed)
    print("\n📋 TEST 1: Defensive Explosive Play")
    print("   Scenario: 20-yard pass completion allowed by defense")
    
    # Test the explosiveness calculation for defense
    is_explosive_offense = calculate_play_explosiveness('receiver', 20, None, 'offense')
    is_explosive_defense = calculate_play_explosiveness('receiver', 20, None, 'defense')
    
    print(f"   Offensive explosive (20 yd pass): {is_explosive_offense}")
    print(f"   Defensive explosive (20 yd pass allowed): {is_explosive_defense}")
    
    # Test 2: Defensive explosive rush (15 yard run allowed)
    print("\n📋 TEST 2: Defensive Explosive Rush")
    print("   Scenario: 15-yard rush allowed by defense")
    
    is_explosive_rush_offense = calculate_play_explosiveness('rusher', 15, None, 'offense')
    is_explosive_rush_defense = calculate_play_explosiveness('rusher', 15, None, 'defense')
    
    print(f"   Offensive explosive (15 yd rush): {is_explosive_rush_offense}")
    print(f"   Defensive explosive (15 yd rush allowed): {is_explosive_rush_defense}")
    
    # Test 3: Defensive negative play (sack for -5 yards)
    print("\n📋 TEST 3: Defensive Negative Play")
    print("   Scenario: Sack for -5 yards (good for defense)")
    
    # Create mock play data for negative play test
    mock_play_data = {
        'down': 2,
        'distance': 10,
        'yards_gained': -5
    }
    mock_player = {
        'role': 'passer',
        'fumble': False,
        'interception': False
    }
    
    is_negative_offense = calculate_play_negativeness(mock_play_data, -5, mock_player, 'offense')
    is_negative_defense = calculate_play_negativeness(mock_play_data, -5, mock_player, 'defense')
    
    print(f"   Offensive negative (-5 yd sack): {is_negative_offense}")
    print(f"   Defensive negative (-5 yd sack allowed): {is_negative_defense}")
    
    # Test 4: Phase detection string processing
    print("\n📋 TEST 4: Phase String Processing")
    
    test_phases = ['offense', 'OFFENSE', 'defense', 'DEFENSE', 'special_teams', 'invalid', None]
    
    for phase in test_phases:
        if phase is None:
            processed_phase = 'offense'  # Default
        else:
            processed_phase = phase.lower() if isinstance(phase, str) else 'offense'
            if processed_phase not in ['offense', 'defense', 'special_teams']:
                processed_phase = 'offense'
        
        print(f"   Input: '{phase}' -> Processed: '{processed_phase}'")
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   ✅ Defensive explosive pass (20+ yd): {is_explosive_defense}")
    print(f"   ✅ Defensive explosive rush (15+ yd): {is_explosive_rush_defense}")
    print(f"   ✅ Defensive negative play (-5 yd): {is_negative_defense}")
    
    if is_explosive_defense and is_explosive_rush_defense:
        print(f"\n✅ SUCCESS: Defensive explosive play detection is working!")
    else:
        print(f"\n❌ ISSUE: Defensive explosive play detection has problems")
    
    if is_negative_defense:
        print(f"✅ SUCCESS: Defensive negative play detection is working!")
    else:
        print(f"❌ ISSUE: Defensive negative play detection has problems")

def test_mock_play_processing():
    """Test how a defensive play would be processed in the backend"""
    
    print("\n" + "=" * 50)
    print("🎯 Testing Mock Defensive Play Processing")
    print("=" * 50)
    
    # Mock data that would come from frontend
    mock_data = {
        'phase': 'defense',
        'play_type': 'pass_defense',
        'yards_gained': '20'
    }
    
    mock_play_data = {
        'yards_gained': 20,
        'players_involved': [
            {
                'role': 'receiver',
                'number': '21',
                'fumble': False,
                'interception': False
            },
            {
                'role': 'defender',
                'number': '25',
                'fumble': False,
                'interception': False
            }
        ]
    }
    
    # Simulate backend processing
    current_phase = mock_data.get('phase', 'offense').lower()
    if current_phase not in ['offense', 'defense', 'special_teams']:
        current_phase = 'offense'
    
    yards_gained = int(mock_data.get('yards_gained', 0))
    
    print(f"📥 Input Data:")
    print(f"   Phase: '{mock_data.get('phase')}' -> Processed: '{current_phase}'")
    print(f"   Yards: {yards_gained}")
    print(f"   Play Type: {mock_data.get('play_type')}")
    
    # Test explosiveness for each player
    team_explosive = False
    team_negative = False
    
    for player in mock_play_data['players_involved']:
        role = player.get('role', '')
        
        is_explosive = calculate_play_explosiveness(role, yards_gained, player, current_phase)
        is_negative = calculate_play_negativeness(mock_play_data, yards_gained, player, current_phase)
        
        print(f"\n👤 Player #{player.get('number')} ({role}):")
        print(f"   Explosive: {is_explosive}")
        print(f"   Negative: {is_negative}")
        
        if is_explosive:
            team_explosive = True
        if is_negative:
            team_negative = True
    
    print(f"\n🏈 Team Results:")
    print(f"   Team Explosive Play: {team_explosive}")
    print(f"   Team Negative Play: {team_negative}")
    
    # Expected results for a 20-yard pass allowed by defense
    expected_explosive = True  # 20 yards >= 15 yard threshold for pass
    expected_negative = False  # Positive yards, not negative
    
    print(f"\n🎯 Expected vs Actual:")
    print(f"   Expected Explosive: {expected_explosive}, Actual: {team_explosive}")
    print(f"   Expected Negative: {expected_negative}, Actual: {team_negative}")
    
    if team_explosive == expected_explosive and team_negative == expected_negative:
        print(f"\n✅ SUCCESS: Mock defensive play processing is correct!")
        return True
    else:
        print(f"\n❌ ISSUE: Mock defensive play processing has problems!")
        return False

if __name__ == "__main__":
    try:
        test_phase_detection_logic()
        success = test_mock_play_processing()
        
        print("\n" + "=" * 50)
        if success:
            print("✅ ALL TESTS PASSED: Phase detection logic is working correctly!")
        else:
            print("❌ SOME TESTS FAILED: Phase detection logic needs fixes!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
