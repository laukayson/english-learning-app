"""
Render Selenium Client
Integrates PythonAnywhere backend with Render Selenium service
"""

import requests
import logging
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class RenderSeleniumClient:
    def __init__(self, render_url: str, timeout: int = 30):
        """
        Initialize client for Render Selenium service
        
        Args:
            render_url: Base URL of your Render Selenium service
            timeout: Request timeout in seconds
        """
        self.base_url = render_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def health_check(self) -> bool:
        """Check if Selenium service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    # Chatbot methods
    def send_chatbot_message(self, message: str, topic: str = "general", 
                           level: int = 1, user_level: str = "beginner") -> str:
        """
        Send message to AI chatbot
        
        Args:
            message: User message
            topic: Conversation topic
            level: User level (1-4)
            user_level: User level string
            
        Returns:
            AI response text
        """
        try:
            data = {
                'message': message,
                'topic': topic,
                'level': level,
                'user_level': user_level
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chatbot/send-message",
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response received')
            else:
                logger.error(f"Chatbot API error: {response.status_code}")
                return "I'm sorry, I'm having trouble responding right now."
                
        except requests.exceptions.Timeout:
            logger.error("Chatbot request timeout")
            return "I'm taking too long to respond. Please try again."
        except Exception as e:
            logger.error(f"Chatbot request failed: {str(e)}")
            return "I'm having technical difficulties. Please try again."
    
    def init_chatbot_context(self, topic: str, level: int = 1, 
                           user_level: str = "beginner") -> bool:
        """
        Initialize chatbot context for a topic
        
        Args:
            topic: Conversation topic
            level: User level (1-4)
            user_level: User level string
            
        Returns:
            True if successful
        """
        try:
            data = {
                'topic': topic,
                'level': level,
                'user_level': user_level
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chatbot/init-context",
                json=data,
                timeout=self.timeout
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Context initialization failed: {str(e)}")
            return False
    
    def end_chatbot_conversation(self) -> bool:
        """
        End the current chatbot conversation and release resources
        
        Returns:
            True if successful
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/chatbot/end-conversation",
                timeout=self.timeout
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"End conversation failed: {str(e)}")
            return False
    
    # Speech-to-Text methods
    def start_stt_session(self, language: str = 'en') -> Optional[str]:
        """
        Start a speech-to-text session
        
        Args:
            language: Language code (en, es, fr, etc.)
            
        Returns:
            Session ID if successful, None otherwise
        """
        try:
            data = {'language': language}
            
            response = self.session.post(
                f"{self.base_url}/api/stt/start-recording",
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('session_id')
            else:
                logger.error(f"STT start error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"STT start failed: {str(e)}")
            return None
    
    def get_stt_result(self, session_id: str) -> str:
        """
        Get current STT transcription
        
        Args:
            session_id: STT session ID
            
        Returns:
            Transcribed text
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/stt/get-result/{session_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('text', '')
            else:
                logger.error(f"STT result error: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"STT result failed: {str(e)}")
            return ""
    
    def stop_stt_session(self, session_id: str) -> str:
        """
        Stop STT session and get final result
        
        Args:
            session_id: STT session ID
            
        Returns:
            Final transcribed text
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/stt/stop-recording/{session_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('text', '')
            else:
                logger.error(f"STT stop error: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"STT stop failed: {str(e)}")
            return ""
    
    # Translation methods
    def translate_text(self, text: str, target_lang: str = 'fa', source_lang: str = 'en') -> str:
        """
        Translate text using Render translation service
        
        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code
            
        Returns:
            Translated text
        """
        try:
            data = {
                'text': text,
                'target_lang': target_lang,
                'source_lang': source_lang
            }
            
            response = self.session.post(
                f"{self.base_url}/api/translate",
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('translation', text)
            else:
                logger.error(f"Translation API error: {response.status_code}")
                return text
                
        except requests.exceptions.Timeout:
            logger.error("Translation request timeout")
            return text
        except Exception as e:
            logger.error(f"Translation request failed: {str(e)}")
            return text

    # Service management methods
    def get_service_status(self) -> Dict[str, Any]:
        """Get detailed service status"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/service/status",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'Status check failed: {response.status_code}'}
                
        except Exception as e:
            return {'error': f'Status check failed: {str(e)}'}
    
    def cleanup_service(self) -> bool:
        """Trigger service cleanup"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/service/cleanup",
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Service cleanup failed: {str(e)}")
            return False

# Singleton instance for easy import
selenium_client = None

def init_selenium_client(render_url: str):
    """Initialize the global selenium client"""
    global selenium_client
    selenium_client = RenderSeleniumClient(render_url)
    return selenium_client

def get_selenium_client() -> Optional[RenderSeleniumClient]:
    """Get the global selenium client"""
    return selenium_client
