"""
Fresh Railway deployment app - minimal Flask setup
"""
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>Hoy Sports Data</h1>
    <p>Fresh Railway deployment successful!</p>
    <p><a href="/health">Health Check</a></p>
    """

@app.route('/health')
def health():
    return {"status": "healthy", "message": "App is running"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
