"""
Database models and connection management for persistent user data storage.
"""
import os
import json
import pickle
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()

class UserSession(db.Model):
    """Store user session data persistently in database"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.String(255), primary_key=True)  # session_id
    username = db.Column(db.String(100), nullable=False, index=True)
    session_data = db.Column(db.LargeBinary, nullable=False)  # pickled data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserSession {self.id} - {self.username}>'

class UserRoster(db.Model):
    """Store user roster data persistently"""
    __tablename__ = 'user_rosters'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, index=True)
    roster_name = db.Column(db.String(200), nullable=False)
    roster_data = db.Column(db.Text, nullable=False)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint on username + roster_name
    __table_args__ = (db.UniqueConstraint('username', 'roster_name', name='unique_user_roster'),)
    
    def __repr__(self):
        return f'<UserRoster {self.username} - {self.roster_name}>'

class SavedGame(db.Model):
    """Store saved game data persistently"""
    __tablename__ = 'saved_games'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, index=True)
    game_name = db.Column(db.String(200), nullable=False)
    game_data = db.Column(db.LargeBinary, nullable=False)  # pickled data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint on username + game_name
    __table_args__ = (db.UniqueConstraint('username', 'game_name', name='unique_user_game'),)
    
    def __repr__(self):
        return f'<SavedGame {self.username} - {self.game_name}>'

class DatabaseManager:
    """Manage database operations for user data persistence"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize database with Flask app"""
        # Configure database URL
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            # Railway PostgreSQL URL format fix
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        else:
            # Fallback to SQLite for local development
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///football_stats.db'
        
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }
        
        db.init_app(app)
        
        with app.app_context():
            try:
                # Create tables if they don't exist
                db.create_all()
                print("Database tables created successfully")
            except Exception as e:
                print(f"Error creating database tables: {e}")
    
    def save_session_data(self, session_id, username, data):
        """Save session data to database"""
        try:
            # Serialize data
            pickled_data = pickle.dumps(data)
            
            # Check if session exists
            session = UserSession.query.filter_by(id=session_id).first()
            
            if session:
                # Update existing session
                session.session_data = pickled_data
                session.updated_at = datetime.utcnow()
            else:
                # Create new session
                session = UserSession(
                    id=session_id,
                    username=username,
                    session_data=pickled_data
                )
                db.session.add(session)
            
            db.session.commit()
            print(f"Session data saved for {username} (session: {session_id})")
            return True
            
        except Exception as e:
            print(f"Error saving session data: {e}")
            db.session.rollback()
            return False
    
    def load_session_data(self, session_id):
        """Load session data from database"""
        try:
            session = UserSession.query.filter_by(id=session_id).first()
            if session:
                data = pickle.loads(session.session_data)
                print(f"Session data loaded for session: {session_id}")
                return data
            else:
                print(f"No session data found for session: {session_id}")
                return {}
                
        except Exception as e:
            print(f"Error loading session data: {e}")
            return {}
    
    def delete_session_data(self, session_id):
        """Delete session data from database"""
        try:
            session = UserSession.query.filter_by(id=session_id).first()
            if session:
                db.session.delete(session)
                db.session.commit()
                print(f"Session data deleted for session: {session_id}")
                return True
            return False
            
        except Exception as e:
            print(f"Error deleting session data: {e}")
            db.session.rollback()
            return False
    
    def save_roster(self, username, roster_name, roster_data):
        """Save roster data to database"""
        try:
            # Serialize roster data as JSON
            json_data = json.dumps(roster_data)
            
            # Check if roster exists
            roster = UserRoster.query.filter_by(username=username, roster_name=roster_name).first()
            
            if roster:
                # Update existing roster
                roster.roster_data = json_data
                roster.updated_at = datetime.utcnow()
            else:
                # Create new roster
                roster = UserRoster(
                    username=username,
                    roster_name=roster_name,
                    roster_data=json_data
                )
                db.session.add(roster)
            
            db.session.commit()
            print(f"Roster '{roster_name}' saved for {username}")
            return True
            
        except Exception as e:
            print(f"Error saving roster: {e}")
            db.session.rollback()
            return False
    
    def load_roster(self, username, roster_name):
        """Load roster data from database"""
        try:
            roster = UserRoster.query.filter_by(username=username, roster_name=roster_name).first()
            if roster:
                data = json.loads(roster.roster_data)
                print(f"Roster '{roster_name}' loaded for {username}")
                return data
            else:
                print(f"No roster '{roster_name}' found for {username}")
                return None
                
        except Exception as e:
            print(f"Error loading roster: {e}")
            return None
    
    def get_user_rosters(self, username):
        """Get all rosters for a user"""
        try:
            rosters = UserRoster.query.filter_by(username=username).order_by(UserRoster.updated_at.desc()).all()
            roster_list = []
            for roster in rosters:
                roster_list.append({
                    'name': roster.roster_name,
                    'created_at': roster.created_at.isoformat(),
                    'updated_at': roster.updated_at.isoformat()
                })
            return roster_list
            
        except Exception as e:
            print(f"Error getting user rosters: {e}")
            return []
    
    def delete_roster(self, username, roster_name):
        """Delete roster from database"""
        try:
            roster = UserRoster.query.filter_by(username=username, roster_name=roster_name).first()
            if roster:
                db.session.delete(roster)
                db.session.commit()
                print(f"Roster '{roster_name}' deleted for {username}")
                return True
            return False
            
        except Exception as e:
            print(f"Error deleting roster: {e}")
            db.session.rollback()
            return False
    
    def save_game(self, username, game_name, game_data):
        """Save game data to database"""
        try:
            # Serialize game data
            pickled_data = pickle.dumps(game_data)
            
            # Check if game exists
            game = SavedGame.query.filter_by(username=username, game_name=game_name).first()
            
            if game:
                # Update existing game
                game.game_data = pickled_data
                game.updated_at = datetime.utcnow()
            else:
                # Create new game
                game = SavedGame(
                    username=username,
                    game_name=game_name,
                    game_data=pickled_data
                )
                db.session.add(game)
            
            db.session.commit()
            print(f"Game '{game_name}' saved for {username}")
            return True
            
        except Exception as e:
            print(f"Error saving game: {e}")
            db.session.rollback()
            return False
    
    def load_game(self, username, game_name):
        """Load game data from database"""
        try:
            game = SavedGame.query.filter_by(username=username, game_name=game_name).first()
            if game:
                data = pickle.loads(game.game_data)
                print(f"Game '{game_name}' loaded for {username}")
                return data
            else:
                print(f"No game '{game_name}' found for {username}")
                return None
                
        except Exception as e:
            print(f"Error loading game: {e}")
            return None
    
    def get_user_games(self, username):
        """Get all saved games for a user"""
        try:
            games = SavedGame.query.filter_by(username=username).order_by(SavedGame.updated_at.desc()).all()
            game_list = []
            for game in games:
                game_list.append({
                    'name': game.game_name,
                    'created_at': game.created_at.isoformat(),
                    'updated_at': game.updated_at.isoformat()
                })
            return game_list
            
        except Exception as e:
            print(f"Error getting user games: {e}")
            return []
    
    def delete_game(self, username, game_name):
        """Delete game from database"""
        try:
            game = SavedGame.query.filter_by(username=username, game_name=game_name).first()
            if game:
                db.session.delete(game)
                db.session.commit()
                print(f"Game '{game_name}' deleted for {username}")
                return True
            return False
            
        except Exception as e:
            print(f"Error deleting game: {e}")
            db.session.rollback()
            return False
    
    def cleanup_old_sessions(self, days_old=30):
        """Clean up old session data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            old_sessions = UserSession.query.filter(UserSession.updated_at < cutoff_date).all()
            
            for session in old_sessions:
                db.session.delete(session)
            
            db.session.commit()
            print(f"Cleaned up {len(old_sessions)} old sessions")
            return len(old_sessions)
            
        except Exception as e:
            print(f"Error cleaning up old sessions: {e}")
            db.session.rollback()
            return 0
