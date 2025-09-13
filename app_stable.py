
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'hoysportsdata_secret_key_2025'

# Simple password authentication without Supabase
SITE_PASSWORDS = ['scots25', 'hunt25', 'cobble25', 'eagleton25']
ADMIN_PASSWORD = 'Jackets21!'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if session.get('authenticated'):
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password in SITE_PASSWORDS or password == ADMIN_PASSWORD:
            session['authenticated'] = True
            session['is_admin'] = (password == ADMIN_PASSWORD)
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/analytics/box-stats')
@login_required
def box_stats():
    return render_template('box_stats.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
