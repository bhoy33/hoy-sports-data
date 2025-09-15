#!/usr/bin/env python3
"""
Debug script to examine actual roster data in Supabase
"""
import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

from supabase_config import SupabaseManager

def debug_roster_data():
    """Debug actual roster data structure in Supabase"""
    
    print("🔍 Debugging Actual Roster Data in Supabase")
    print("=" * 50)
    
    # Initialize Supabase manager
    supabase_manager = SupabaseManager()
    
    if not supabase_manager.supabase:
        print("❌ Cannot connect to Supabase - missing credentials")
        return
    
    try:
        # Get all rosters directly from Supabase
        result = supabase_manager.supabase.table('rosters').select('*').execute()
        
        if result.data:
            print(f"📋 Found {len(result.data)} rosters in Supabase:")
            print()
            
            for i, roster in enumerate(result.data, 1):
                print(f"Roster {i}:")
                print(f"  ID: {roster.get('id')}")
                print(f"  User ID: {roster.get('user_id')}")
                print(f"  Roster Name: '{roster.get('roster_name')}'")
                print(f"  Created At: {roster.get('created_at')}")
                
                # Check roster_data structure
                roster_data = roster.get('roster_data', {})
                if isinstance(roster_data, dict):
                    players = roster_data.get('players', {})
                    print(f"  Players Count: {len(players)}")
                    
                    # Show sample player data
                    if players:
                        sample_player = list(players.values())[0]
                        print(f"  Sample Player: {sample_player}")
                else:
                    print(f"  Roster Data Type: {type(roster_data)}")
                    print(f"  Roster Data: {roster_data}")
                
                print("-" * 40)
        else:
            print("📋 No rosters found in Supabase")
            
    except Exception as e:
        print(f"❌ Error querying Supabase: {e}")
    
    print("\n🔍 ANALYSIS:")
    print("• Check if roster_name field is actually being saved")
    print("• Verify roster_data structure matches expected format")
    print("• Look for any null or empty roster_name values")

if __name__ == "__main__":
    debug_roster_data()
