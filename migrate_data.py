"""
Data migration script to transfer existing file-based session data to database
"""
import os
import pickle
import json
from datetime import datetime
from database import DatabaseManager, db, UserSession, UserRoster, SavedGame
from flask import Flask

def create_migration_app():
    """Create Flask app for migration"""
    app = Flask(__name__)
    
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
    
    db_manager = DatabaseManager(app)
    return app, db_manager

def migrate_file_sessions_to_database(session_dir='server_sessions'):
    """Migrate existing file-based sessions to database"""
    app, db_manager = create_migration_app()
    
    with app.app_context():
        migrated_count = 0
        error_count = 0
        
        print(f"Starting migration from {session_dir}...")
        
        if not os.path.exists(session_dir):
            print(f"Session directory {session_dir} does not exist")
            return 0, 0
        
        # Walk through all session files
        for root, dirs, files in os.walk(session_dir):
            for file in files:
                if file.endswith('.pkl') and not file.startswith('backup_'):
                    file_path = os.path.join(root, file)
                    session_id = file.replace('.pkl', '')
                    
                    try:
                        # Load session data from file
                        with open(file_path, 'rb') as f:
                            session_data = pickle.load(f)
                        
                        # Handle both old format (direct data) and new format (wrapped data)
                        if isinstance(session_data, dict) and 'session_data' in session_data:
                            actual_data = session_data['session_data']
                        else:
                            actual_data = session_data
                        
                        # Extract username from session data if available
                        username = 'migrated_user'
                        if isinstance(actual_data, dict):
                            if 'username' in actual_data:
                                username = actual_data['username']
                            elif 'user_info' in actual_data and 'username' in actual_data['user_info']:
                                username = actual_data['user_info']['username']
                        
                        # Check if session already exists in database
                        existing_session = UserSession.query.filter_by(id=session_id).first()
                        if existing_session:
                            print(f"Session {session_id} already exists in database, skipping")
                            continue
                        
                        # Save to database
                        if db_manager.save_session_data(session_id, username, actual_data):
                            migrated_count += 1
                            print(f"Migrated session {session_id} for user {username}")
                        else:
                            error_count += 1
                            print(f"Failed to migrate session {session_id}")
                            
                    except Exception as e:
                        error_count += 1
                        print(f"Error migrating session {session_id}: {e}")
        
        print(f"Migration complete: {migrated_count} sessions migrated, {error_count} errors")
        return migrated_count, error_count

def backup_database_to_files(backup_dir='database_backup'):
    """Backup database sessions to files as a safety measure"""
    app, db_manager = create_migration_app()
    
    with app.app_context():
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        backup_count = 0
        error_count = 0
        
        print(f"Starting database backup to {backup_dir}...")
        
        # Backup all sessions
        sessions = UserSession.query.all()
        for session in sessions:
            try:
                # Create subdirectory based on first 2 chars of session ID
                subdir = os.path.join(backup_dir, session.id[:2])
                if not os.path.exists(subdir):
                    os.makedirs(subdir)
                
                # Save session data to file
                backup_file = os.path.join(subdir, f"{session.id}.pkl")
                session_data = pickle.loads(session.session_data)
                
                session_wrapper = {
                    'session_data': session_data,
                    'username': session.username,
                    'created_at': session.created_at.isoformat(),
                    'updated_at': session.updated_at.isoformat()
                }
                
                with open(backup_file, 'wb') as f:
                    pickle.dump(session_wrapper, f)
                
                backup_count += 1
                print(f"Backed up session {session.id} for user {session.username}")
                
            except Exception as e:
                error_count += 1
                print(f"Error backing up session {session.id}: {e}")
        
        print(f"Backup complete: {backup_count} sessions backed up, {error_count} errors")
        return backup_count, error_count

def cleanup_old_file_sessions(session_dir='server_sessions', confirm=True):
    """Clean up old file-based sessions after successful migration"""
    if confirm:
        response = input(f"Are you sure you want to delete all files in {session_dir}? (yes/no): ")
        if response.lower() != 'yes':
            print("Cleanup cancelled")
            return 0
    
    deleted_count = 0
    
    if not os.path.exists(session_dir):
        print(f"Session directory {session_dir} does not exist")
        return 0
    
    print(f"Cleaning up files in {session_dir}...")
    
    # Remove all .pkl files
    for root, dirs, files in os.walk(session_dir):
        for file in files:
            if file.endswith('.pkl'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"Deleted {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
    
    print(f"Cleanup complete: {deleted_count} files deleted")
    return deleted_count

def verify_migration():
    """Verify that migration was successful by comparing counts"""
    app, db_manager = create_migration_app()
    
    with app.app_context():
        # Count database sessions
        db_session_count = UserSession.query.count()
        print(f"Database sessions: {db_session_count}")
        
        # Count file sessions
        session_dir = 'server_sessions'
        file_session_count = 0
        
        if os.path.exists(session_dir):
            for root, dirs, files in os.walk(session_dir):
                for file in files:
                    if file.endswith('.pkl') and not file.startswith('backup_'):
                        file_session_count += 1
        
        print(f"File sessions: {file_session_count}")
        
        if db_session_count >= file_session_count:
            print("✅ Migration verification successful")
            return True
        else:
            print("❌ Migration verification failed - database has fewer sessions than files")
            return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrate_data.py [migrate|backup|cleanup|verify]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'migrate':
        migrate_file_sessions_to_database()
    elif command == 'backup':
        backup_database_to_files()
    elif command == 'cleanup':
        cleanup_old_file_sessions()
    elif command == 'verify':
        verify_migration()
    else:
        print("Unknown command. Use: migrate, backup, cleanup, or verify")
