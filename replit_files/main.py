#!/usr/bin/env python3
"""
Replit entry point for English Learning App
Simply imports and runs your existing Flask app
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Import your existing app (renamed from app_pythonanywhere.py to app.py)
from app import app

if __name__ == "__main__":
    # Replit configuration
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    
    print(f"🚀 Starting English Learning App on Replit")
    print(f"🌍 Access at: {host}:{port}")
    
    app.run(host=host, port=port, debug=True)
