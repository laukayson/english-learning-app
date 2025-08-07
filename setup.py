# Setup script for Language Learning App

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_python_dependencies():
    """Install Python dependencies"""
    try:
        print("📦 Installing Python dependencies...")
        
        # Core dependencies that should work on any system
        core_packages = [
            "flask==2.3.3",
            "flask-cors==4.0.0", 
            "requests==2.31.0",
            "python-dotenv==1.0.0",
            "Pillow==10.0.1"
        ]
        
        # Install core packages one by one
        for package in core_packages:
            try:
                print(f"   Installing {package}...")
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                              check=True, cwd="backend", capture_output=True)
            except subprocess.CalledProcessError as e:
                print(f"   ⚠️ Failed to install {package}, trying without version...")
                package_name = package.split("==")[0]
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                                  check=True, cwd="backend", capture_output=True)
                    print(f"   ✅ Installed {package_name} (latest version)")
                except subprocess.CalledProcessError:
                    print(f"   ❌ Could not install {package_name}")
        
        print("✅ Core dependencies installation completed")
        
        # Try to install optional AI packages
        print("🤖 Attempting to install optional AI packages...")
        ai_packages = ["transformers", "torch", "numpy"]
        
        for package in ai_packages:
            try:
                # First check if already installed
                subprocess.run([sys.executable, "-c", f"import {package}"], 
                              check=True, capture_output=True)
                print(f"   ✅ {package} already installed")
            except subprocess.CalledProcessError:
                # Not installed, try to install
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                  check=True, capture_output=True, timeout=120)
                    print(f"   ✅ Installed {package}")
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    print(f"   ⚠️ Could not install {package} (AI features may be limited)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during dependency installation: {e}")
        print("💡 Try running: pip install flask flask-cors requests python-dotenv")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        "data",
        "data/db",
        "data/logs",
        "data/cache",
        "backend/cache",
        "backend/cache/images",
        "backend/logs",
        "tests",
        "scripts"
    ]
    
    try:
        print("📁 Creating directories...")
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"   Created: {directory}")
        print("✅ Directories created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create directories: {e}")
        return False

