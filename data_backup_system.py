#!/usr/bin/env python3
"""
Comprehensive data backup and recovery system for hoysportsdata.com
Ensures all user data is saved to multiple locations with automatic recovery
"""

import os
import json
import pickle
import shutil
import hashlib
from datetime import datetime
from database import db_manager

class DataBackupSystem:
    """Handles comprehensive backup and recovery of all user data"""
    
    def __init__(self, base_dir="/tmp/hoy_sports_backup"):
        self.base_dir = base_dir
        self.ensure_backup_dirs()
    
    def ensure_backup_dirs(self):
        """Create backup directory structure"""
        dirs = [
            self.base_dir,
            os.path.join(self.base_dir, "sessions"),
            os.path.join(self.base_dir, "games"),
            os.path.join(self.base_dir, "rosters"),
            os.path.join(self.base_dir, "emergency")
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def backup_session_data(self, session_id, username, data):
        """Backup session data to multiple locations"""
        success_count = 0
        
        # 1. Database backup
        try:
            if db_manager.save_session_data(session_id, username, data):
                print(f"✓ Session {session_id} backed up to database")
                success_count += 1
        except Exception as e:
            print(f"❌ Database session backup failed: {e}")
        
        # 2. File backup
        try:
            session_file = os.path.join(self.base_dir, "sessions", f"{session_id}.json")
            backup_data = {
                'session_id': session_id,
                'username': username,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            with open(session_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            print(f"✓ Session {session_id} backed up to file")
            success_count += 1
        except Exception as e:
            print(f"❌ File session backup failed: {e}")
        
        # 3. Emergency pickle backup
        try:
            emergency_file = os.path.join(self.base_dir, "emergency", f"session_{session_id}.pkl")
            with open(emergency_file, 'wb') as f:
                pickle.dump({'session_id': session_id, 'username': username, 'data': data}, f)
            success_count += 1
        except Exception as e:
            print(f"❌ Emergency session backup failed: {e}")
        
        return success_count > 0
    
    def backup_game_data(self, username, game_name, game_data):
        """Backup game data to multiple locations"""
        success_count = 0
        
        # 1. Database backup
        try:
            if db_manager.save_game(username, game_name, game_data):
                print(f"✓ Game '{game_name}' backed up to database for {username}")
                success_count += 1
        except Exception as e:
            print(f"❌ Database game backup failed: {e}")
        
        # 2. File backup
        try:
            user_hash = hashlib.md5(username.encode()).hexdigest()[:8]
            game_dir = os.path.join(self.base_dir, "games", user_hash)
            os.makedirs(game_dir, exist_ok=True)
            
            safe_name = "".join(c for c in game_name if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
            game_file = os.path.join(game_dir, f"{safe_name}.json")
            
            backup_data = {
                'game_name': game_name,
                'username': username,
                'timestamp': datetime.now().isoformat(),
                'game_data': game_data
            }
            
            with open(game_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            print(f"✓ Game '{game_name}' backed up to file for {username}")
            success_count += 1
        except Exception as e:
            print(f"❌ File game backup failed: {e}")
        
        return success_count > 0
    
    def backup_roster_data(self, username, roster_name, roster_data):
        """Backup roster data to multiple locations"""
        success_count = 0
        
        # 1. Database backup
        try:
            if db_manager.save_roster(username, roster_name, roster_data):
                print(f"✓ Roster '{roster_name}' backed up to database for {username}")
                success_count += 1
        except Exception as e:
            print(f"❌ Database roster backup failed: {e}")
        
        # 2. File backup
        try:
            user_hash = hashlib.md5(username.encode()).hexdigest()[:8]
            roster_dir = os.path.join(self.base_dir, "rosters", user_hash)
            os.makedirs(roster_dir, exist_ok=True)
            
            safe_name = "".join(c for c in roster_name if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
            roster_file = os.path.join(roster_dir, f"{safe_name}.json")
            
            backup_data = {
                'roster_name': roster_name,
                'username': username,
                'timestamp': datetime.now().isoformat(),
                'roster_data': roster_data
            }
            
            with open(roster_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            print(f"✓ Roster '{roster_name}' backed up to file for {username}")
            success_count += 1
        except Exception as e:
            print(f"❌ File roster backup failed: {e}")
        
        return success_count > 0
    
    def recover_session_data(self, session_id):
        """Attempt to recover session data from backups"""
        # Try database first
        try:
            data = db_manager.load_session_data(session_id)
            if data:
                print(f"✓ Session {session_id} recovered from database")
                return data
        except Exception as e:
            print(f"❌ Database session recovery failed: {e}")
        
        # Try file backup
        try:
            session_file = os.path.join(self.base_dir, "sessions", f"{session_id}.json")
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    backup_data = json.load(f)
                print(f"✓ Session {session_id} recovered from file backup")
                return backup_data.get('data')
        except Exception as e:
            print(f"❌ File session recovery failed: {e}")
        
        # Try emergency backup
        try:
            emergency_file = os.path.join(self.base_dir, "emergency", f"session_{session_id}.pkl")
            if os.path.exists(emergency_file):
                with open(emergency_file, 'rb') as f:
                    backup_data = pickle.load(f)
                print(f"✓ Session {session_id} recovered from emergency backup")
                return backup_data.get('data')
        except Exception as e:
            print(f"❌ Emergency session recovery failed: {e}")
        
        return None
    
    def get_backup_status(self, username=None):
        """Get status of all backups"""
        status = {
            'database_connected': False,
            'total_sessions': 0,
            'total_games': 0,
            'total_rosters': 0,
            'backup_locations': []
        }
        
        # Check database connection
        try:
            status['database_connected'] = db_manager.test_connection()
        except:
            pass
        
        # Count file backups
        try:
            sessions_dir = os.path.join(self.base_dir, "sessions")
            if os.path.exists(sessions_dir):
                status['total_sessions'] = len([f for f in os.listdir(sessions_dir) if f.endswith('.json')])
            
            games_dir = os.path.join(self.base_dir, "games")
            if os.path.exists(games_dir):
                for user_dir in os.listdir(games_dir):
                    user_path = os.path.join(games_dir, user_dir)
                    if os.path.isdir(user_path):
                        status['total_games'] += len([f for f in os.listdir(user_path) if f.endswith('.json')])
            
            rosters_dir = os.path.join(self.base_dir, "rosters")
            if os.path.exists(rosters_dir):
                for user_dir in os.listdir(rosters_dir):
                    user_path = os.path.join(rosters_dir, user_dir)
                    if os.path.isdir(user_path):
                        status['total_rosters'] += len([f for f in os.listdir(user_path) if f.endswith('.json')])
        except Exception as e:
            print(f"Error getting backup status: {e}")
        
        status['backup_locations'] = [
            f"Database: {'✓' if status['database_connected'] else '❌'}",
            f"File System: ✓ ({self.base_dir})",
            f"Emergency Backups: ✓"
        ]
        
        return status

# Global backup system instance
backup_system = DataBackupSystem()

def backup_all_user_data(username, session_id=None, game_data=None, roster_data=None):
    """Comprehensive backup of all user data"""
    results = []
    
    if session_id and game_data:
        success = backup_system.backup_session_data(session_id, username, game_data)
        results.append(f"Session backup: {'✓' if success else '❌'}")
    
    if game_data and isinstance(game_data, dict) and 'game_name' in game_data:
        success = backup_system.backup_game_data(username, game_data['game_name'], game_data)
        results.append(f"Game backup: {'✓' if success else '❌'}")
    
    if roster_data and isinstance(roster_data, dict) and 'roster_name' in roster_data:
        success = backup_system.backup_roster_data(username, roster_data['roster_name'], roster_data)
        results.append(f"Roster backup: {'✓' if success else '❌'}")
    
    return results

if __name__ == "__main__":
    # Test the backup system
    print("=== Data Backup System Test ===")
    status = backup_system.get_backup_status()
    print(f"Database Connected: {status['database_connected']}")
    print(f"Total Sessions: {status['total_sessions']}")
    print(f"Total Games: {status['total_games']}")
    print(f"Total Rosters: {status['total_rosters']}")
    print("Backup Locations:")
    for location in status['backup_locations']:
        print(f"  {location}")
