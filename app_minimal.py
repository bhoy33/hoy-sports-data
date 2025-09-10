from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Hoy Sports Data - Minimal Version"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/login')
def login():
    return "Login page - coming soon"

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
