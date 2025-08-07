#!/usr/bin/env python3
"""
WSGI configuration for PythonAnywhere deployment
"""

import sys
import os

# Add your project directory to the Python path
path = '/home/laukayson/englishlearningapp'  # Updated for your PythonAnywhere setup
if path not in sys.path:
    sys.path.insert(0, path)

# Add the backend directory to the path
backend_path = '/home/laukayson/englishlearningapp/backend'  # Updated for your PythonAnywhere setup
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Set environment variables for production
os.environ['DEBUG'] = 'False'
os.environ['FLASK_ENV'] = 'production'

# Import your Flask application (use PythonAnywhere-specific version)
from backend.app_pythonanywhere import app as application

if __name__ == "__main__":
    application.run()
