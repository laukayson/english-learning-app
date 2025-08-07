"""
Google Translate service using direct HTTP requests
"""
import logging
import requests
import json
import time
import traceback

logger = logging.getLogger(__name__)

class GoogleTranslationService:
    def __init__(self):
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        logger.info("Google Translate service created and ready for use")
    
    def _translate_text(self, text, source_lang, target_lang):
        """
        Translate text using Google Translate web interface
        """
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last)
            
            # Use the Google Translate web interface URL
            url = "https://translate.googleapis.com/translate_a/single"
            
            params = {
                'client': 'gtx',
                'sl': source_lang,
                'tl': target_lang,
                'dt': 't',
                'q': text
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            logger.info(f"Making request to Google Translate API with text: '{text[:100]}...'")
            
            response = self.session.get(url, params=params, headers=headers)
            self.last_request_time = time.time()
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.info(f"Raw API response structure: {type(result)} with {len(result) if isinstance(result, list) else 'unknown'} elements")
                    
                    if result and isinstance(result, list) and len(result) > 0:
                        translation_segments = result[0]
                        if isinstance(translation_segments, list):
                            logger.info(f"Found {len(translation_segments)} translation segments")
                            
                            # Concatenate all translation segments
                            translation_parts = []
                            for i, segment in enumerate(translation_segments):
                                if isinstance(segment, list) and len(segment) > 0:
                                    segment_text = segment[0]
                                    translation_parts.append(segment_text)
                            
                            final_translation = ''.join(translation_parts)
                            
                            self.last_request_time = time.time()
                            return final_translation
                
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Response text: {response.text[:200]}...")
            
            logger.warning(f"Google Translate API returned status: {response.status_code}")
            if response.status_code != 200:
                logger.warning(f"Response text: {response.text[:200]}...")
            return ""
            
        except Exception as e:
            logger.error(f"Google Translate request failed: {e}")
            logger.error(traceback.format_exc())
            return ""
    
    def translate_english_to_farsi(self, text):
        """
        Translate English text to Farsi using Google Translate
        """
        
        if not text.strip():
            return ""
        
        try:
            logger.info(f"STARTING TRANSLATION - Input: '{text}' (length: {len(text)})")
            logger.info(f"Translating with Google Translate: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            translation = self._translate_text(text, "en", "fa")
            
            if translation and translation.strip():
                logger.info(f"TRANSLATION SUCCESS - Input length: {len(text)}, Output length: {len(translation)}")
                logger.info(f"FULL RESULT: '{translation}'")
                return translation
            else:
                logger.warning("Google Translate returned empty result")
                return ""
                
        except Exception as e:
            logger.error(f"Google Translate error: {e}")
            return ""
    
    def get_service_info(self):
        return {
            "name": "Google Translate (HTTP)",
            "type": "cloud_api"
        }
