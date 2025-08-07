# Render Deployment Cleanup Script
# This script removes PythonAnywhere-specific files and prepares for Render deployment

import os
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_for_render():
    """Remove PythonAnywhere-specific files and directories"""
    
    files_to_remove = [
        # PythonAnywhere specific files
        'requirements_pythonanywhere.txt',
        'pythonanywhere_integration.py',
        'pythonanywhere_wsgi_config_template.py',
        'cleanup_pythonanywhere.py',
        'PYTHONANYWHERE_DEPLOYMENT.md',
        'PYTHONANYWHERE_LOCAL_FIXES.md',
        
        # Backend PythonAnywhere files
        'backend/app_pythonanywhere.py',
        'backend/config_pythonanywhere.py',
        
        # Frontend PythonAnywhere files
        'frontend/js/config_pythonanywhere.js',
        
        # Development and debugging files
        'debug_service_startup.py',
        'test_backend_startup.py',
        'test_registration_debug.html',
        'test_level_update.html',
        'test_progress_tracker.py',
        'test_service_initialization.py',
        'test_services_quick.py',
        
        # Documentation that's no longer relevant
        'SERVICE_FIXES_COMPLETE.md',
        'REGISTRATION_DEBUG_GUIDE.md',
        'REGISTRATION_TROUBLESHOOTING.md',
        'QUICK_START.md',
        'UPLOAD_CHECKLIST.md',
        
        # Selenium service (not supported on Render free tier)
        'render_selenium_client.py',
        
        # Old WSGI config
        'wsgi.py'
    ]
    
    directories_to_remove = [
        # Selenium service directory (browser automation not supported on Render free)
        'render_selenium_service',
        
        # Replit specific files
        'replit_files'
    ]
    
    # Remove files
    for file_path in files_to_remove:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"✅ Removed file: {file_path}")
            else:
                logger.info(f"⚠️ File not found (already removed?): {file_path}")
        except Exception as e:
            logger.error(f"❌ Error removing file {file_path}: {e}")
    
    # Remove directories
    for dir_path in directories_to_remove:
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                logger.info(f"✅ Removed directory: {dir_path}")
            else:
                logger.info(f"⚠️ Directory not found (already removed?): {dir_path}")
        except Exception as e:
            logger.error(f"❌ Error removing directory {dir_path}: {e}")
    
    logger.info("🧹 Cleanup completed!")

def update_main_app():
    """Update main app.py to point to render version"""
    
    try:
        # Create a symbolic link or copy the render app
        if os.path.exists('backend/app_render.py'):
            if os.path.exists('app.py'):
                os.remove('app.py')
            
            # Create a simple app.py that imports the render version
            with open('app.py', 'w') as f:
                f.write("""# Main application entry point for Render
# This imports and runs the Render-optimized version

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import and run the Render app
from app_render import app

if __name__ == '__main__':
    # Get port from environment (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
""")
            
            logger.info("✅ Created main app.py entry point for Render")
    
    except Exception as e:
        logger.error(f"❌ Error updating main app: {e}")

def create_render_specific_files():
    """Create additional files needed for Render"""
    
    try:
        # Create .gitignore for Render (if not exists)
        gitignore_content = """# Render specific
.env
*.log

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# Database
*.db
*.sqlite
*.sqlite3

# Local development
data/db/
data/logs/
data/cache/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
        
        if not os.path.exists('.gitignore'):
            with open('.gitignore', 'w') as f:
                f.write(gitignore_content)
            logger.info("✅ Created .gitignore for Render")
        
        # Create runtime.txt for Python version (if needed)
        runtime_content = "python-3.11.0\n"
        
        with open('runtime.txt', 'w') as f:
            f.write(runtime_content)
        logger.info("✅ Created runtime.txt for Python version")
        
    except Exception as e:
        logger.error(f"❌ Error creating Render files: {e}")

def main():
    """Main cleanup function"""
    print("🧹 Cleaning up for Render deployment...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('backend') or not os.path.exists('frontend'):
        print("❌ Error: This script must be run from the project root directory")
        return
    
    # Ask for confirmation
    response = input("This will remove PythonAnywhere-specific files. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cleanup cancelled")
        return
    
    # Perform cleanup
    cleanup_for_render()
    update_main_app()
    create_render_specific_files()
    
    print("\n🎉 Cleanup completed successfully!")
    print("\nNext steps:")
    print("1. Review the changes")
    print("2. Test locally with: python app.py")
    print("3. Commit changes to GitHub")
    print("4. Deploy to Render")
    print("\nFiles ready for Render deployment! 🚀")

if __name__ == "__main__":
    main()
