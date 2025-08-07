# 🚀 Complete Migration Guide: PythonAnywhere → Render + Turso

## Overview
This guide will help you migrate your English Learning App from PythonAnywhere to Render (hosting) + Turso (database) to eliminate outbound access restrictions while maintaining ALL features including voice recognition and browser automation.

## ✅ Prerequisites Checklist
- [ ] GitHub account (for code deployment)
- [ ] Render account (free tier: https://render.com)
- [ ] Turso account (free tier: https://turso.tech)
- [ ] Git installed on your local machine

---

## 📊 **STEP 1: Set Up Turso Database**

### 1.1 Create Turso Account
1. Go to https://turso.tech
2. Click "Sign Up" and create a free account
3. Verify your email if required

### 1.2 Create Database via Web Console
1. Login to Turso dashboard: https://app.turso.tech
2. Click "Create Database"
3. Choose these settings:
   - **Database Name**: `english-learning-app`
   - **Location**: Choose closest to your users (e.g., `lhr` for London, `iad` for US East)
   - **Plan**: Free (25 databases, 1M row reads/month, 1K row writes/month)
4. Click "Create Database"

### 1.3 Get Database Credentials
After database creation, you'll see:
- **Database URL**: `libsql://your-db-name-your-org.turso.io`
- **Auth Token**: Click "Create Token" → "Read & Write" → Copy the token

**📝 SAVE THESE VALUES - YOU'LL NEED THEM FOR RENDER!**

### 1.4 Initialize Database Schema
1. In Turso dashboard, open your database
2. Go to "SQL Console" tab
3. Run this SQL to create your tables:

**Run these SQL commands one at a time in the Turso SQL Console:**

```sql
-- Step 1: Create Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    level INTEGER NOT NULL,
    settings TEXT DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

```sql
-- Step 2: Create User progress table
CREATE TABLE user_progress (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    level INTEGER NOT NULL,
    conversations_count INTEGER DEFAULT 0,
    words_learned INTEGER DEFAULT 0,
    pronunciation_score REAL DEFAULT 0.0,
    last_practice DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

```sql
-- Step 3: Create Chat history table (optional but recommended)
CREATE TABLE chat_history (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    topic TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

```sql
-- Step 4: Create indexes for better performance (run these one by one)
CREATE INDEX idx_users_username ON users(username);
```

```sql
CREATE INDEX idx_progress_user_id ON user_progress(user_id);
```

```sql
CREATE INDEX idx_progress_topic ON user_progress(topic);
```

```sql
CREATE INDEX idx_chat_user_id ON chat_history(user_id);
```

```sql
CREATE INDEX idx_chat_timestamp ON chat_history(timestamp);
```

4. **Execute the SQL step by step**: Copy and paste each SQL block above into the Turso SQL console and click "Execute" after each one. This ensures each table is created before the indexes.

---

## 🔧 **STEP 2: Prepare Your Code for Render**

### 2.1 Application Entry Point Configuration
Since you've chosen the **full-featured version**, your render.yaml is already configured correctly:

```yaml
startCommand: python backend/app.py
```

This gives you:
- ✅ **Voice recognition** (speech-to-text)
- ✅ **Text-to-speech** (audio generation)
- ✅ **Browser automation** (Selenium-powered conversational AI)
- ✅ **Complete AI chat** with full context and history
- ✅ **All original features** from your PythonAnywhere app

### 2.2 Verify Required Files
Make sure these files exist in your project:
- [ ] `requirements.txt` (✅ Already created)
- [ ] `backend/config.py` (✅ Already created) 
- [ ] `backend/app.py` (✅ Already created)
- [ ] `backend/turso_service.py` (✅ Already created)
- [ ] `render.yaml` (✅ Already created)

---

## 📁 **STEP 3: Set Up GitHub Repository**

### 3.1 Initialize Git Repository
```bash
# Navigate to your project folder
cd d:\D\Coding\Applications\app\englishlearningapp

# Initialize Git repository
git init

# Add all files to staging
git add .

# Create initial commit
git commit -m "Initial commit - English Learning App ready for Render + Turso migration"
```

### 3.2 Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `english-learning-app`
3. Description: `AI-powered English learning app with voice features`
4. Visibility: Public (required for free Render plan)
5. Click "Create repository"
6. **Don't initialize with README** (since you already have files)

### 3.3 Push Code to GitHub
```bash
# Connect to your GitHub repository
git remote add origin https://github.com/laukayson/english-learning-app.git

# Rename branch to main
git branch -M main

# Push your code
git push -u origin main
```

✅ **Status: Complete!** Your code is now on GitHub at: https://github.com/laukayson/english-learning-app

---

## 🌐 **STEP 4: Deploy to Render**

### 4.1 Create Render Account
1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended for easy deployment)

### 4.2 Connect GitHub Repository
1. In Render dashboard, click "New +"
2. Select "Web Service"
3. Connect your GitHub account if prompted
4. Select your `english-learning-app` repository
5. Click "Connect"

### 4.3 Configure Deployment Settings
**Basic Settings:**
- **Name**: `english-learning-app` (or your preferred name)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python backend/app.py` ✅ **Full-featured version**

**Advanced Settings:**
- **Instance Type**: `Free` (512 MB RAM, shared CPU)
- **Auto-Deploy**: `Yes` (deploys on every GitHub push)

### 4.4 Add Environment Variables
Click "Environment" tab and add these variables:

| Key | Value | Notes |
|-----|-------|-------|
| `TURSO_DATABASE_URL` | `libsql://your-db-url` | From Step 1.3 |
| `TURSO_AUTH_TOKEN` | `your-auth-token` | From Step 1.3 - **SECURE TOKEN** |
| `FLASK_ENV` | `production` | Sets Flask to production mode |
| `PORT` | `10000` | Render's default port |
| `RENDER` | `true` | Enables Render-specific features |
| `SELENIUM_HEADLESS` | `true` | Runs browser automation headlessly |

**🔐 IMPORTANT**: Keep your `TURSO_AUTH_TOKEN` secure! This token provides full read/write access to your database.

### 4.5 Deploy!
1. Click "Create Web Service"
2. Render will start building your app (this takes 5-10 minutes)
3. Watch the build logs for any errors
4. Once complete, you'll get a URL like `https://your-app-name.onrender.com`

---

## 🧪 **STEP 5: Test Your Migration**

### 5.1 Health Check
Visit: `https://your-app-name.onrender.com/health`

You should see:
```json
{
  "status": "healthy",
  "environment": "render",
  "database": "connected",
  "features": {
    "voice_features": true,
    "web_stt": true,
    "selenium_chatbot": true
  }
}
```

### 5.2 Test Core Features
1. **Frontend**: Visit your app URL
2. **Registration**: Create a test user account
3. **Chat**: Test AI conversation
4. **Voice**: Test speech-to-text (if browser supports)
5. **Translation**: Test English ↔ Farsi translation

### 5.3 Monitor Performance
- Check Render logs for any errors
- Monitor Turso usage in their dashboard
- Test response times from different locations

---

## 🔄 **STEP 6: Data Migration (if you have existing data)**

### 6.1 Export from PythonAnywhere
If you have existing user data on PythonAnywhere:

1. Access your PythonAnywhere console
2. Export your SQLite database:
```bash
sqlite3 your_database.db .dump > database_backup.sql
```
3. Download the backup file

### 6.2 Import to Turso
1. Clean up the SQL file (remove SQLite-specific commands)
2. In Turso console, run the INSERT statements
3. Or use the migration script we created: `migrate_to_turso.py`

---

## 🎯 **STEP 7: Performance Optimization**

### 7.1 Render Optimizations
- **Keep warm**: Free tier sleeps after 15 minutes of inactivity
- **Custom domain**: Add your own domain (optional)
- **Monitoring**: Set up health check endpoints

### 7.2 Turso Optimizations
- **Location**: Ensure database is in optimal region
- **Indexing**: Add indexes for frequently queried fields
- **Connection pooling**: Already handled by turso_service.py

---

## 🚨 **Troubleshooting Common Issues**

### Build Failures
- **Chrome installation fails**: Check apt-get commands in render.yaml
- **Python dependencies**: Verify requirements_render_full.txt
- **Memory issues**: Free tier has 512MB limit

### Database Connection Issues
- **Wrong URL/Token**: Double-check Turso credentials
- **Network issues**: Turso should work from anywhere
- **Schema errors**: Ensure tables are created

### Voice Features Not Working
- **Browser compatibility**: Chrome/Firefox work best
- **HTTPS required**: Voice features need secure connection
- **Microphone permissions**: User must grant access

---

## 📊 **Resource Limits & Costs**

### Render Free Tier
- ✅ 750 hours/month (enough for always-on app)
- ✅ 512 MB RAM
- ✅ Shared CPU
- ✅ 100 GB bandwidth/month
- ✅ Custom domains
- ⚠️ Sleeps after 15 min inactivity

### Turso Free Tier
- ✅ 25 databases
- ✅ 1M row reads/month
- ✅ 1K row writes/month  
- ✅ 500 MB storage
- ✅ Global edge locations
- ⚠️ No backups on free tier

### When to Upgrade
- **Render**: If you need always-on ($7/month)
- **Turso**: If you exceed read/write limits ($5/month)

---

## ✅ **Success Checklist**

- [ ] Turso database created and configured
- [ ] GitHub repository set up
- [ ] Render deployment successful
- [ ] Health check passes
- [ ] Core features working
- [ ] Voice features functional
- [ ] Database operations successful
- [ ] Performance acceptable

---

## 🎉 **You're Done!**

Your English Learning App is now running on Render + Turso with:
- ✅ **No outbound access restrictions**
- ✅ **All original features preserved**
- ✅ **Voice recognition and browser automation**
- ✅ **Global edge database**
- ✅ **Free hosting and database**
- ✅ **Automatic deployments**

Your app should be significantly faster and more reliable than PythonAnywhere!

---

## 🆘 **Need Help?**

If you encounter any issues:
1. Check the troubleshooting section above
2. Review Render build logs
3. Check Turso connection in health endpoint
4. Feel free to ask for assistance!
