# Fresh Railway Project Setup Instructions

## Files for New Railway Project

### Core Application
- `app_fresh.py` - Clean Flask app with health endpoint
- `requirements_fresh.txt` - Minimal dependencies (Flask + gunicorn)
- `Procfile_fresh` - Process definition for Railway
- `railway_fresh.toml` - Railway configuration (optional)

## Setup Steps

### 1. Create New Railway Project
1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Select your `hoy-sports-data` repository

### 2. Configure Deployment Files
**Option A: Rename files in repository**
```bash
mv app_fresh.py app.py
mv requirements_fresh.txt requirements.txt
mv Procfile_fresh Procfile
mv railway_fresh.toml railway.toml  # optional
```

**Option B: Create new branch for fresh deployment**
```bash
git checkout -b railway-fresh
mv app_fresh.py app.py
mv requirements_fresh.txt requirements.txt
mv Procfile_fresh Procfile
git add .
git commit -m "Fresh Railway deployment setup"
git push -u origin railway-fresh
```

### 3. Railway Environment Variables
Set these in Railway dashboard:
- `PORT` - Automatically set by Railway
- `FLASK_ENV` - Set to "production"

### 4. Custom Domain (if needed)
- In Railway project settings, add custom domain: `hoysportsdata.com`
- Update DNS records to point to Railway

## Testing Locally
```bash
# Test the fresh app locally first
PORT=8080 python app_fresh.py
# Should show "Fresh Railway deployment successful!" at localhost:8080
```

## Expected Behavior
- `/` - Shows success message with link to health check
- `/health` - Returns JSON health status
- Should deploy without 502 errors

## Troubleshooting
If still getting 502 errors:
1. Check Railway deployment logs in dashboard
2. Verify PORT environment variable is set
3. Ensure gunicorn is binding to 0.0.0.0:$PORT
4. Check Railway service status and restart if needed
