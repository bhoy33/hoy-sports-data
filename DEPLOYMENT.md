# Simple Deployment Guide for Hoy Sports Data

## Local Testing (Currently Running)
Your Flask app is running at: http://127.0.0.1:5004
Test it locally first to make sure everything works.

## Deploy to Railway (Simplest Option)

1. Go to [railway.app](https://railway.app)
2. Sign up/login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select this repository
5. Railway will automatically:
   - Detect it's a Python Flask app
   - Install dependencies from requirements.txt
   - Use the Procfile to start the app
   - Provide a public URL

## Files Already Created:
- ✅ `Procfile` - Tells Railway how to start your app
- ✅ `railway.json` - Railway configuration
- ✅ `requirements.txt` - Python dependencies

## Custom Domain:
After deployment, you can add hoysportsdata.com as a custom domain in Railway's dashboard.

## Alternative: Render
If Railway doesn't work, try [render.com](https://render.com) - similar process, also Flask-friendly.
