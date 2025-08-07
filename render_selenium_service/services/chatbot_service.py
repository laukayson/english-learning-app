"""
Chatbot Service using Selenium
Handles AI conversation via web scraping
"""

import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

logger = logging.getLogger(__name__)

class ChatbotService:
    def __init__(self, browser_manager):
        self.browser_manager = browser_manager
        self.session_id = None
        self.driver = None
        self.context_initialized = False
        
    def initialize_context(self, topic, level, user_level):
        """Initialize chatbot context for a topic"""
        try:
            # Get or create browser session
            self.session_id, self.driver = self.browser_manager.get_session("chatbot")
            
            # Navigate to AI service (using your existing URL)
            self.driver.get("https://tinyurl.com/49kj3jns")
            time.sleep(3)
            
            # Set context message
            context_message = self._build_context_message(topic, level, user_level)
            self._send_message_to_ai(context_message)
            
            self.context_initialized = True
            logger.info(f"Chatbot context initialized for topic: {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Context initialization failed: {str(e)}")
            if self.session_id:
                self.browser_manager.release_session(self.session_id)
            return False
    
    def get_ai_response(self, message, topic=None, level=None, user_level=None, persist_session=True):
        """Get AI response to user message"""
        try:
            # Initialize context if not done
            if not self.context_initialized:
                if topic and level and user_level:
                    self.initialize_context(topic, level, user_level)
                else:
                    # Use session without specific context, reuse existing if available
                    self.session_id, self.driver = self.browser_manager.get_session("chatbot", reuse_existing=True)
                    if not self.driver.current_url or "tinyurl.com/49kj3jns" not in self.driver.current_url:
                        self.driver.get("https://tinyurl.com/49kj3jns")
                        time.sleep(3)
            
            # Send message and get response
            response = self._send_message_to_ai(message)
            
            # Keep session alive for conversation continuity unless explicitly releasing
            if not persist_session:
                self.browser_manager.release_session(self.session_id)
                self.context_initialized = False
                self.session_id = None
                self.driver = None
            
            return response
            
        except Exception as e:
            logger.error(f"AI response failed: {str(e)}")
            if self.session_id:
                self.browser_manager.release_session(self.session_id)
                self.context_initialized = False
                self.session_id = None
                self.driver = None
            raise Exception(f"Failed to get AI response: {str(e)}")
    
    def end_conversation(self):
        """Explicitly end the conversation and release resources"""
        try:
            if self.session_id:
                self.browser_manager.release_session(self.session_id)
                self.context_initialized = False
                self.session_id = None
                self.driver = None
                logger.info("Conversation ended and session released")
                return True
        except Exception as e:
            logger.error(f"Error ending conversation: {str(e)}")
            return False
    
    def _build_context_message(self, topic, level, user_level):
        """Build context setting message"""
        level_descriptions = {
            1: "absolute beginner",
            2: "beginner", 
            3: "intermediate",
            4: "advanced"
        }
        
        level_desc = level_descriptions.get(level, user_level)
        
        context = f"""You are an English conversation tutor. The student is at {level_desc} level. 
        We're practicing the topic: {topic}. 
        Please respond naturally and helpfully, adjusting your language complexity to their level.
        Keep responses conversational and encouraging.
        Ready to start the conversation about {topic}."""
        
        return context
    
    def _send_message_to_ai(self, message):
        """Send message to AI and get response"""
        try:
            # Mark session as in use
            if self.session_id:
                self.browser_manager.use_session(self.session_id)
            
            # Find and use input field
            input_field = self.driver.find_element(By.CSS_SELECTOR, "[role='textbox']")
            input_field.clear()
            input_field.send_keys(message)
            input_field.send_keys(Keys.RETURN)
            
            # Wait for response
            response = self._wait_for_response()
            return response
            
        except Exception as e:
            logger.error(f"Message sending failed: {str(e)}")
            raise
    
    def _wait_for_response(self):
        """Wait for AI response to complete"""
        try:
            last_text = ""
            stable_count = 0
            max_wait = 30
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    message_contents = self.driver.find_elements(By.TAG_NAME, "message-content")
                    if not message_contents:
                        time.sleep(0.1)
                        continue
                        
                    last_message = message_contents[-1]
                    divs = last_message.find_elements(By.TAG_NAME, "div")
                    if not divs:
                        time.sleep(0.1)
                        continue
                        
                    div = divs[0]
                    p_tags = div.find_elements(By.TAG_NAME, "p")
                    if p_tags:
                        result_text = "\n".join([p.text for p in p_tags])
                        
                        if result_text == last_text:
                            stable_count += 1
                        else:
                            stable_count = 0
                            last_text = result_text
                            
                        if stable_count >= 5:  # Text stable for ~0.5 seconds
                            return result_text
                            
                except StaleElementReferenceException:
                    # Element changed, continue waiting
                    pass
                    
                time.sleep(0.1)
            
            # Timeout - return what we have
            return last_text if last_text else "I'm sorry, I couldn't generate a response. Please try again."
            
        except Exception as e:
            logger.error(f"Response waiting failed: {str(e)}")
            return "I'm having trouble responding right now. Please try again."
    
    def close_session(self):
        """Close the chatbot session"""
        if self.session_id:
            self.browser_manager.close_session(self.session_id)
            self.session_id = None
            self.driver = None
            self.context_initialized = False
