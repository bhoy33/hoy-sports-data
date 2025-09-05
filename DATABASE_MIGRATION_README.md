# Database Migration and Persistent Storage Implementation

## Overview

The Football Box Stats Analytics app has been upgraded with persistent database storage to prevent data loss during app updates and deployments. The system uses a hybrid approach with PostgreSQL as the primary database and file-based storage as a backup.

## Key Features

### 1. Database Models
- **UserSession**: Stores user session data with pickled binary data
- **UserRoster**: Stores saved player rosters as JSON
- **SavedGame**: Stores saved game data with pickled binary data

### 2. Hybrid Storage System
- **Primary**: PostgreSQL database (Railway production) / SQLite (local development)
- **Backup**: File-based storage for redundancy
- **Automatic Fallback**: If database fails, system falls back to file storage

### 3. Environment Configuration
- **Production**: Uses `DATABASE_URL` environment variable for PostgreSQL
- **Development**: Falls back to SQLite database file
- **Railway**: Automatically detects and fixes PostgreSQL URL format

## Database Schema

### UserSession Table
```sql
CREATE TABLE user_sessions (
    id VARCHAR(255) PRIMARY KEY,           -- session_id
    username VARCHAR(100) NOT NULL,       -- user identifier
    session_data BYTEA NOT NULL,          -- pickled session data
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### UserRoster Table
```sql
CREATE TABLE user_rosters (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    roster_name VARCHAR(200) NOT NULL,
    roster_data TEXT NOT NULL,            -- JSON string
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(username, roster_name)
);
```

### SavedGame Table
```sql
CREATE TABLE saved_games (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    game_name VARCHAR(200) NOT NULL,
    game_data BYTEA NOT NULL,             -- pickled game data
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(username, game_name)
);
```

## Migration Process

### 1. Automatic Migration
The system automatically creates database tables on first run. No manual intervention required.

### 2. Data Migration Utilities
Use the `migrate_data.py` script for advanced operations:

```bash
# Migrate existing file sessions to database
python3 migrate_data.py migrate

# Backup database to files
python3 migrate_data.py backup

# Verify migration success
python3 migrate_data.py verify

# Clean up old files (after successful migration)
python3 migrate_data.py cleanup
```

### 3. Admin Endpoints
Access via admin login (`Jackets21!`):

- `POST /admin/migrate_data` - Migrate file sessions to database
- `POST /admin/backup_database` - Backup database to files
- `GET /admin/database_status` - View database statistics

## Deployment Instructions

### Railway Deployment

1. **Add PostgreSQL Database**:
   ```bash
   # In Railway dashboard, add PostgreSQL service to your project
   # Railway will automatically set DATABASE_URL environment variable
   ```

2. **Deploy Application**:
   ```bash
   git add .
   git commit -m "Database migration implementation"
   git push
   # Railway auto-deploys from GitHub
   ```

3. **Verify Database Connection**:
   - Check Railway logs for "Database tables created successfully"
   - Access `/admin/database_status` endpoint as admin

### Local Development

1. **Install Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Run Application**:
   ```bash
   python3 app.py
   ```
   - Uses SQLite database (`football_stats.db`)
   - Database tables created automatically

## Data Persistence Benefits

### Before (File-Based)
- ❌ Data lost during Railway deployments
- ❌ No cross-deployment persistence
- ❌ Limited scalability
- ✅ Simple local development

### After (Database + File Hybrid)
- ✅ Data persists across deployments
- ✅ Scalable database storage
- ✅ Automatic backups to files
- ✅ Fallback to file storage if database fails
- ✅ Cross-device data access
- ✅ Admin management tools

## Backward Compatibility

The system maintains full backward compatibility:
- Existing file-based sessions continue to work
- Gradual migration to database storage
- No data loss during transition
- File backups maintained for safety

## Monitoring and Maintenance

### Database Status
Check database health via admin dashboard:
- Session count and recent activity
- Roster and saved game statistics
- Database connection status

### Backup Strategy
- **Primary**: PostgreSQL database (Railway managed)
- **Secondary**: File-based backups (automatic)
- **Manual**: Admin backup endpoints

### Cleanup
- Old file sessions can be safely deleted after migration
- Database includes automatic timestamp tracking
- Optional cleanup of sessions older than 30 days

## Troubleshooting

### Database Connection Issues
1. Check `DATABASE_URL` environment variable
2. Verify PostgreSQL service is running (Railway)
3. Check Railway logs for connection errors
4. System automatically falls back to file storage

### Migration Issues
1. Use `migrate_data.py verify` to check migration status
2. Run `migrate_data.py backup` before cleanup
3. Check file permissions in `server_sessions` directory

### Performance
- Database queries are optimized with indexes
- Large session data uses binary storage (pickle)
- Connection pooling enabled for production

## Security Considerations

- Session data encrypted via pickle serialization
- Database credentials managed via environment variables
- Admin endpoints require authentication
- User data isolated by username

## Future Enhancements

- Database connection pooling optimization
- Automated backup scheduling
- Data retention policies
- Performance monitoring
- Multi-region database support

---

This implementation ensures that all user data (game stats, rosters, player data) persists across app updates and deployments, providing a reliable and scalable foundation for the Football Box Stats Analytics application.
