# Render + Turso Deployment Guide

## Quick Setup Overview

### 1. Turso Database Setup (5 minutes)
1. Sign up at https://turso.tech/ (free account)
2. Create new database: `english-learning-app`
3. Get your database URL and auth token
4. Keep these credentials safe

### 2. Render Deployment (10 minutes)
1. Sign up at https://render.com/ (free account)
2. Connect your GitHub repository
3. Create new Web Service
4. Use these settings:
   - Build Command: `pip install -r requirements_render.txt`
   - Start Command: `cd backend && python app_render.py`
   - Environment: Python
   - Plan: Free

### 3. Environment Variables
Add these in Render dashboard:
```
TURSO_DATABASE_URL=libsql://your-database-url
TURSO_AUTH_TOKEN=your-auth-token
FLASK_ENV=production
PORT=10000
```

## Detailed Setup Instructions

### Step 1: Turso Database Setup

1. **Create Turso Account**:
   - Go to https://turso.tech/
   - Sign up with GitHub (recommended)
   - Verify your email

2. **Create Database**:
   ```bash
   # Install Turso CLI (optional)
   curl -sSfL https://get.tur.so/install.sh | bash
   
   # Or use web dashboard
   ```

3. **Get Credentials**:
   - Database URL: `libsql://your-db-name-your-org.turso.io`
   - Auth Token: Generate in dashboard under "Settings" → "Tokens"

### Step 2: Render Web Service Setup

1. **Connect Repository**:
   - Go to https://render.com/
   - Sign up and connect your GitHub account
   - Select your repository

2. **Create Web Service**:
   - Choose "Web Service"
   - Select your repository
   - Set branch to `main`

3. **Configuration**:
   ```yaml
   Name: english-learning-app
   Environment: Python
   Region: Oregon (US West) - or closest to you
   Branch: main
   Build Command: pip install -r requirements_render.txt
   Start Command: cd backend && python app_render.py
   ```

4. **Environment Variables**:
   ```
   TURSO_DATABASE_URL=libsql://your-database-your-org.turso.io
   TURSO_AUTH_TOKEN=your_auth_token_here
   FLASK_ENV=production
   PORT=10000
   RENDER=true
   ```

### Step 3: Data Migration (if you have existing data)

1. **Install Migration Dependencies**:
   ```bash
   pip install libsql-client
   ```

2. **Run Migration Script**:
   ```bash
   python migrate_to_turso.py
   ```

3. **Follow Prompts**:
   - Enter your SQLite database path
   - Enter your Turso database URL
   - Enter your Turso auth token

### Step 4: Test Deployment

1. **Check Health Endpoint**:
   ```
   https://your-app-name.onrender.com/health
   ```

2. **Test Features**:
   - User registration/login
   - Text-based chat
   - Translation
   - Progress tracking

## Features Available on Render

✅ **Available Features**:
- Text-based AI chat
- User registration and login
- Progress tracking and gamification
- English-Farsi translation
- Topic-based learning
- Responsive web interface

❌ **Disabled Features** (due to Render limitations):
- Voice recognition (STT)
- Text-to-speech (TTS)
- Browser automation (Selenium)
- Image generation

## Cost Breakdown

### Turso Database:
- **Free Tier**: 500 DB reads/writes per day
- **Paid Plans**: Start at $5/month for higher limits
- **Recommended**: Start with free, upgrade if needed

### Render Hosting:
- **Free Tier**: 
  - 750 hours/month (enough for 24/7)
  - Auto-sleep after 15 min of inactivity
  - Limited to 1 concurrent build
- **Paid Plans**: Start at $7/month for always-on service

### Total Cost:
- **Development/Testing**: $0/month
- **Production**: $0-12/month depending on usage

## Monitoring and Maintenance

### Health Checks:
- Render automatically monitors your app
- Check `/health` endpoint for detailed status
- Database status included in health check

### Logs:
- View logs in Render dashboard
- Filter by timestamp and log level
- Download logs for offline analysis

### Updates:
- Push to GitHub to trigger auto-deployment
- Use environment variables for configuration
- Database schema updates handled automatically

## Troubleshooting

### Common Issues:

1. **Build Failures**:
   - Check requirements_render.txt dependencies
   - Verify Python version compatibility
   - Review build logs in Render dashboard

2. **Database Connection Issues**:
   - Verify TURSO_DATABASE_URL format
   - Check auth token validity
   - Test connection locally first

3. **App Won't Start**:
   - Check start command: `cd backend && python app_render.py`
   - Verify PORT environment variable
   - Review application logs

### Getting Help:
- Check Render documentation: https://render.com/docs
- Turso documentation: https://docs.turso.tech/
- GitHub issues for app-specific problems

## Security Considerations

### Environment Variables:
- Never commit secrets to GitHub
- Use Render's environment variable system
- Rotate auth tokens periodically

### Database Security:
- Turso provides automatic encryption
- Use strong auth tokens
- Monitor access patterns

### Application Security:
- HTTPS enforced by Render
- Rate limiting implemented
- Input validation in place

## Performance Optimization

### Database:
- Turso provides global edge locations
- Connection pooling handled automatically
- Monitor query performance

### Application:
- Static files served efficiently
- Response caching where appropriate
- Minimal dependencies for faster startup

### Monitoring:
- Use Render metrics dashboard
- Monitor response times
- Track error rates

## Backup and Recovery

### Database Backups:
- Turso provides automatic backups
- Export data using migration script
- Test restore procedures regularly

### Application Backups:
- Code is version controlled in GitHub
- Environment variables documented
- Deployment process automated
