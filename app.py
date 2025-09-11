from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import hashlib
import uuid
import altair as alt
from functools import wraps
import pickle
from datetime import datetime
import hashlib
import io
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Import database manager with error handling
try:
    from database import db_manager
    print("✅ Database manager loaded successfully")
except ImportError as e:
    print(f"❌ Database import failed: {e}")
    db_manager = None

try:
    from data_backup_system import backup_system, backup_all_user_data
except ImportError:
    print("Warning: data_backup_system not available, using fallback")
    backup_system = None
    backup_all_user_data = lambda *args, **kwargs: []

# Import Supabase manager
try:
    from supabase_config import supabase_manager
    print("✅ Supabase manager loaded successfully")
except ImportError as e:
    print(f"Warning: Supabase not available ({e}), using fallback")
    supabase_manager = None
except Exception as e:
    print(f"Warning: Supabase initialization failed ({e}), using fallback")
    supabase_manager = None

# Configure Altair to use inline data for web serving
alt.data_transformers.disable_max_rows()
alt.data_transformers.enable('default')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'hoy-sports-data-secret-key-2025')

# Authentication helper functions
def hash_password(password):
    """Hash password with salt"""
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

def check_password(hashed_password, user_password):
    """Check if password matches hash"""
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()

def require_login(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Health check endpoints
@app.route('/health')
def health_check():
    """Ultra-simple health check for Railway deployment"""
    return "OK", 200

@app.route('/health/detailed')
def detailed_health_check():
    """Detailed health check with all system status"""
    try:
        response_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'app': 'running'
        }
        
        # Try Supabase connection
        try:
            if supabase_manager and supabase_manager.is_connected():
                supabase_connected = supabase_manager.test_connection()
                response_data['supabase'] = 'connected' if supabase_connected else 'disconnected'
            else:
                response_data['supabase'] = 'not_available'
        except Exception as supabase_e:
            response_data['supabase'] = 'error'
            response_data['supabase_error'] = str(supabase_e)
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            'status': 'basic_healthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'message': 'App is running despite errors'
        }), 200

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login.html', error="Username and password required")
        
        if not supabase_manager:
            return render_template('login.html', error="Database not available")
        
        try:
            result = supabase_manager.supabase.table('users').select('*').eq('username', username).execute()
            
            if result.data and len(result.data) > 0:
                user = result.data[0]
                if check_password(user['password_hash'], password):
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['is_admin'] = user.get('is_admin', False)
                    return redirect(url_for('index'))
                else:
                    return render_template('login.html', error="Invalid credentials")
            else:
                return render_template('login.html', error="Invalid credentials")
                
        except Exception as e:
            return render_template('login.html', error=f"Login error: {str(e)}")
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if not username or not password:
            return render_template('signup.html', error="Username and password required")
        
        if not supabase_manager:
            return render_template('signup.html', error="Database not available")
        
        try:
            result = supabase_manager.supabase.table('users').select('username').eq('username', username).execute()
            
            if result.data and len(result.data) > 0:
                return render_template('signup.html', error="Username already exists")
            
            user_data = {
                'username': username,
                'password_hash': hash_password(password),
                'email': email,
                'is_admin': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = supabase_manager.supabase.table('users').insert(user_data).execute()
            
            if result.data:
                user = result.data[0]
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = user.get('is_admin', False)
                return redirect(url_for('index'))
            else:
                return render_template('signup.html', error="Failed to create account")
                
        except Exception as e:
            return render_template('signup.html', error=f"Signup error: {str(e)}")
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/')
def index():
    """Main dashboard - show login/signup if not authenticated, otherwise show app"""
    if 'user_id' not in session:
        return """
        <h1>Hoy Sports Data</h1>
        <p>Professional Football Analytics Platform</p>
        <p><a href="/login">Login</a> | <a href="/signup">Sign Up</a></p>
        <p><a href="/health">Health Check</a></p>
        """
    
    # User is logged in, show main dashboard
    return f"""
    <h1>Welcome to Hoy Sports Data, {session.get('username', 'User')}!</h1>
    <p>Your professional football analytics platform is ready.</p>
    <ul>
        <li><a href="/dashboard">Dashboard</a></li>
        <li><a href="/games">Game Management</a></li>
        <li><a href="/players">Player Management</a></li>
        <li><a href="/analytics">Analytics</a></li>
        <li><a href="/logout">Logout</a></li>
    </ul>
    """

@app.route('/dashboard')
@require_login
def dashboard():
    """Main user dashboard"""
    return f"""
    <h1>Dashboard - {session.get('username')}</h1>
    <p>Full sports data functionality will be restored here.</p>
    <p><a href="/">Back to Home</a></p>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting Hoy Sports Data app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
