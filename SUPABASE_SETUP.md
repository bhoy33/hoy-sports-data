# Supabase Setup Guide for Hoy Sports Data App

## Overview
This guide walks you through setting up Supabase as the primary database for your sports analytics application, replacing the current file-based storage system.

## Prerequisites
1. Supabase account (free tier available)
2. Python environment with updated dependencies

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Choose your organization
4. Set project details:
   - **Name**: `hoy-sports-data`
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your users
5. Click "Create new project"

## Step 2: Run Database Schema

1. In your Supabase dashboard, go to the **SQL Editor**
2. Copy the contents of `supabase_schema.sql`
3. Paste into the SQL Editor and click **Run**
4. Verify tables are created in the **Table Editor**

## Step 3: Get API Credentials

1. Go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9`)

## Step 4: Environment Variables

Create a `.env` file in your project root:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# Railway Configuration (if using Railway)
DATABASE_URL=postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres

# App Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
```

## Step 5: Install Dependencies

```bash
pip install -r requirements_supabase.txt
```

## Step 6: Test Connection

```python
from supabase_config import supabase_manager

# Test connection
if supabase_manager.test_connection():
    print("✅ Supabase connection successful!")
else:
    print("❌ Supabase connection failed")
```

## Step 7: Data Migration

The system includes automatic migration capabilities:

```python
# Migrate existing session data
session_id = supabase_manager.migrate_session_data(old_session_data, user_id)
```

## Database Schema Overview

### Core Tables
- **users**: User authentication and profiles
- **game_sessions**: Individual games/practices
- **players**: Player roster management
- **plays**: Individual plays within sessions
- **play_players**: Player involvement in plays

### Analytics Tables
- **team_stats**: Aggregated team statistics by phase
- **player_stats**: Individual player performance
- **play_call_stats**: Play call effectiveness
- **down_distance_stats**: Situational analytics
- **progressive_stats**: Game progression tracking

### Security Features
- **Row Level Security (RLS)**: Users can only access their own data
- **Authentication**: Secure user management
- **Data Isolation**: Multi-tenant architecture

## Key Benefits

### 🛡️ Data Persistence
- **No more data loss** during deployments
- **Automatic backups** with Supabase
- **Point-in-time recovery** available

### 📊 Enhanced Analytics
- **Real-time queries** for live statistics
- **Complex aggregations** for advanced metrics
- **Historical data analysis** across seasons

### 🚀 Scalability
- **Handles thousands of plays** efficiently
- **Multi-user support** with data isolation
- **API-first architecture** for future mobile apps

### 🔒 Security
- **Encrypted data** at rest and in transit
- **User authentication** built-in
- **Role-based access** control

## Migration Strategy

### Phase 1: Parallel Operation
- Keep existing file system as backup
- Write to both systems during transition
- Validate data consistency

### Phase 2: Primary Switch
- Use Supabase as primary data store
- File system becomes backup only
- Monitor performance and reliability

### Phase 3: Full Migration
- Remove file-based storage
- Complete Supabase integration
- Optimize queries and performance

## Troubleshooting

### Connection Issues
```python
# Check environment variables
import os
print("SUPABASE_URL:", os.getenv('SUPABASE_URL'))
print("SUPABASE_ANON_KEY:", os.getenv('SUPABASE_ANON_KEY')[:20] + "...")
```

### RLS Policies
If you get permission errors, check that RLS policies are properly configured in the Supabase dashboard.

### Performance
- Use indexes for frequently queried columns
- Batch operations when possible
- Monitor query performance in Supabase dashboard

## Support

- **Supabase Docs**: [docs.supabase.com](https://docs.supabase.com)
- **Community**: [github.com/supabase/supabase](https://github.com/supabase/supabase)
- **Dashboard**: Your project dashboard for monitoring and management

## Next Steps

1. Set up Supabase project
2. Run the schema migration
3. Update environment variables
4. Test the connection
5. Begin data migration
6. Deploy with enhanced reliability

This setup will eliminate data loss issues and provide a robust foundation for your sports analytics platform.