def initialise_database():
    """Initialise SQLite database"""
    try:
        print("🗄️ Initialising database...")
        db_path = "data/db/language_app.db"
        
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialise database with basic tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                level INTEGER DEFAULT 1,
                native_language TEXT DEFAULT 'farsi',
                created_at TEXT NOT NULL,
                last_login TEXT,
                preferences TEXT DEFAULT '{}'
            )
        ''')
        
        # Basic configuration table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Insert default configuration
        default_config = [
            ('app_version', '1.0.0'),
            ('db_version', '1.0'),
            ('setup_completed', 'true'),
            ('rate_limit_enabled', 'true'),
            ('ai_services_enabled', 'true')
        ]
        
        for key, value in default_config:
            cursor.execute('''
                INSERT OR IGNORE INTO app_config (key, value, updated_at) 
                VALUES (?, ?, datetime('now'))
            ''', (key, value))
        
        conn.commit()
        conn.close()
        
        print("✅ Database initialised successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database initialisation failed: {e}")
        return False

def create_config_files():
    """Create configuration files"""
    print("⚙️ Creating configuration files...")
    
    # Environment configuration
    env_config = """# Language Learning App Configuration
# Copy this file to .env and update values as needed

# Application Settings
APP_NAME=Language Learning App
APP_VERSION=1.0.0
DEBUG=False
HOST=localhost
FRONTEND_PORT=8000
BACKEND_PORT=5000

# Database
DATABASE_PATH=data/db/language_app.db

# AI Services (Free Tier)
HUGGINGFACE_TOKEN=your_huggingface_token_here
HUGGINGFACE_MODEL_CONVERSATION=microsoft/DialoGPT-medium
HUGGINGFACE_MODEL_TRANSLATION=Helsinki-NLP/opus-mt-en-fa
HUGGINGFACE_MODEL_IMAGE=runwayml/stable-diffusion-v1-5

# Rate Limiting
RATE_LIMIT_ENABLED=true
REQUESTS_PER_MINUTE=60
DAILY_REQUEST_LIMIT=1000

# Voice Settings
VOICE_ENABLED=true
SPEECH_LANGUAGE=en-US
PRONUNCIATION_THRESHOLD=60

# Cache Settings
CACHE_ENABLED=true
CACHE_DURATION_HOURS=24
IMAGE_CACHE_SIZE_MB=100

# Logging
LOG_LEVEL=INFO
LOG_FILE=data/logs/app.log
LOG_MAX_SIZE_MB=10
LOG_BACKUP_COUNT=5

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
"""
    
    with open(".env.example", "w", encoding="utf-8") as f:
        f.write(env_config)
    
    print("   Created: .env.example")
    
    # Create actual .env if it doesn't exist
    if not os.path.exists(".env"):
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_config.replace("your_huggingface_token_here", "")
                             .replace("your-secret-key-here", "development-key-change-in-production"))
        print("   Created: .env")
    
    print("✅ Configuration files created")
    return True

def create_launch_scripts():
    """Create launch scripts"""
    print("🚀 Creating launch scripts...")
    
    # Windows batch script
    windows_script = """@echo off
echo Starting Language Learning App...
echo.

echo Starting Python backend...
start /B cmd /c "cd backend && python app.py"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo Starting frontend server...
python -m http.server 8000 --directory frontend

echo.
echo App should be available at: http://localhost:8000
pause
"""
    
    with open("start.bat", "w") as f:
        f.write(windows_script)
    
    # Unix shell script
    unix_script = """#!/bin/bash
echo "Starting Language Learning App..."
echo

echo "Starting Python backend..."
cd backend && python app.py &
BACKEND_PID=$!

echo "Waiting for backend to start..."
sleep 3

echo "Starting frontend server..."
cd ..
python -m http.server 8000 --directory frontend &
FRONTEND_PID=$!

echo
echo "App should be available at: http://localhost:8000"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo
echo "Press Ctrl+C to stop both servers"

# Wait for interrupt
trap 'kill $BACKEND_PID $FRONTEND_PID; exit' INT
wait
"""
    
    with open("start.sh", "w") as f:
        f.write(unix_script)
    
    # Make shell script executable on Unix-like systems
    try:
        os.chmod("start.sh", 0o755)
    except:
        pass  # Windows doesn't support chmod
    
    print("   Created: start.bat (Windows)")
    print("   Created: start.sh (Unix/Linux/Mac)")
    print("✅ Launch scripts created")
    return True

def create_readme():
    """Create comprehensive README"""
    readme_content = """# Language Learning App for Afghan Refugees

An AI-powered English language learning application specifically designed for Afghan refugees, featuring voice recognition, Farsi translations, and gamified learning experiences.

## 🌟 Features

### Core Learning Features
- **4-Level Curriculum**: Beginner to Advanced English learning path
- **20+ Topics**: From greetings to advanced professional communication
- **AI Conversation Partner**: Practice real conversations with AI tutor
- **Voice Recognition**: Pronunciation checking and voice input
- **Farsi Integration**: All content includes Farsi translations
- **Spaced Repetition**: Scientifically-proven memory retention system

### Gamification & Progress
- **Streak Tracking**: Daily learning streaks and achievements
- **Progress Analytics**: Detailed learning statistics and insights
- **Achievement System**: Unlock badges and milestones
- **Daily Goals**: Customizable learning targets

### Accessibility & Inclusion
- **Offline Capable**: Core features work without internet
- **Mobile Responsive**: Works on phones, tablets, and computers
- **Cultural Sensitivity**: Content designed for Afghan refugee context
- **Free Forever**: No costs or subscriptions required

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Modern web browser with microphone support
- Internet connection (for AI features)

### Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd language-learning-app
   ```

2. **Run the setup script**
   ```bash
   python setup.py
   ```

3. **Start the application**
   
   **Windows:**
   ```cmd
   start.bat
   ```
   
   **Mac/Linux:**
   ```bash
   ./start.sh
   ```
   
   **Manual start:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python app.py
   
   # Terminal 2 - Frontend
   python -m http.server 8000 --directory frontend
   ```

4. **Open your browser**
   - Navigate to: `http://localhost:8000`
   - Create your profile and start learning!

## 📚 Learning Curriculum

### Level 1: Foundation (Beginner)
- Greetings & Basic Courtesy
- Family & Personal Information
- Numbers & Time
- Colours & Basic Shapes
- Daily Routines

### Level 2: Practical (Elementary)
- Food & Dining
- Shopping & Money
- Transportation & Directions
- Weather & Seasons
- Body Parts & Health

### Level 3: Social (Intermediate)
- Emotions & Feelings
- Hobbies & Free Time
- Work & Professions
- House & Home
- Technology & Communication

### Level 4: Advanced (Upper-Intermediate)
- Travel & Adventure
- Environment & Nature
- Culture & Traditions
- Health & Medical
- Advanced Grammar & Expressions

## 🛠️ Configuration

### AI Services Setup (Optional)
To enable AI features, get a free Hugging Face token:

1. Visit [huggingface.co](https://huggingface.co)
2. Create free account
3. Go to Settings → Access Tokens
4. Create new token
5. Add to `.env` file:
   ```
   HUGGINGFACE_TOKEN=your_token_here
   ```

### Voice Settings
- Microphone access required for pronunciation checking
- Works in Chrome, Firefox, Safari, Edge
- Supports multiple English accents

## 📱 Usage Guide

### Getting Started
1. **Create Profile**: Enter your name and select experience level
2. **Choose Topic**: Pick from available learning topics
3. **Practice Conversations**: Chat with AI tutor in English
4. **Use Voice Features**: Practice pronunciation with feedback
5. **Track Progress**: Monitor your learning journey

### Conversation Practice
- Type messages or use voice input
- AI responds with helpful corrections
- Farsi translations provided for all content
- Pronunciation scoring for voice input

### Spaced Repetition
- System automatically schedules review sessions
- Practice previously learned phrases at optimal intervals
- Improves long-term memory retention

## 🔧 Technical Details

### Architecture
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python Flask with SQLite database
- **AI Services**: Hugging Face Transformers (free tier)
- **Voice**: Web Speech API
- **Storage**: Local storage + server database

### Browser Compatibility
- Chrome 60+ (recommended)
- Firefox 55+
- Safari 11+
- Edge 79+

### Performance
- Lightweight design for low-end devices
- Offline functionality for core features
- Optimised for mobile data usage

## 🤝 Contributing

This is an open-source project designed to help Afghan refugees learn English. Contributions are welcome!

### Areas for Contribution
- Additional language translations
- More conversation topics
- Improved AI responses
- Better pronunciation checking
- Cultural content adaptation
- Accessibility improvements

### Development Setup
1. Follow installation steps above
2. Enable debug mode in `.env`: `DEBUG=True`
3. Backend auto-reloads on file changes
4. Frontend served from `/frontend` directory

## 📄 License

MIT License - This project is free to use, modify, and distribute.

## 🙏 Acknowledgments

- **Greater Action**: Nonprofit organisation supporting Afghan refugees
- **Hugging Face**: Free AI model hosting
- **Web Speech API**: Browser-based voice recognition
- **Afghan Community**: Input and feedback on cultural appropriateness

## 🆘 Support

### Getting Help
- Check the troubleshooting section below
- Review browser console for error messages
- Ensure microphone permissions are granted

### Common Issues

**"AI not responding"**
- Check internet connection
- Verify Hugging Face token in `.env`
- Try refreshing the page

**"Voice not working"**
- Grant microphone permissions
- Use HTTPS or localhost only
- Check browser compatibility

**"Database errors"**
- Run `python setup.py` again
- Check file permissions in `data/` directory

**"Frontend won't load"**
- Ensure Python HTTP server is running
- Check port 8000 is not in use
- Try different browser

### Contact
For bugs, suggestions, or contributions:
- Create GitHub issue
- Email: [your-contact-email]

---

**Built with ❤️ for the Afghan refugee community**

*"Language learning opens doors to new opportunities and connections. This app is our contribution to helping Afghan refugees build new lives through English proficiency."*
"""
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("   Created: README.md")
    return True

def main():
    """Main setup function"""
    print("🚀 Language Learning App Setup")
    print("=" * 50)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Creating directories", create_directories),
        ("Installing Python dependencies", install_python_dependencies),
        ("Initialising database", initialise_database),
        ("Creating configuration files", create_config_files),
        ("Creating launch scripts", create_launch_scripts),
        ("Creating documentation", create_readme)
    ]
    
    success_count = 0
    for step_name, step_function in steps:
        print(f"\n{step_name}...")
        if step_function():
            success_count += 1
        else:
            print(f"❌ Setup failed at: {step_name}")
            break
    
    print("\n" + "=" * 50)
    if success_count == len(steps):
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Configure AI services in .env file (optional)")
        print("2. Run 'start.bat' (Windows) or './start.sh' (Mac/Linux)")
        print("3. Open http://localhost:8000 in your browser")
        print("4. Create your profile and start learning!")
        
        print("\n💡 Tips:")
        print("- Grant microphone access for voice features")
        print("- Use Chrome browser for best experience")
        print("- Check README.md for detailed instructions")
        
    else:
        print(f"⚠️ Setup partially completed ({success_count}/{len(steps)} steps)")
        print("Please check error messages above and try again")
    
    print("\n🙏 Thank you for supporting Afghan refugee education!")

if __name__ == "__main__":
    main()
