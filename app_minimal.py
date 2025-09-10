from flask import Flask, jsonify
import os

# Import Supabase with error handling
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Supabase not available ({e})")
    SUPABASE_AVAILABLE = False

app = Flask(__name__)

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

@app.route('/')
def home():
    return "Hoy Sports Data - Minimal Version with Supabase"

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
            # Simple test query
            result = supabase_client.table('users').select('count').execute()
            status['supabase_test'] = 'success'
        except Exception as e:
            status['supabase_test'] = f'error: {str(e)}'
    
    return jsonify(status)

@app.route('/login')
def login():
    return "Login page - coming soon"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
