#!/bin/bash
# Enhanced startup script for Railway deployment with database verification

echo "=== Starting Football Box Stats Analytics ==="

# Set environment variables for better database handling
export PYTHONUNBUFFERED=1
export CLEANUP_OLD_SESSIONS=true

# Run database health check and initialization
echo "Running database health check..."
python3 database_health.py

if [ $? -ne 0 ]; then
    echo "❌ Database health check failed - attempting to continue with degraded service"
    # Don't exit - allow app to start with file fallback
fi

echo "✓ Database health check completed"

# Start the application with optimized settings for Railway
echo "Starting Gunicorn server..."
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    app:app
