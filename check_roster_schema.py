#!/usr/bin/env python3
"""
Check the actual Supabase rosters table schema
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from supabase_config import SupabaseManager

def check_roster_schema():
    """Check actual rosters table schema in Supabase"""
    
    print("🔍 Checking Actual Rosters Table Schema")
    print("=" * 40)
    
    supabase_manager = SupabaseManager()
    
    if not supabase_manager.supabase:
        print("❌ Cannot connect to Supabase")
        return
    
    try:
        # Try to get one roster to see the actual column structure
        result = supabase_manager.supabase.table('rosters').select('*').limit(1).execute()
        
        if result.data and len(result.data) > 0:
            roster = result.data[0]
            print("✅ Found roster record. Actual columns:")
            for column, value in roster.items():
                print(f"  • {column}: {type(value).__name__}")
            
            print("\n📋 Sample roster data:")
            for column, value in roster.items():
                if isinstance(value, str) and len(str(value)) > 50:
                    print(f"  {column}: {str(value)[:50]}...")
                else:
                    print(f"  {column}: {value}")
        else:
            print("⚠️  No roster records found to examine schema")
            
        # Try different column name variations to see what works
        print("\n🧪 Testing column name variations:")
        
        test_columns = ['name', 'roster_name', 'title', 'players', 'roster_data', 'data']
        for col in test_columns:
            try:
                test_result = supabase_manager.supabase.table('rosters').select(col).limit(1).execute()
                print(f"  ✅ {col}: EXISTS")
            except Exception as e:
                if 'does not exist' in str(e):
                    print(f"  ❌ {col}: DOES NOT EXIST")
                else:
                    print(f"  ⚠️  {col}: ERROR - {e}")
                    
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

if __name__ == "__main__":
    check_roster_schema()
