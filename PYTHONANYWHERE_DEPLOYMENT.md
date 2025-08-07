# PythonAnywhere Deployment Guide
# English Learning App - laukayson.pythonanywhere.com

## 📋 Pre-Upload Checklist

✅ **Cleaned for Production:**
- ❌ Removed all test files (test_*.py, debug_*.py)
- ❌ Removed development scripts (*.bat files, startup_config.py)
- ❌ Removed documentation files (*.md files except README.md)
- ❌ Removed temporary configuration files (.env, .browser_config)
- ✅ Kept production configuration (.env.production)

✅ **PythonAnywhere Ready:**
- ✅ wsgi.py configured for laukayson.pythonanywhere.com
- ✅ app_pythonanywhere.py as main application
- ✅ Production environment defaults (headless browsers)
- ✅ Logging configured for PythonAnywhere paths

## 🚀 Upload Instructions

### 1. Upload Files to PythonAnywhere

Upload the entire `englishlearningapp` folder to:
```
/home/laukayson/englishlearningapp/
```

### 2. Set Up Virtual Environment

In PythonAnywhere bash console:
```bash
cd /home/laukayson/englishlearningapp
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements_pythonanywhere.txt
```

### 3. Configure Web App

In PythonAnywhere Web tab:
- **Source code:** `/home/laukayson/englishlearningapp`
- **Working directory:** `/home/laukayson/englishlearningapp`
- **WSGI configuration file:** `/home/laukayson/englishlearningapp/wsgi.py`
- **Static files:**
  - URL: `/static/`
  - Directory: `/home/laukayson/englishlearningapp/frontend/`

### 4. Create Required Directories

```bash
mkdir -p /home/laukayson/englishlearningapp/data/logs
mkdir -p /home/laukayson/englishlearningapp/data/db
mkdir -p /home/laukayson/englishlearningapp/data/cache
chmod 755 /home/laukayson/englishlearningapp/data/
```

### 5. Initialize Database

```bash
cd /home/laukayson/englishlearningapp/backend
python3 -c "
import sqlite3
conn = sqlite3.connect('../data/db/app_database.db')
cursor = conn.cursor()
# Create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    age INTEGER,
    level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()
conn.close()
print('Database initialized successfully')
"
```

## ⚙️ Production Configuration

### Browser Settings (Automatic)
- 🤖 **AI Chatbot:** HIDDEN (headless mode)
- 🎤 **SpeechTexter:** HIDDEN (headless mode)
- ✅ **Both services enabled**

This is configured in `.env.production` and will be loaded automatically.

### User Level Mapping (Fixed)
- **Level 1** → Absolute Beginner (very simple responses)
- **Level 2** → Beginner (simple, clear responses)  
- **Level 3** → Intermediate (more complex vocabulary)
- **Level 4** → Advanced (natural, complex responses)

## 🔧 Environment Variables

The app will automatically load production settings from `.env.production`:
```env
CHATBOT_HEADLESS=true
STT_HEADLESS=true
ENABLE_SELENIUM_CHATBOT=true
ENABLE_WEB_STT=true
ENVIRONMENT=production
```

## 📱 Features Included

✅ **Core Learning Features:**
- Multi-level English conversation (4 proficiency levels)
- Speech-to-text with SpeechTexter integration
- AI tutoring with Gemini automation
- Bilingual interface (English/Farsi)
- Progress tracking and user management

✅ **Technical Features:**
- Selenium browser automation (headless in production)
- Rate limiting for API protection
- User authentication and sessions
- Responsive web interface
- Production logging

## 🎯 Access Your App

After deployment, your app will be available at:
**https://laukayson.pythonanywhere.com**

## 🔍 Troubleshooting

### If the app doesn't start:
1. Check error logs in PythonAnywhere Error Log
2. Verify all directories were created
3. Check database permissions
4. Ensure virtual environment is activated

### If browsers don't work:
- Browser automation runs in headless mode (no windows)
- Check that Chrome is available on PythonAnywhere
- Verify selenium and webdriver-manager are installed

### If user levels don't work:
- The level mapping is now fixed in selenium_chatbot.py
- Frontend levels (1,2,3,4) map to AI levels automatically
- Check that users can change levels in settings (gear icon)

## ✅ Ready for Production!

Your app is now cleaned, optimized, and ready for PythonAnywhere deployment with:
- Production-safe configuration
- Working browser automation (headless)
- Fixed user level functionality
- All development files removed
