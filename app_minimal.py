from flask import Flask, jsonify, request, session, redirect, url_for, render_template_string
import os
import hashlib
import uuid
from datetime import datetime

# Import Supabase with error handling
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Supabase not available ({e})")
    SUPABASE_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'hoy-sports-data-secret-key-2025')

# Initialize Supabase
supabase_client = None
if SUPABASE_AVAILABLE:
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if supabase_url and supabase_key:
        try:
            supabase_client = create_client(supabase_url, supabase_key)
            print("✅ Supabase client initialized successfully")
        except Exception as e:
            print(f"❌ Supabase initialization failed: {e}")
    else:
        print("⚠️ Supabase credentials not found in environment")

# Helper functions
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
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return f"Welcome to Hoy Sports Data, {session.get('username', 'User')}! <a href='/logout'>Logout</a>"
    return "Hoy Sports Data - <a href='/login'>Login</a> | <a href='/signup'>Sign Up</a>"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/health/detailed')
def health_detailed():
    status = {
        'app': 'running',
        'supabase_available': SUPABASE_AVAILABLE,
        'supabase_client': 'connected' if supabase_client else 'not_connected'
    }
    
    # Test Supabase connection
    if supabase_client:
        try:
            # Simple test query - just check if table exists
            result = supabase_client.table('users').select('id').limit(1).execute()
            status['supabase_test'] = 'success'
        except Exception as e:
            status['supabase_test'] = f'error: {str(e)}'
    
    return jsonify(status)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template_string(LOGIN_TEMPLATE, error="Username and password required")
        
        if not supabase_client:
            return render_template_string(LOGIN_TEMPLATE, error="Database not available")
        
        try:
            # Check user credentials
            result = supabase_client.table('users').select('*').eq('username', username).execute()
            
            if result.data and len(result.data) > 0:
                user = result.data[0]
                if check_password(user['password_hash'], password):
                    # Login successful
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['is_admin'] = user.get('is_admin', False)
                    return redirect(url_for('dashboard'))
                else:
                    return render_template_string(LOGIN_TEMPLATE, error="Invalid credentials")
            else:
                return render_template_string(LOGIN_TEMPLATE, error="Invalid credentials")
                
        except Exception as e:
            return render_template_string(LOGIN_TEMPLATE, error=f"Login error: {str(e)}")
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if not username or not password:
            return render_template_string(SIGNUP_TEMPLATE, error="Username and password required")
        
        if not supabase_client:
            return render_template_string(SIGNUP_TEMPLATE, error="Database not available")
        
        try:
            # Check if username exists
            result = supabase_client.table('users').select('username').eq('username', username).execute()
            
            if result.data and len(result.data) > 0:
                return render_template_string(SIGNUP_TEMPLATE, error="Username already exists")
            
            # Create new user
            user_data = {
                'username': username,
                'password_hash': hash_password(password),
                'email': email,
                'is_admin': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = supabase_client.table('users').insert(user_data).execute()
            
            if result.data:
                # Auto-login after signup
                user = result.data[0]
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = user.get('is_admin', False)
                return redirect(url_for('dashboard'))
            else:
                return render_template_string(SIGNUP_TEMPLATE, error="Failed to create account")
                
        except Exception as e:
            return render_template_string(SIGNUP_TEMPLATE, error=f"Signup error: {str(e)}")
    
    return render_template_string(SIGNUP_TEMPLATE)

@app.route('/dashboard')
@require_login
def dashboard():
    username = session.get('username', 'User')
    is_admin = session.get('is_admin', False)
    
    return render_template_string(DASHBOARD_TEMPLATE, username=username, is_admin=is_admin)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# HTML Templates
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login - Hoy Sports Data</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input[type="text"], input[type="password"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .error { color: red; margin-bottom: 15px; }
        .links { margin-top: 15px; }
    </style>
</head>
<body>
    <h2>Login to Hoy Sports Data</h2>
    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}
    <form method="POST">
        <div class="form-group">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required>
        </div>
        <div class="form-group">
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required>
        </div>
        <button type="submit">Login</button>
    </form>
    <div class="links">
        <a href="/signup">Don't have an account? Sign up</a> | 
        <a href="/">Back to Home</a>
    </div>
</body>
</html>
'''

SIGNUP_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Sign Up - Hoy Sports Data</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input[type="text"], input[type="password"], input[type="email"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #1e7e34; }
        .error { color: red; margin-bottom: 15px; }
        .links { margin-top: 15px; }
    </style>
</head>
<body>
    <h2>Sign Up for Hoy Sports Data</h2>
    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}
    <form method="POST">
        <div class="form-group">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required>
        </div>
        <div class="form-group">
            <label for="email">Email (optional):</label>
            <input type="email" id="email" name="email">
        </div>
        <div class="form-group">
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required>
        </div>
        <button type="submit">Sign Up</button>
    </form>
    <div class="links">
        <a href="/login">Already have an account? Login</a> | 
        <a href="/">Back to Home</a>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Hoy Sports Data</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .card { background: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 8px; border: 1px solid #dee2e6; }
        .btn { background: #007bff; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-right: 10px; }
        .btn:hover { background: #0056b3; }
        .admin-badge { background: #dc3545; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Welcome, {{ username }}!</h1>
        <div>
            {% if is_admin %}
                <span class="admin-badge">ADMIN</span>
            {% endif %}
            <a href="/logout" class="btn">Logout</a>
        </div>
    </div>
    
    <div class="card">
        <h3>🏈 Sports Data Management</h3>
        <p>Your sports data platform is ready! Features coming soon:</p>
        <ul>
            <li>Game session management</li>
            <li>Player roster tracking</li>
            <li>Play-by-play data entry</li>
            <li>Defensive analytics & NEE calculations</li>
            <li>Statistical reports and charts</li>
        </ul>
    </div>
    
    <div class="card">
        <h3>🔧 System Status</h3>
        <p>✅ Supabase database connected</p>
        <p>✅ User authentication working</p>
        <p>✅ Railway deployment stable</p>
        <a href="/health/detailed" class="btn">View Detailed Status</a>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
