"""
Replit-specific configuration for the English Learning App
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

class Config:
    """Base configuration for Replit"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    
    # Database Configuration
    DATABASE_PATH = str(BASE_DIR / 'data' / 'database' / 'app.db')
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    os.makedirs(BASE_DIR / 'data' / 'logs', exist_ok=True)
    os.makedirs(BASE_DIR / 'data' / 'cache', exist_ok=True)
    
    # CORS Configuration - More permissive for Replit
    CORS_ORIGINS = [
        f"https://{os.environ.get('REPL_SLUG', 'app')}.{os.environ.get('REPL_OWNER', 'user')}.repl.co",
        "https://*.repl.co",
        "https://*.replit.dev",
        "http://localhost:*",
        "http://127.0.0.1:*"
    ]
    
    # Rate Limiting - Adjusted for Replit
    RATE_LIMIT = {
        'REQUESTS_PER_MINUTE': int(os.environ.get('RATE_LIMIT_REQUESTS_PER_MINUTE', 30)),
        'REQUESTS_PER_HOUR': int(os.environ.get('RATE_LIMIT_REQUESTS_PER_HOUR', 300))
    }
    
    # AI Configuration
    AI_CONFIG = {
        'PROVIDER': 'openai',  # Default to OpenAI for reliability
        'MODEL': os.environ.get('AI_MODEL', 'gpt-3.5-turbo'),
        'API_KEY': os.environ.get('OPENAI_API_KEY'),
        'MAX_TOKENS': 150,
        'TEMPERATURE': 0.7,
        'TIMEOUT': 30
    }
    
    # Feature Flags - Optimized for Replit
    FEATURES = {
        'SELENIUM_CHATBOT': False,  # Selenium doesn't work well on Replit
        'OPENAI_CHATBOT': True,     # Use OpenAI API instead
        'IMAGE_GENERATION': False,  # May hit resource limits
        'VOICE_SYNTHESIS': True,    # Browser-based TTS works fine
        'TRANSLATION': True,        # API-based translation
        'PROGRESS_TRACKING': True   # Local database tracking
    }
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = str(BASE_DIR / 'data' / 'logs' / 'app.log')
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = str(BASE_DIR / 'data' / 'uploads')

class DevelopmentConfig(Config):
    """Development configuration for Replit"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration for Replit deployment"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
