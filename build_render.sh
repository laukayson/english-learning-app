#!/bin/bash
# Build script for Render deployment

echo "🚀 Starting Render build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements_render.txt

# Verify critical dependencies
echo "🔍 Verifying dependencies..."
python -c "import flask; print('✅ Flask installed')"
python -c "import libsql_client; print('✅ Turso client installed')" || echo "⚠️ Turso client not found - will use SQLite fallback"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/db
mkdir -p data/logs
mkdir -p data/cache

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 backend/app_render.py

# Run database initialization (will create tables)
echo "🗄️ Initializing database..."
cd backend
python -c "
from turso_service import get_db_service
db = get_db_service()
print('✅ Database service initialized')
print(f'Database type: {\"Turso\" if db.is_turso else \"SQLite\"}')
"

echo "✅ Build process completed successfully!"
echo "🌐 Application ready for deployment"
