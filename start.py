#!/usr/bin/env python3
import subprocess
import sys
import os

# Try to import gunicorn, install if not available
try:
    import gunicorn
except ImportError:
    print("Installing gunicorn...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gunicorn>=21.2.0"])

# Start the application
if __name__ == "__main__":
    os.system("gunicorn --config gunicorn.conf.py app:app")
