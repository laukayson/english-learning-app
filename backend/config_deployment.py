"""
Production configuration for the language learning app
"""
import os

class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    
    # Database configuration
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'db', 'language_app.db')
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # API Configuration
    API_RATE_LIMIT = {
        'REQUESTS_PER_MINUTE': 30,
        'REQUESTS_PER_HOUR': 200
    }
    
    # Security settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
    
    # CORS settings
    CORS_ORIGINS = [
        'https://*.pythonanywhere.com',
        'http://localhost:*',
        'http://127.0.0.1:*'
    ]

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    CORS_ORIGINS = ['*']  # Allow all origins in development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Add production-specific settings here

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
