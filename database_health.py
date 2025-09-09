#!/usr/bin/env python3
"""
Database health monitoring and recovery utilities for Railway deployments
"""
import os
import time
import logging
from datetime import datetime
from database import DatabaseManager, db, UserSession, UserRoster, SavedGame
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_app():
    """Create a minimal Flask app for database testing"""
    app = Flask(__name__)
    
    # Configure database URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///football_stats.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    return app

def test_database_connection(max_retries=10):
    """Test database connection with retries"""
    app = create_test_app()
    db_manager = DatabaseManager(app)
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                # Test basic connection
                if db_manager.verify_database_connection():
                    logger.info(f"✓ Database connection successful on attempt {attempt + 1}")
                    return True
                else:
                    logger.warning(f"Database connection failed on attempt {attempt + 1}")
                    
        except Exception as e:
            logger.error(f"Database connection error on attempt {attempt + 1}: {e}")
            
        if attempt < max_retries - 1:
            wait_time = min(2 ** attempt, 30)  # Exponential backoff, max 30 seconds
            logger.info(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
    
    logger.error("❌ Database connection failed after all retries")
    return False

def verify_database_schema():
    """Verify all required tables exist with correct schema"""
    app = create_test_app()
    db_manager = DatabaseManager(app)
    
    try:
        with app.app_context():
            db.init_app(app)
            
            # Get table information
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            expected_tables = ['user_sessions', 'user_rosters', 'saved_games']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                logger.warning(f"Missing tables: {missing_tables}")
                logger.info("Creating missing tables...")
                db.create_all()
                logger.info("✓ Tables created successfully")
            else:
                logger.info("✓ All required tables exist")
            
            # Verify table schemas
            for table_name in expected_tables:
                columns = inspector.get_columns(table_name)
                column_names = [col['name'] for col in columns]
                logger.info(f"Table {table_name} columns: {column_names}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Schema verification failed: {e}")
        return False

def get_database_stats():
    """Get database statistics for monitoring"""
    app = create_test_app()
    
    try:
        with app.app_context():
            db.init_app(app)
            
            # Count records in each table
            session_count = UserSession.query.count()
            roster_count = UserRoster.query.count()
            game_count = SavedGame.query.count()
            
            stats = {
                'user_sessions': session_count,
                'user_rosters': roster_count,
                'saved_games': game_count,
                'total_records': session_count + roster_count + game_count,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Database stats: {stats}")
            return stats
            
    except Exception as e:
        logger.error(f"❌ Failed to get database stats: {e}")
        return None

def cleanup_old_sessions(days_old=30):
    """Clean up old session data"""
    app = create_test_app()
    
    try:
        with app.app_context():
            db.init_app(app)
            
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_sessions = UserSession.query.filter(
                UserSession.updated_at < cutoff_date
            ).all()
            
            for session in old_sessions:
                db.session.delete(session)
            
            db.session.commit()
            logger.info(f"✓ Cleaned up {len(old_sessions)} old sessions")
            return len(old_sessions)
            
    except Exception as e:
        logger.error(f"❌ Failed to cleanup old sessions: {e}")
        return 0

def main():
    """Main health check routine"""
    logger.info("=== Database Health Check ===")
    
    # Test connection
    if not test_database_connection():
        logger.error("Database connection failed - exiting")
        exit(1)
    
    # Verify schema
    if not verify_database_schema():
        logger.error("Schema verification failed - exiting")
        exit(1)
    
    # Get stats
    stats = get_database_stats()
    if stats:
        logger.info(f"Database is healthy with {stats['total_records']} total records")
    
    # Optional cleanup
    if os.environ.get('CLEANUP_OLD_SESSIONS', '').lower() == 'true':
        cleanup_old_sessions()
    
    logger.info("✓ Database health check completed successfully")

if __name__ == "__main__":
    main()
