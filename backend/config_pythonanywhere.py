"""
PythonAnywhere-specific configuration for the language learning app
"""
import os

class Config:
    """Base configuration for PythonAnywhere"""
    DEBUG = False
    TESTING = False
    
    # Database configuration - environment-specific path
    if os.name == 'nt':  # Windows
        # Local development on Windows
        DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'db', 'language_app.db')
    else:
        # PythonAnywhere production path
        DATABASE_PATH = '/home/laukayson/englishlearningapp/data/db/language_app.db'
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # API Configuration - Reduced limits for PythonAnywhere
    API_RATE_LIMIT = {
        'REQUESTS_PER_MINUTE': 20,  # Reduced for PythonAnywhere
        'REQUESTS_PER_HOUR': 150    # Reduced for PythonAnywhere
    }
    
    # Security settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production-pythonanywhere')
    
    # CORS settings - PythonAnywhere specific
    CORS_ORIGINS = [
        'https://laukayson.pythonanywhere.com',
        'https://*.pythonanywhere.com'
    ]
    
    # PythonAnywhere and local development settings
    if os.name == 'nt':  # Windows local development
        MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
        base_path = os.path.dirname(os.path.dirname(__file__))
        UPLOAD_FOLDER = os.path.join(base_path, 'data', 'uploads')
        CACHE_FOLDER = os.path.join(base_path, 'data', 'cache')
        LOGS_FOLDER = os.path.join(base_path, 'data', 'logs')
    else:
        # PythonAnywhere production paths
        MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
        UPLOAD_FOLDER = '/home/laukayson/englishlearningapp/data/uploads'
        CACHE_FOLDER = '/home/laukayson/englishlearningapp/data/cache'
        LOGS_FOLDER = '/home/laukayson/englishlearningapp/data/logs'
    
    # Feature flags for PythonAnywhere limitations
    FEATURES = {
        'SELENIUM_CHATBOT': False,  # Selenium may not work on PythonAnywhere
        'IMAGE_GENERATION': False,  # May hit resource limits
        'VOICE_SYNTHESIS': True,
        'TRANSLATION': True,
        'PROGRESS_TRACKING': True
    }
    
    # AI Model configuration for resource constraints
    AI_CONFIG = {
        'MAX_TOKENS': 150,  # Reduced for faster response
        'TEMPERATURE': 0.7,
        'TIMEOUT': 30  # Seconds
    }

class PythonAnywhereConfig(Config):
    """Production configuration for PythonAnywhere"""
    DEBUG = False
    
    # Logging configuration
    LOG_LEVEL = 'WARNING'
    if os.name == 'nt':  # Windows local development
        LOG_FILE = os.path.join(Config.LOGS_FOLDER, 'app.log')
    else:
        LOG_FILE = '/home/laukayson/englishlearningapp/data/logs/app.log'
    
    # Database settings
    DATABASE_POOL_SIZE = 5  # Limited connection pool
    DATABASE_TIMEOUT = 20   # Database timeout in seconds

class DevelopmentConfig(Config):
    """Development configuration for testing on PythonAnywhere"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # More relaxed CORS for development
    CORS_ORIGINS = [
        'https://laukayson.pythonanywhere.com',
        'https://*.pythonanywhere.com',
        'http://localhost:*',
        'http://127.0.0.1:*'
    ]

# Configuration dictionary
config = {
    'production': PythonAnywhereConfig,
    'development': DevelopmentConfig,
    'default': PythonAnywhereConfig
}
