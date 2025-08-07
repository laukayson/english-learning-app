"""
Translation Service for Language Learning App - GOOGLE TRANSLATE API ONLY
NO FALLBACK SERVICES - PURE API TESTING MODE
"""

import logging
from typing import Optional, Dict, Any
import os

# ONLY GOOGLE TRANSLATE API - NO FALLBACKS FOR TESTING
try:
    from google_translation_service import GoogleTranslationService
    GOOGLE_TRANSLATION_AVAILABLE = True
    logging.info("Google Translate API loaded - NO FALLBACK SERVICES")
except ImportError:
    GOOGLE_TRANSLATION_AVAILABLE = False
    logging.error("Google translation service not available - NO FALLBACKS!")

# ALL FALLBACK SERVICES DISABLED FOR PURE API TESTING
SIMPLE_TRANSLATION_AVAILABLE = False
FREE_TRANSLATION_AVAILABLE = False  
LIGHTWEIGHT_AVAILABLE = False

# Set up logging
logger = logging.getLogger(__name__)

class TranslationService:
    """Google Translate API ONLY - No Fallback Translation Service"""
    
    def __init__(self):
        self.google_service = None
        self.primary_service = None
        self.ready = False
        
        logger.info("Initialising Translation Service - GOOGLE TRANSLATE API ONLY MODE")
        self.initialise_services()

    def initialise_services(self):
        """Initialize ONLY Google Translate service - NO FALLBACKS"""
        if not GOOGLE_TRANSLATION_AVAILABLE:
            logger.error("Google Translate service not available - NO FALLBACKS CONFIGURED!")
            raise Exception("Google Translate API is required - no fallback services available")
        
        logger.info("Initializing Google Translate service (API ONLY - NO FALLBACKS)...")
        self.google_service = GoogleTranslationService()
        self.primary_service = self.google_service  # Set the primary service
        self.ready = True  # Mark as ready
    
    def translate_english_to_farsi(self, text: str) -> str:
        """Translate English text to Farsi using ONLY Google Translate API"""
        if not self.ready or not self.primary_service:
            logger.error("Translation service not ready - Google Translate API required")
            raise Exception("Google Translate API not available")
        
        try:
            logger.info(f"Using Google Translate API for: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            result = self.primary_service.translate_english_to_farsi(text)
            
            if result:
                logger.info(f"Google Translate API success: '{result[:50]}{'...' if len(result) > 50 else ''}'")
                return result
            else:
                logger.error("Google Translate API returned empty result")
                raise Exception("Google Translate API failed to translate")
                
        except Exception as e:
            logger.error(f"Google Translate API error: {e}")
            raise Exception(f"Google Translate API failed: {e}")
    
    def is_ready(self) -> bool:
        """Check if translation service is ready"""
        return self.ready
    
    def translate_farsi_to_english(self, text: str) -> str:
        """Translate Farsi text to English using ONLY Google Translate API"""
        if not self.ready or not self.primary_service:
            logger.error("Translation service not ready - Google Translate API required")
            raise Exception("Google Translate API not available")
        
        try:
            logger.info(f"Using Google Translate API for Farsi->English: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            # Use the generic translate method
            result = self.primary_service._translate_text(text, "fa", "en")
            
            if result:
                logger.info(f"Google Translate API success: '{result[:50]}{'...' if len(result) > 50 else ''}'")
                return result
            else:
                logger.error("Google Translate API returned empty result")
                raise Exception("Google Translate API failed to translate")
                
        except Exception as e:
            logger.error(f"Google Translate API error: {e}")
            raise Exception(f"Google Translate API failed: {e}")

    def get_translation_stats(self) -> Dict[str, Any]:
        """Get translation service statistics"""
        if not self.ready or not self.primary_service:
            return {"service": "none", "status": "not_ready"}
        
        return {
            "service": "Google Translate API ONLY",
            "status": "ready",
            "fallbacks_disabled": True,
            "api_testing_mode": True
        }
