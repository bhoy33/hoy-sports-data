#!/bin/bash
echo "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo "Starting Flask application..."
python app.py
