# Deploy to Render - Quick Guide

## Your app is ready for Render deployment!

### Step 1: Go to Render
1. Visit https://render.com
2. Sign up/login (can use GitHub account)

### Step 2: Create New Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub account if not already connected
3. Select your repository: `bhoy33/hoy-sports-data`
4. Click "Connect"

### Step 3: Configure Deployment
**Basic Settings:**
- **Name:** `hoysportsdata` (or your preferred name)
- **Region:** Choose closest to your users
- **Branch:** `main`
- **Runtime:** `Python 3`

**Build & Deploy Settings:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn --config gunicorn.conf.py app:app`

**Environment Variables:**
- **PORT:** `10000` (Render default)
- Add any other environment variables your app needs

### Step 4: Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy your app
3. You'll get a URL like: `https://hoysportsdata.onrender.com`

### Step 5: Custom Domain (Optional)
1. Go to Settings → Custom Domains
2. Add `hoysportsdata.com`
3. Update your DNS records as instructed

## Why Render Works Better
- ✅ Native Python/Flask support
- ✅ Automatic dependency installation
- ✅ Uses your existing Procfile
- ✅ Better error handling
- ✅ Free tier available

## Your App Configuration
Your app is already perfectly configured with:
- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Start command for Gunicorn
- ✅ `runtime.txt` - Python version (3.10.12)
- ✅ `gunicorn.conf.py` - Gunicorn configuration
- ✅ All latest code pushed to GitHub

The deployment should work immediately!
