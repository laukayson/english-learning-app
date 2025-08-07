"""
Speech-to-Text Service using Selenium
Handles voice recognition via web scraping
"""

import time
import logging
import uuid
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self, browser_manager):
        self.browser_manager = browser_manager
        self.active_sessions = {}
        
    def start_session(self, language='en'):
        """Start a new STT session"""
        try:
            session_id = str(uuid.uuid4())
            
            # Get browser session
            browser_session_id, driver = self.browser_manager.get_session("stt")
            
            # Navigate to SpeechTexter
            driver.get("https://speechtexter.com/")
            time.sleep(3)
            
            # Set up language if needed
            self._setup_language(driver, language)
            
            # Start recording
            self._start_recording(driver)
            
            # Store session info
            self.active_sessions[session_id] = {
                'browser_session_id': browser_session_id,
                'driver': driver,
                'language': language,
                'started_at': time.time(),
                'recording': True
            }
            
            logger.info(f"STT session started: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"STT session start failed: {str(e)}")
            if 'browser_session_id' in locals():
                self.browser_manager.release_session(browser_session_id)
            raise Exception(f"Failed to start STT session: {str(e)}")
    
    def get_result(self, session_id):
        """Get current transcription result"""
        try:
            if session_id not in self.active_sessions:
                raise Exception("Session not found")
            
            session = self.active_sessions[session_id]
            driver = session['driver']
            
            # Mark browser session as in use
            self.browser_manager.use_session(session['browser_session_id'])
            
            # Get transcription text
            text = self._get_transcription_text(driver)
            
            # Release browser session
            self.browser_manager.release_session(session['browser_session_id'])
            
            return text
            
        except Exception as e:
            logger.error(f"STT get result failed: {str(e)}")
            if session_id in self.active_sessions:
                self.browser_manager.release_session(
                    self.active_sessions[session_id]['browser_session_id']
                )
            raise Exception(f"Failed to get STT result: {str(e)}")
    
    def stop_session(self, session_id):
        """Stop STT session and get final result"""
        try:
            if session_id not in self.active_sessions:
                raise Exception("Session not found")
            
            session = self.active_sessions[session_id]
            driver = session['driver']
            
            # Mark browser session as in use
            self.browser_manager.use_session(session['browser_session_id'])
            
            # Stop recording
            self._stop_recording(driver)
            
            # Get final transcription
            text = self._get_transcription_text(driver)
            
            # Clean up
            self.browser_manager.close_session(session['browser_session_id'])
            del self.active_sessions[session_id]
            
            logger.info(f"STT session stopped: {session_id}")
            return text
            
        except Exception as e:
            logger.error(f"STT session stop failed: {str(e)}")
            if session_id in self.active_sessions:
                self.browser_manager.release_session(
                    self.active_sessions[session_id]['browser_session_id']
                )
                del self.active_sessions[session_id]
            raise Exception(f"Failed to stop STT session: {str(e)}")
    
    def _setup_language(self, driver, language):
        """Set up language for speech recognition"""
        try:
            # Look for language selector (this depends on SpeechTexter's UI)
            language_selectors = {
                'en': 'English',
                'es': 'Spanish', 
                'fr': 'French',
                'de': 'German',
                'it': 'Italian'
            }
            
            if language in language_selectors:
                # Try to find and click language selector
                # This is a simplified implementation - may need adjustment
                pass
                
        except Exception as e:
            logger.warning(f"Language setup failed: {str(e)}")
            # Continue with default language
    
    def _start_recording(self, driver):
        """Start recording on SpeechTexter"""
        try:
            # Wait for page to load
            wait = WebDriverWait(driver, 10)
            
            # Look for the microphone/start button
            # This selector may need adjustment based on SpeechTexter's current UI
            start_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[title*='Start'], [title*='Record'], .mic-button, #start"))
            )
            start_button.click()
            
            # Wait a moment for recording to start
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Recording start failed: {str(e)}")
            raise Exception("Failed to start recording")
    
    def _stop_recording(self, driver):
        """Stop recording on SpeechTexter"""
        try:
            # Look for the stop button
            stop_button = driver.find_element(By.CSS_SELECTOR, "[title*='Stop'], .stop-button, #stop")
            stop_button.click()
            
            # Wait for recording to stop
            time.sleep(1)
            
        except Exception as e:
            logger.warning(f"Recording stop failed: {str(e)}")
            # May already be stopped or UI changed
    
    def _get_transcription_text(self, driver):
        """Get transcribed text from SpeechTexter"""
        try:
            # Look for the text area where transcription appears
            # This selector may need adjustment based on SpeechTexter's current UI
            possible_selectors = [
                "#textarea",
                ".transcription-text",
                "[name='text']",
                "textarea",
                ".text-output"
            ]
            
            for selector in possible_selectors:
                try:
                    text_element = driver.find_element(By.CSS_SELECTOR, selector)
                    text = text_element.get_attribute('value') or text_element.text
                    if text.strip():
                        return text.strip()
                except:
                    continue
            
            # If no text found, return empty string
            return ""
            
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            return ""
    
    def cleanup_expired_sessions(self):
        """Clean up expired STT sessions"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            # Sessions expire after 10 minutes
            if current_time - session['started_at'] > 600:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            try:
                self.stop_session(session_id)
            except:
                pass  # Session may already be cleaned up
        
        return len(expired_sessions)
