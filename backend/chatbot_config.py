"""
Configuration for the Language Learning App Chatbot
"""

import os
from typing import Dict, Any

def load_env_file(env_path='.env'):
    """Load environment variables from .env file if it exists"""
    try:
        # For PythonAnywhere production, prefer .env.production
        production_env = '.env.production'
        if os.path.exists(production_env):
            env_path = production_env
        elif not os.path.exists(env_path):
            # Try parent directory
            parent_env = os.path.join('..', '.env')
            parent_production = os.path.join('..', '.env.production')
            if os.path.exists(parent_production):
                env_path = parent_production
            elif os.path.exists(parent_env):
                env_path = parent_env
            else:
                return  # No .env file found
        
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print(f"✅ Loaded environment variables from {env_path}")
    except Exception as e:
        print(f"⚠️ Could not load .env file: {e}")

# Load .env file before setting up configuration
load_env_file()
load_env_file('../.env.production')  # Also try parent directory for production
load_env_file('../.env')  # Fallback to regular .env

class ChatbotConfig:
    """Configuration class for chatbot settings"""
    
    # Selenium Chatbot Configuration (AI Conversations)
    ENABLE_SELENIUM_CHATBOT = os.getenv('ENABLE_SELENIUM_CHATBOT', 'false').lower() == 'true'
    # Chatbot browser visibility - defaults to headless (true) for production
    CHATBOT_HEADLESS = os.getenv('CHATBOT_HEADLESS', 'true').lower() == 'true'
    SELENIUM_TIMEOUT = int(os.getenv('SELENIUM_TIMEOUT', '30'))
    SELENIUM_TARGET_URL = os.getenv('SELENIUM_TARGET_URL', 'https://tinyurl.com/49kj3jns')
    
    # Google Translate STT Configuration (Speech-to-Text)
    ENABLE_WEB_STT = os.getenv('ENABLE_WEB_STT', 'true').lower() == 'true'
    # STT browser visibility - defaults to headless (true) for production
    STT_HEADLESS = os.getenv('STT_HEADLESS', 'true').lower() == 'true'
    STT_TIMEOUT = int(os.getenv('STT_TIMEOUT', '30'))
    
    # Legacy support (for backward compatibility)
    SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'true').lower() == 'true'  # Fallback for old configs
    
    # Fallback Response Configuration
    USE_FALLBACK_RESPONSES = True
    FALLBACK_RESPONSE_STYLE = 'educational'  # 'educational', 'conversational', 'supportive'
    
    # General Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    MAX_RESPONSE_LENGTH = int(os.getenv('MAX_RESPONSE_LENGTH', '500'))
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration as a dictionary"""
        return {
            'selenium_enabled': cls.ENABLE_SELENIUM_CHATBOT,
            'chatbot_headless': cls.CHATBOT_HEADLESS,
            'stt_enabled': cls.ENABLE_WEB_STT,
            'stt_headless': cls.STT_HEADLESS,
            'selenium_timeout': cls.SELENIUM_TIMEOUT,
            'stt_timeout': cls.STT_TIMEOUT,
            'selenium_url': cls.SELENIUM_TARGET_URL,
            'use_fallback': cls.USE_FALLBACK_RESPONSES,
            'fallback_style': cls.FALLBACK_RESPONSE_STYLE,
            'log_level': cls.LOG_LEVEL,
            'max_response_length': cls.MAX_RESPONSE_LENGTH,
            # Legacy support
            'selenium_headless': cls.SELENIUM_HEADLESS
        }
    
    @classmethod
    def enable_selenium_chatbot(cls):
        """Enable the Selenium chatbot for the current session"""
        cls.ENABLE_SELENIUM_CHATBOT = True
        os.environ['ENABLE_SELENIUM_CHATBOT'] = 'true'
    
    @classmethod
    def disable_selenium_chatbot(cls):
        """Disable the Selenium chatbot for the current session"""
        cls.ENABLE_SELENIUM_CHATBOT = False
        os.environ['ENABLE_SELENIUM_CHATBOT'] = 'false'
    
    @classmethod
    def force_headless_mode(cls):
        """Force headless mode to be enabled (no browser windows)"""
        cls.CHATBOT_HEADLESS = True
        cls.STT_HEADLESS = True
        os.environ['CHATBOT_HEADLESS'] = 'true'
        os.environ['STT_HEADLESS'] = 'true'
        # Legacy support
        cls.SELENIUM_HEADLESS = True
        os.environ['SELENIUM_HEADLESS'] = 'true'
    
    @classmethod
    def enable_debug_mode(cls):
        """Enable debug mode (visible browser windows for both services)"""
        cls.CHATBOT_HEADLESS = False
        cls.STT_HEADLESS = False
        os.environ['CHATBOT_HEADLESS'] = 'false'
        os.environ['STT_HEADLESS'] = 'false'
        # Legacy support
        cls.SELENIUM_HEADLESS = False
        os.environ['SELENIUM_HEADLESS'] = 'false'
    
    @classmethod
    def force_stt_visible(cls):
        """Force STT service to run in visible mode for debugging"""
        cls.STT_HEADLESS = False
        os.environ['STT_HEADLESS'] = 'false'
    
    @classmethod
    def set_chatbot_headless(cls, headless: bool):
        """Set headless mode specifically for AI chatbot"""
        cls.CHATBOT_HEADLESS = headless
        os.environ['CHATBOT_HEADLESS'] = 'true' if headless else 'false'
    
    @classmethod
    def set_stt_headless(cls, headless: bool):
        """Set headless mode specifically for STT service"""
        cls.STT_HEADLESS = headless
        os.environ['STT_HEADLESS'] = 'true' if headless else 'false'
    
    @classmethod
    def ensure_headless_mode(cls):
        """Ensure headless mode is enabled for security and performance"""
        if not cls.CHATBOT_HEADLESS:
            cls.CHATBOT_HEADLESS = True
            os.environ['CHATBOT_HEADLESS'] = 'true'
        if not cls.STT_HEADLESS:
            cls.STT_HEADLESS = True
            os.environ['STT_HEADLESS'] = 'true'
        return cls.CHATBOT_HEADLESS and cls.STT_HEADLESS

# Default configuration
DEFAULT_CONFIG = ChatbotConfig.get_config()
