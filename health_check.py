#!/usr/bin/env python3
"""
Simple health check app to test Railway connectivity
"""
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'message': 'Railway app is responding',
        'port': os.environ.get('PORT', 'not set'),
        'env_check': {
            'SUPABASE_URL': 'set' if os.environ.get('SUPABASE_URL') else 'missing',
            'SUPABASE_ANON_KEY': 'set' if os.environ.get('SUPABASE_ANON_KEY') else 'missing',
            'SECRET_KEY': 'set' if os.environ.get('SECRET_KEY') else 'missing'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': '2025-09-13T16:11:18'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
