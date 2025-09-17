"""
Supabase configuration and database operations for Hoy Sports Data App
"""
import os
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import Supabase with fallback
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Supabase not available: {e}")
    SUPABASE_AVAILABLE = False
    Client = None

class SupabaseManager:
    """Manages all Supabase database operations for the sports data app"""
    
    def __init__(self):
        """Initialize Supabase client with environment variables"""
        self.url = os.getenv('SUPABASE_URL')
        self.anon_key = os.getenv('SUPABASE_ANON_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase library not available")
            self.supabase = None
            self.supabase_admin = None
        elif not self.url or not self.anon_key:
            logger.warning("Supabase credentials not found in environment variables")
            self.supabase = None
            self.supabase_admin = None
        else:
            try:
                # Regular client with anon key for standard operations
                self.supabase: Client = create_client(self.url, self.anon_key)
                logger.info("Supabase client initialized successfully")
                
                # Admin client with service role key for bypassing RLS
                if self.service_key:
                    self.supabase_admin: Client = create_client(self.url, self.service_key)
                    logger.info("Supabase admin client initialized successfully")
                else:
                    self.supabase_admin = None
                    logger.warning("Service role key not found - admin operations may fail")
                    
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.supabase = None
                self.supabase_admin = None
    
    def is_connected(self) -> bool:
        """Check if Supabase connection is available"""
        return self.supabase is not None
    
    def test_connection(self) -> bool:
        """Test the database connection"""
        if not self.supabase:
            return False
        
        try:
            # Simple query to test connection
            result = self.supabase.table('users').select('id').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    # User Management
    def create_user(self, username: str, password_hash: str, email: str = None, is_admin: bool = False) -> Optional[Dict]:
        """Create a new user"""
        if not self.supabase:
            return None
        
        try:
            user_data = {
                'username': username,
                'password_hash': password_hash,
                'email': email,
                'is_admin': is_admin
            }
            
            result = self.supabase.table('users').insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        if not self.supabase:
            return None
        
        try:
            result = self.supabase.table('users').select('*').eq('username', username).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
    
    # Game Session Management
    def create_game_session(self, user_id: str, session_data: Dict) -> Optional[Dict]:
        """Create a new game session using admin client to bypass RLS"""
        # Use admin client if available to bypass RLS, otherwise fall back to regular client
        client = self.supabase_admin if self.supabase_admin else self.supabase
        
        if not client:
            return None
        
        try:
            session_record = {
                'user_id': user_id,
                'session_name': session_data.get('session_name'),
                'game_date': session_data.get('game_date'),
                'opponent': session_data.get('opponent'),
                'location': session_data.get('location'),
                'weather_conditions': session_data.get('weather_conditions'),
                'game_type': session_data.get('game_type', 'regular'),
                'status': 'active'
            }
            
            result = client.table('game_sessions').insert(session_record).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to create game session: {e}")
            return None
    
    def save_game_session(self, user_id: str, session_data: Dict) -> bool:
        """Save game session data to Supabase"""
        try:
            # Use admin client if available to bypass RLS, otherwise fall back to regular client
            client = self.supabase_admin if self.supabase_admin else self.supabase
            
            if not client:
                return False
            
            session_record = {
                'user_id': user_id,
                'session_name': session_name,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'status': 'active',
                'box_stats': session_data
            }
            
            print(f"DEBUG: Saving game session to Supabase:")
            print(f"  User ID: {user_id}")
            print(f"  Session Name: {session_name}")
            print(f"  Box Stats Keys: {list(session_data.keys()) if isinstance(session_data, dict) else 'Not a dict'}")
            
            result = self.supabase.table('game_sessions').insert(session_record).execute()
            
            if result.data:
                logger.info(f"Game session saved successfully for user {user_id}")
                print(f"✓ Game session '{session_name}' saved to Supabase with ID: {result.data[0].get('id')}")
                return True
            else:
                logger.error(f"Failed to save game session for user {user_id}")
                print(f"❌ Failed to save game session - no data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error saving game session: {e}")
            print(f"❌ Exception saving game session: {e}")
            return False
    
    def get_user_rosters(self, user_id: str) -> List[Dict]:
        """Get all rosters for a specific user from Supabase"""
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return []
            
            result = self.supabase.table('rosters').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                logger.info(f"Retrieved {len(result.data)} rosters for user {user_id}")
                return result.data
            else:
                logger.info(f"No rosters found for user {user_id}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting user rosters from Supabase: {e}")
            return []
    
    def get_user_game_sessions(self, user_id: str) -> List[Dict]:
        """Get all game sessions for a specific user from Supabase"""
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return []
            
            result = self.supabase.table('game_sessions').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                logger.info(f"Retrieved {len(result.data)} game sessions for user {user_id}")
                return result.data
            else:
                logger.info(f"No game sessions found for user {user_id}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting user game sessions from Supabase: {e}")
            return []
    
    def delete_roster(self, user_id: str, roster_name: str) -> bool:
        """Delete a roster for a specific user from Supabase"""
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return False
            
            result = self.supabase.table('rosters').delete().eq('user_id', user_id).eq('name', roster_name).execute()
            
            if result.data:
                logger.info(f"Deleted roster '{roster_name}' for user {user_id}")
                return True
            else:
                logger.warning(f"No roster found to delete: '{roster_name}' for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting roster from Supabase: {e}")
            return False

    def get_user_sessions(self, user_id: str) -> List[Dict]:
        """Get all sessions for a user"""
        if not self.supabase:
            return []
        
        try:
            result = self.supabase.table('game_sessions').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []
    
    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        if not self.supabase:
            return None
        
        try:
            result = self.supabase.table('game_sessions').select('*').eq('id', session_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    def update_session_status(self, session_id: str, status: str) -> bool:
        """Update session status"""
        if not self.supabase:
            return False
        
        try:
            result = self.supabase.table('game_sessions').update({'status': status}).eq('id', session_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to update session status: {e}")
            return False
    
    # Player Management
    def create_player(self, user_id: str, player_data: Dict) -> Optional[Dict]:
        """Create a new player"""
        if not self.supabase:
            return None
        
        try:
            player_record = {
                'user_id': user_id,
                'name': player_data.get('name'),
                'number': player_data.get('number'),
                'position': player_data.get('position'),
                'class_year': player_data.get('class_year'),
                'height': player_data.get('height'),
                'weight': player_data.get('weight'),
                'is_active': True
            }
            
            result = self.supabase.table('players').insert(player_record).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to create player: {e}")
            return None
    
    def get_user_players(self, user_id: str) -> List[Dict]:
        """Get all active players for a user"""
        if not self.supabase:
            return []
        
        try:
            result = self.supabase.table('players').select('*').eq('user_id', user_id).eq('is_active', True).order('number').execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get user players: {e}")
            return []
    
    # Play Management
    def create_play(self, session_id: str, play_data: Dict) -> Optional[Dict]:
        """Create a new play"""
        if not self.supabase:
            return None
        
        try:
            play_record = {
                'session_id': session_id,
                'play_number': play_data.get('play_number'),
                'quarter': play_data.get('quarter'),
                'down': play_data.get('down'),
                'distance': play_data.get('distance'),
                'yard_line': play_data.get('yard_line'),
                'play_type': play_data.get('play_type'),
                'play_call': play_data.get('play_call'),
                'phase': play_data.get('phase'),
                'yards_gained': play_data.get('yards_gained', 0),
                'result': play_data.get('result'),
                'time_remaining': play_data.get('time_remaining'),
                'score_home': play_data.get('score_home', 0),
                'score_away': play_data.get('score_away', 0),
                'notes': play_data.get('notes')
            }
            
            result = self.supabase.table('plays').insert(play_record).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to create play: {e}")
            return None
    
    def create_play_player(self, play_id: str, player_id: str, player_involvement: Dict) -> Optional[Dict]:
        """Create player involvement in a play"""
        if not self.supabase:
            return None
        
        try:
            play_player_record = {
                'play_id': play_id,
                'player_id': player_id,
                'role': player_involvement.get('role'),
                'yards_gained': player_involvement.get('yards_gained', 0),
                'is_touchdown': player_involvement.get('touchdown', False),
                'is_fumble': player_involvement.get('fumble', False),
                'is_interception': player_involvement.get('interception', False),
                'is_first_down': player_involvement.get('first_down', False),
                'is_penalty': player_involvement.get('penalty', False),
                'penalty_type': player_involvement.get('penalty_type'),
                'penalty_yards': player_involvement.get('penalty_yards', 0)
            }
            
            result = self.supabase.table('play_players').insert(play_player_record).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to create play player: {e}")
            return None
    
    def get_session_plays(self, session_id: str) -> List[Dict]:
        """Get all plays for a session with player involvement"""
        if not self.supabase:
            return []
        
        try:
            # Get plays with player involvement
            result = self.supabase.table('plays').select('''
                *,
                play_players (
                    *,
                    players (
                        name,
                        number,
                        position
                    )
                )
            ''').eq('session_id', session_id).order('play_number').execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get session plays: {e}")
            return []
    
    # Statistics Management
    def upsert_team_stats(self, session_id: str, phase: str, stats: Dict) -> bool:
        """Insert or update team statistics"""
        if not self.supabase:
            return False
        
        try:
            stats_record = {
                'session_id': session_id,
                'phase': phase,
                **stats
            }
            
            result = self.supabase.table('team_stats').upsert(stats_record, on_conflict='session_id,phase').execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to upsert team stats: {e}")
            return False
    
    def upsert_player_stats(self, session_id: str, player_id: str, stats: Dict) -> bool:
        """Insert or update player statistics"""
        if not self.supabase:
            return False
        
        try:
            stats_record = {
                'session_id': session_id,
                'player_id': player_id,
                **stats
            }
            
            result = self.supabase.table('player_stats').upsert(stats_record, on_conflict='session_id,player_id').execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to upsert player stats: {e}")
            return False
    
    def get_team_stats(self, session_id: str) -> Dict[str, Dict]:
        """Get all team statistics for a session"""
        if not self.supabase:
            return {}
        
        try:
            result = self.supabase.table('team_stats').select('*').eq('session_id', session_id).execute()
            
            stats_by_phase = {}
            for stat in result.data or []:
                phase = stat.pop('phase')
                stats_by_phase[phase] = stat
            
            return stats_by_phase
        except Exception as e:
            logger.error(f"Failed to get team stats: {e}")
            return {}
    
    def get_player_stats(self, session_id: str) -> Dict[str, Dict]:
        """Get all player statistics for a session"""
        if not self.supabase:
            return {}
        
        try:
            result = self.supabase.table('player_stats').select('''
                *,
                players (
                    name,
                    number,
                    position
                )
            ''').eq('session_id', session_id).execute()
            
            stats_by_player = {}
            for stat in result.data or []:
                player_info = stat.pop('players')
                player_key = f"{player_info['name']}_{player_info['number']}"
                stats_by_player[player_key] = {**stat, **player_info}
            
            return stats_by_player
        except Exception as e:
            logger.error(f"Failed to get player stats: {e}")
            return {}
    
    # Progressive Statistics
    def create_progressive_stat(self, session_id: str, phase: str, play_number: int, stats: Dict) -> bool:
        """Create a progressive statistic entry"""
        if not self.supabase:
            return False
        
        try:
            progressive_record = {
                'session_id': session_id,
                'phase': phase,
                'play_number': play_number,
                'quarter': stats.get('quarter'),
                'efficiency_rate': stats.get('efficiency_rate', 0.0),
                'explosive_rate': stats.get('explosive_rate', 0.0),
                'negative_rate': stats.get('negative_rate', 0.0),
                'nee_score': stats.get('nee_score', 0.0),
                'total_plays': stats.get('total_plays', 0),
                'total_yards': stats.get('total_yards', 0)
            }
            
            result = self.supabase.table('progressive_stats').insert(progressive_record).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to create progressive stat: {e}")
            return False
    
    def get_progressive_stats(self, session_id: str, phase: str) -> List[Dict]:
        """Get progressive statistics for a session and phase"""
        if not self.supabase:
            return []
        
        try:
            result = self.supabase.table('progressive_stats').select('*').eq('session_id', session_id).eq('phase', phase).order('play_number').execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get progressive stats: {e}")
            return []
    
    # Data Backup Tracking
    def create_backup_record(self, session_id: str, backup_type: str, backup_path: str = None, backup_size: int = None) -> bool:
        """Create a backup record"""
        if not self.supabase:
            return False
        
        try:
            backup_record = {
                'session_id': session_id,
                'backup_type': backup_type,
                'backup_path': backup_path,
                'backup_size': backup_size,
                'backup_status': 'active'
            }
            
            result = self.supabase.table('data_backups').insert(backup_record).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to create backup record: {e}")
            return False
    
    def get_backup_status(self, session_id: str) -> List[Dict]:
        """Get backup status for a session"""
        if not self.supabase:
            return []
        
        try:
            result = self.supabase.table('data_backups').select('*').eq('session_id', session_id).order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get backup status: {e}")
            return []
    
    def save_roster(self, user_id: str, roster_name: str, roster_data: Dict) -> bool:
        """Save roster data to Supabase"""
        if not self.supabase:
            return False
        
        try:
            # Use actual schema: name and players columns (based on error log)
            roster_record = {
                'user_id': user_id,
                'name': roster_name,  # Actual column name is 'name'
                'players': json.dumps(roster_data),  # Actual column name is 'players', needs JSON string
            }
            
            # Check if roster already exists for this user
            existing = self.supabase.table('rosters').select('id').eq('user_id', user_id).eq('name', roster_name).execute()
            
            if existing.data:
                # Update existing roster
                result = self.supabase.table('rosters').update({
                    'players': json.dumps(roster_data),
                }).eq('user_id', user_id).eq('name', roster_name).execute()
                logger.info(f"Updated existing roster '{roster_name}' for user {user_id}")
            else:
                # Insert new roster
                result = self.supabase.table('rosters').insert(roster_record).execute()
                logger.info(f"Created new roster '{roster_name}' for user {user_id}")
            
            if result.data:
                logger.info(f"Successfully saved roster '{roster_name}' for user {user_id}")
                return True
            else:
                logger.error(f"No data returned when saving roster '{roster_name}' for user {user_id}")
                return False
        except Exception as e:
            logger.error(f"Exception saving roster '{roster_name}' for user {user_id}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def save_game_session(self, user_id: str, game_name: str, game_data: Dict) -> bool:
        """Save game session data to Supabase using existing schema"""
        if not self.supabase:
            return False
        
        try:
            # Use the create_game_session method which matches existing schema
            session_record = self.create_game_session(user_id, {
                'session_name': game_name,
                'game_date': game_data.get('game_date', datetime.now().date().isoformat()),
                'opponent': game_data.get('opponent', 'Unknown'),
                'location': game_data.get('location'),
                'weather_conditions': game_data.get('weather_conditions'),
                'game_type': game_data.get('game_type', 'regular')
            })
            
            return session_record is not None
        except Exception as e:
            logger.error(f"Failed to save game session: {e}")
            return False
    
    # Migration and Data Recovery
    def migrate_session_data(self, session_data: Dict, user_id: str) -> Optional[str]:
        """Migrate existing session data to Supabase"""
        if not self.supabase:
            return None
        
        try:
            # Create game session
            session_record = self.create_game_session(user_id, {
                'session_name': session_data.get('session_name', 'Migrated Session'),
                'game_date': datetime.now().date().isoformat(),
                'opponent': session_data.get('opponent', 'Unknown'),
                'game_type': 'regular'
            })
            
            if not session_record:
                return None
            
            session_id = session_record['id']
            
            # Migrate plays if they exist
            box_stats = session_data.get('box_stats', {})
            plays = box_stats.get('plays', [])
            
            for i, play in enumerate(plays):
                play_record = self.create_play(session_id, {
                    'play_number': i + 1,
                    'quarter': play.get('quarter'),
                    'down': play.get('down'),
                    'distance': play.get('distance'),
                    'yard_line': play.get('yard_line'),
                    'play_type': play.get('play_type'),
                    'play_call': play.get('play_call'),
                    'phase': play.get('phase'),
                    'yards_gained': play.get('yards_gained', 0),
                    'result': play.get('result'),
                    'time_remaining': play.get('time_remaining')
                })
                
                if play_record:
                    # Migrate player involvement
                    for player in play.get('players_involved', []):
                        # Create player if doesn't exist
                        player_record = self.create_player(user_id, {
                            'name': player.get('name', 'Unknown'),
                            'number': player.get('number', 0),
                            'position': player.get('position', '')
                        })
                        
                        if player_record:
                            self.create_play_player(play_record['id'], player_record['id'], player)
            
            # Migrate team statistics
            team_stats = box_stats.get('team_stats', {})
            for phase, stats in team_stats.items():
                self.upsert_team_stats(session_id, phase, stats)
            
            # Migrate player statistics
            player_stats = box_stats.get('players', {})
            for player_key, stats in player_stats.items():
                # Find or create player
                name = stats.get('name', 'Unknown')
                number = stats.get('number', 0)
                
                player_record = self.create_player(user_id, {
                    'name': name,
                    'number': number,
                    'position': stats.get('position', '')
                })
                
                if player_record:
                    self.upsert_player_stats(session_id, player_record['id'], stats)
            
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to migrate session data: {e}")
            return None

# Global instance
supabase_manager = SupabaseManager()
