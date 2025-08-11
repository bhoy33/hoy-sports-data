# Hoy Sports Data - Deployment Guide

## Current Status
- ✅ Flask app is fully functional locally
- ✅ All features implemented (admin dashboard, analytics menu, play comparison, data preview)
- ✅ Code committed to local Git repository
- ✅ Deployment configuration files ready (Procfile, gunicorn.conf.py, requirements.txt)
- ❌ Need to push to GitHub and deploy to production

## Deployment Options

### Option 1: Render.com (Recommended for Flask)
1. **Create GitHub Repository**
   - Go to https://github.com/new
   - Repository name: `hoy-sports-data`
   - Make it public
   - Don't initialize with README (we have existing code)

2. **Push Code to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/hoy-sports-data.git
   git branch -M main
   git push -u origin main
   ```

3. **Deploy on Render**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Settings:
     - Name: `hoy-sports-data`
     - Environment: `Python 3`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn --config gunicorn.conf.py app:app`
     - Custom Domain: `hoysportsdata.com`

### Option 2: Railway.app (Alternative)
1. **Create GitHub Repository** (same as above)
2. **Deploy on Railway**
   - Go to https://railway.app
   - Click "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect Python/Flask
   - Add custom domain: `hoysportsdata.com`

### Option 3: Heroku (Classic Option)
1. **Create GitHub Repository** (same as above)
2. **Deploy on Heroku**
   - Go to https://heroku.com
   - Create new app: `hoy-sports-data`
   - Connect to GitHub repository
   - Enable automatic deploys
   - Add custom domain: `hoysportsdata.com`

## Environment Variables Needed
- `PORT` (automatically set by most platforms)
- `FLASK_ENV=production`
- `SECRET_KEY=hoysportsdata_secret_key_2025`

## Files Ready for Deployment
- ✅ `app.py` - Main Flask application
- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Process configuration
- ✅ `gunicorn.conf.py` - Production server configuration
- ✅ `railway.json` - Railway-specific configuration
- ✅ `netlify.toml` - Netlify configuration (if needed)
- ✅ All templates and static files

## Post-Deployment Steps
1. Test the deployed app
2. Configure custom domain (hoysportsdata.com)
3. Set up SSL certificate (usually automatic)
4. Test admin functionality
5. Test maintenance mode
6. Verify all analytics features work

## Troubleshooting
- If deployment fails, check the build logs
- Ensure all dependencies are in requirements.txt
- Verify PORT environment variable is used correctly
- Check that uploads directory is created properly

## Current App Features
- 🔐 Password protection (regular: `scots25`, admin: `Jackets21!`)
- 📊 Analytics selection menu
- ⚙️ Admin dashboard with maintenance mode
- 📈 Offensive Self Scout Analysis (fully functional)
- 📋 Data preview with scrolling
- 🔍 Play comparison (1-10 plays)
- 📱 Responsive design
- 🛡️ Error handling and validation

## Next Steps
1. Create GitHub repository manually
2. Push code to GitHub
3. Deploy using Render.com (recommended)
4. Configure hoysportsdata.com domain
5. Test production deployment
