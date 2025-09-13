#!/usr/bin/env python3
"""
Ultra-minimal Flask app for Railway deployment testing
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Railway deployment test successful!"

@app.route('/health')
def health():
    return {"status": "ok", "message": "Minimal app running"}

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
