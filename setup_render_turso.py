# Render + Turso Setup Automation Script
# This script automates the entire migration process

import os
import sys
import subprocess
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RenderTursoSetup:
    """Automate Render + Turso setup"""
    
    def __init__(self):
        self.project_root = os.getcwd()
        self.turso_url = None
        self.turso_token = None
        
    def welcome(self):
        """Display welcome message"""
        print("🚀 English Learning App - Render + Turso Setup")
        print("=" * 60)
        print("This script will help you migrate from PythonAnywhere to Render + Turso")
        print("Estimated time: 15-20 minutes")
        print("=" * 60)
        print()
    
    def check_dependencies(self):
        """Check for required dependencies"""
        logger.info("🔍 Checking dependencies...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            logger.error("❌ Python 3.8+ required")
            return False
        
        # Check for git
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            logger.info("✅ Git is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ Git is required for deployment")
            return False
        
        # Check for pip
        try:
            subprocess.run([sys.executable, '-m', 'pip', '--version'], capture_output=True, check=True)
            logger.info("✅ Pip is available")
        except subprocess.CalledProcessError:
            logger.error("❌ Pip is required")
            return False
        
        return True
    
    def collect_turso_credentials(self):
        """Collect Turso database credentials"""
        print("\n📋 Turso Database Setup")
        print("-" * 30)
        print("1. Sign up at https://turso.tech/ (if you haven't already)")
        print("2. Create a new database")
        print("3. Get your database URL and auth token")
        print()
        
        self.turso_url = input("Enter your Turso database URL (libsql://...): ").strip()
        if not self.turso_url.startswith('libsql://'):
            logger.error("❌ Invalid Turso URL format. Must start with 'libsql://'")
            return False
        
        self.turso_token = input("Enter your Turso auth token: ").strip()
        if not self.turso_token:
            logger.error("❌ Auth token is required")
            return False
        
        return True
    
    def install_dependencies(self):
        """Install required dependencies"""
        logger.info("📦 Installing dependencies...")
        
        try:
            # Install libsql-client for Turso
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', 
                'libsql-client', 'python-dotenv'
            ], check=True)
            logger.info("✅ Dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
    
    def migrate_database(self):
        """Migrate existing SQLite data to Turso"""
        sqlite_path = os.path.join("data", "db", "language_app.db")
        
        if not os.path.exists(sqlite_path):
            logger.info("⚠️ No existing SQLite database found - will create fresh database")
            return True
        
        print(f"\n📊 Found existing database: {sqlite_path}")
        migrate = input("Do you want to migrate existing data to Turso? (y/N): ").strip().lower()
        
        if migrate == 'y':
            logger.info("🔄 Starting database migration...")
            
            try:
                # Import and run migration
                from migrate_to_turso import DatabaseMigrator
                
                migrator = DatabaseMigrator(sqlite_path, self.turso_url, self.turso_token)
                
                if migrator.migrate_all_data():
                    if migrator.verify_migration():
                        logger.info("✅ Database migration completed successfully!")
                        return True
                    else:
                        logger.error("❌ Migration verification failed")
                        return False
                else:
                    logger.error("❌ Database migration failed")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Migration error: {e}")
                return False
        else:
            logger.info("⚠️ Skipping database migration - fresh database will be created")
            return True
    
    def create_env_file(self):
        """Create .env file for local testing"""
        logger.info("📝 Creating .env file for local testing...")
        
        env_content = f"""# Environment variables for Render deployment
TURSO_DATABASE_URL={self.turso_url}
TURSO_AUTH_TOKEN={self.turso_token}
FLASK_ENV=development
PORT=5000
RENDER=false
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        logger.info("✅ Created .env file")
        
        # Add .env to .gitignore if not already there
        gitignore_path = '.gitignore'
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                content = f.read()
            
            if '.env' not in content:
                with open(gitignore_path, 'a') as f:
                    f.write('\n# Environment variables\n.env\n')
                logger.info("✅ Added .env to .gitignore")
    
    def test_local_setup(self):
        """Test the local setup"""
        logger.info("🧪 Testing local setup...")
        
        try:
            # Test database connection
            from backend.turso_service import TursoService
            
            db = TursoService(self.turso_url, self.turso_token)
            health = db.health_check()
            
            if health['status'] == 'healthy':
                logger.info(f"✅ Database connection successful ({health['database_type']})")
                return True
            else:
                logger.error(f"❌ Database connection failed: {health}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Local test failed: {e}")
            return False
    
    def cleanup_files(self):
        """Clean up PythonAnywhere-specific files"""
        logger.info("🧹 Cleaning up old files...")
        
        try:
            from cleanup_for_render import cleanup_for_render, update_main_app, create_render_specific_files
            
            cleanup_for_render()
            update_main_app()
            create_render_specific_files()
            
            logger.info("✅ Cleanup completed")
            return True
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return False
    
    def generate_deployment_instructions(self):
        """Generate personalized deployment instructions"""
        logger.info("📋 Generating deployment instructions...")
        
        instructions = f"""# Your Render Deployment Instructions
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🚀 Deploy to Render

### 1. Push to GitHub
```bash
git add .
git commit -m "Migrate to Render + Turso"
git push origin main
```

### 2. Create Render Web Service
1. Go to https://render.com/
2. Sign up and connect your GitHub account
3. Click "New +" → "Web Service"
4. Select your repository
5. Use these settings:

**Basic Settings:**
- Name: english-learning-app
- Environment: Python
- Region: Oregon (US West)
- Branch: main

**Build & Deploy:**
- Build Command: `pip install -r requirements_render.txt`
- Start Command: `python app.py`

### 3. Environment Variables
Add these in the Render dashboard:

```
TURSO_DATABASE_URL={self.turso_url}
TURSO_AUTH_TOKEN={self.turso_token}
FLASK_ENV=production
PORT=10000
RENDER=true
```

### 4. Test Your Deployment
After deployment, test these URLs:
- Health check: https://your-app-name.onrender.com/health
- Main app: https://your-app-name.onrender.com/

## 🔧 Local Development
To run locally:
```bash
python app.py
# Visit http://localhost:5000
```

## 📊 Features Available
✅ Text-based AI chat
✅ User registration/login
✅ Progress tracking
✅ Translation
✅ Topic-based learning

❌ Voice features (disabled on Render)
❌ Browser automation (disabled on Render)

## 💡 Tips
- Render free tier sleeps after 15 minutes of inactivity
- First request after sleep may be slow (cold start)
- Monitor usage in Render dashboard
- Upgrade to paid plan for always-on service

## 🆘 Need Help?
- Render docs: https://render.com/docs
- Turso docs: https://docs.turso.tech/
- Project issues: Create GitHub issue
"""
        
        with open('RENDER_DEPLOYMENT_INSTRUCTIONS.md', 'w') as f:
            f.write(instructions)
        
        logger.info("✅ Created personalized deployment instructions")
    
    def run_setup(self):
        """Run the complete setup process"""
        self.welcome()
        
        # Step 1: Check dependencies
        if not self.check_dependencies():
            return False
        
        # Step 2: Collect credentials
        if not self.collect_turso_credentials():
            return False
        
        # Step 3: Install dependencies
        if not self.install_dependencies():
            return False
        
        # Step 4: Migrate database
        if not self.migrate_database():
            return False
        
        # Step 5: Create environment file
        self.create_env_file()
        
        # Step 6: Test setup
        if not self.test_local_setup():
            return False
        
        # Step 7: Clean up files
        if not self.cleanup_files():
            return False
        
        # Step 8: Generate instructions
        self.generate_deployment_instructions()
        
        return True
    
    def show_completion_message(self):
        """Show completion message"""
        print("\n🎉 Setup completed successfully!")
        print("=" * 60)
        print("✅ Dependencies installed")
        print("✅ Database configured")
        print("✅ Files cleaned up")
        print("✅ Local testing passed")
        print("✅ Deployment instructions generated")
        print()
        print("📋 Next Steps:")
        print("1. Review RENDER_DEPLOYMENT_INSTRUCTIONS.md")
        print("2. Test locally: python app.py")
        print("3. Commit and push to GitHub")
        print("4. Deploy to Render")
        print()
        print("🌐 Your app will be available at:")
        print("   https://your-app-name.onrender.com")
        print("=" * 60)

def main():
    """Main setup function"""
    setup = RenderTursoSetup()
    
    try:
        if setup.run_setup():
            setup.show_completion_message()
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
