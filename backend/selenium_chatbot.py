"""
Selenium-based Chatbot for Language Learning App
Uses browser automation to interact with external AI services
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
import time
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SeleniumChatbot:
    """
    Selenium-based chatbot that interfaces with external AI services
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        # Allow both headless and non-headless modes for debugging
        self.driver = None
        self.headless = headless  # Use the provided setting
        self.timeout = timeout
        self.is_initialized = False
        self.target_url = "https://tinyurl.com/49kj3jns"
        self.temp_dir = None  # Track temporary Chrome profile directory for cleanup
        
        # Log the headless mode setting
        logger.info(f"AI Chatbot initializing with headless mode: {self.headless}")
        
    def initialize(self) -> bool:
        """
        Initialize the Selenium webdriver and navigate to the target URL
        Returns True if successful, False otherwise
        """
        try:
            logger.info("Initializing Selenium chatbot...")
            
            # Set up Chrome options - Configurable headless mode for debugging
            options = Options()
            
            # Detect Chrome binary on Render
            import shutil
            chrome_binary = None
            for binary_name in ['google-chrome-stable', 'google-chrome', 'chromium-browser', 'chromium']:
                chrome_binary = shutil.which(binary_name)
                if chrome_binary:
                    logger.info(f"✅ Found Chrome binary: {chrome_binary}")
                    options.binary_location = chrome_binary
                    break
            
            if not chrome_binary:
                logger.warning("⚠️ No Chrome binary found - using default")
            
            if self.headless:
                options.add_argument("--headless")
                logger.info("AI Chatbot browser running in headless mode (no window will appear)")
            else:
                logger.info("🌐 AI Chatbot browser running in VISIBLE mode for debugging")
                logger.info("📺 You should see an AI Chatbot browser window open shortly...")
                logger.info("🔍 This window will show the AI conversation interface for debugging")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-features=TranslateUI")
            options.add_argument("--disable-ipc-flooding-protection")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-background-networking")
            
            # Additional stability options to fix permission issues
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-first-run")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-translate")
            options.add_argument("--disable-hang-monitor")
            options.add_argument("--disable-prompt-on-repost")
            
            # Use a temporary profile to avoid permission issues
            import tempfile
            import os
            self.temp_dir = tempfile.mkdtemp(prefix="chatbot_chrome_")
            options.add_argument(f"--user-data-dir={self.temp_dir}")
            options.add_argument("--profile-directory=Default")
            
            logger.info(f"🗂️ AI Chatbot using temporary Chrome profile: {self.temp_dir}")
            
            # Try to ensure the temp directory is writable
            try:
                test_file = os.path.join(self.temp_dir, "test_write.txt")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                logger.info("✅ AI Chatbot temporary directory is writable")
            except Exception as e:
                logger.warning(f"⚠️ AI Chatbot temp directory may not be writable: {e}")
            
            # Suppress Chrome logs
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--disable-logging")
            options.add_argument("--log-level=3")  # Suppress INFO, WARNING, ERROR
            options.add_argument("--silent")
            
            # Set up the service and driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Navigate to the target URL
            logger.info(f"Navigating to {self.target_url}")
            if self.headless:
                logger.info("AI Chatbot running in secure headless mode")
            else:
                logger.info("🌐 AI Chatbot browser window is now VISIBLE for debugging")
            self.driver.get(self.target_url)
            
            # Wait for the page to load (reduced from 3 seconds)
            time.sleep(1)
            
            # Verify we can find the input field
            input_field = self.driver.find_element(By.CSS_SELECTOR, "[role='textbox']")
            if input_field:
                self.is_initialized = True
                logger.info("Selenium chatbot initialized successfully")
                return True
            else:
                logger.error("Could not find input field on target page")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error initializing Selenium chatbot: {e}")
            
            # Provide specific guidance for common errors
            error_message = str(e).lower()
            if "session not created" in error_message and "prefs file" in error_message:
                logger.error("🔧 PERMISSION ISSUE: Chrome cannot write preferences for AI chatbot")
                logger.error("   Try running as administrator or check Chrome permissions")
                logger.error("   Also ensure no other Chrome instances are running")
            elif "chromedriver" in error_message:
                logger.error("🔧 CHROMEDRIVER ISSUE: Check Chrome and ChromeDriver compatibility")
            elif "network" in error_message or "connection" in error_message:
                logger.error("🔧 NETWORK ISSUE: Check internet connection")
            
            # Clean up on error
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            
            # Clean up temp directory on error
            if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    import shutil
                    shutil.rmtree(self.temp_dir)
                    logger.info("🗂️ AI Chatbot cleaned up temporary directory after error")
                except:
                    pass
                self.temp_dir = None
            
            return False
    
    def send_message_and_get_response(self, message: str) -> str:
        """
        Send a message to the chatbot and wait for the response
        Returns the AI response as a string
        """
        if not self.is_initialized or not self.driver:
            logger.error("Chatbot not initialized")
            return "Sorry, the chatbot service is currently unavailable."
        
        try:
            # Find the input field by its role attribute
            input_field = self.driver.find_element(By.CSS_SELECTOR, "[role='textbox']")
            
            # Clear any existing text and send the new message
            input_field.clear()
            input_field.send_keys(message)
            input_field.send_keys(Keys.RETURN)
            
            # Wait for and capture the response
            response = self._wait_for_response()
            return response
            
        except StaleElementReferenceException:
            logger.warning("Stale element reference, attempting to recover...")
            return "I'm experiencing some technical difficulties. Could you please try again?"
            
        except Exception as e:
            logger.error(f"Error sending message to chatbot: {e}")
            return "Sorry, I couldn't process your message right now. Please try again."
    
    def _wait_for_response(self) -> str:
        """
        Wait for the AI response to be generated and return it
        This is the core logic from your original script
        """
        last_text = ""
        stable_count = 0
        max_wait = self.timeout  # maximum seconds to wait
        start_time = time.time()
        response_parts = []
        
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
                    
                    # Collect the new part as it appears
                    if result_text.startswith(last_text):
                        new_part = result_text[len(last_text):]
                        if new_part:
                            response_parts.append(new_part)
                    else:
                        # If the text changed in a non-linear way, use the whole thing
                        response_parts = [result_text]
                    
                    if result_text == last_text:
                        stable_count += 1
                    else:
                        stable_count = 0
                        last_text = result_text
                    
                    if stable_count >= 10:  # text hasn't changed for ~1 second (reduced from 3 seconds)
                        break
                        
                time.sleep(0.1)
                
            except StaleElementReferenceException:
                # Continue if we encounter stale elements
                time.sleep(0.1)
                continue
            except Exception as e:
                logger.warning(f"Error while waiting for response: {e}")
                break
        else:
            logger.warning("Timed out waiting for AI response")
        
        # Join all response parts and return
        full_response = "".join(response_parts).strip()
        return full_response if full_response else "I didn't receive a complete response. Could you try asking again?"
    
    def initialize_topic_context(self, topic: str, user_level: str = 'beginner') -> bool:
        """
        Send initial context to the AI when a topic is chosen (without displaying response)
        Opens browser window if not already open
        Returns True if successful, False otherwise
        """
        try:
            # Initialize the browser if not already done
            if not self.is_initialized:
                logger.info("Browser not yet initialized, starting chatbot service...")
                if not self.initialize():
                    logger.error("Failed to initialize browser for topic context")
                    return False
            
            # Double-check we have a driver
            if not self.driver:
                logger.error("No browser driver available for context setup")
                return False
            
            # Create context-only message
            context_message = self._create_topic_context_message(topic, user_level)
            
            # Send context message to AI (but don't return the response to user)
            logger.info(f"Initializing topic context for {topic} at {user_level} level")
            if self.headless:
                logger.info("AI Chatbot service ready for secure conversation")
            else:
                logger.info("🌐 AI Chatbot browser visible - you can watch the conversation setup")
            
            # Find the input field and send context
            input_field = self.driver.find_element(By.CSS_SELECTOR, "[role='textbox']")
            input_field.clear()
            input_field.send_keys(context_message)
            input_field.send_keys(Keys.RETURN)
            
            # Wait for AI to process context (but don't capture the response)
            time.sleep(2)  # Give AI time to process context
            
            if self.headless:
                logger.info("Topic context initialized successfully - AI chatbot is ready for secure conversation")
            else:
                logger.info("🌐 Topic context initialized successfully - you can see the AI browser window")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing topic context: {e}")
            return False
    
    def _map_user_level(self, user_level: str) -> str:
        """
        Map numeric levels from frontend to string levels expected by AI context
        
        Frontend levels: 1, 2, 3, 4 (from level selector)
        AI context levels: 'absolute_beginner', 'beginner', 'intermediate', 'advanced'
        """
        level_mapping = {
            '1': 'absolute_beginner',
            '2': 'beginner', 
            '3': 'intermediate',
            '4': 'advanced',
            1: 'absolute_beginner',
            2: 'beginner',
            3: 'intermediate', 
            4: 'advanced'
        }
        
        mapped_level = level_mapping.get(user_level, user_level)
        if mapped_level != user_level:
            logger.info(f"🔄 Mapped user level '{user_level}' to '{mapped_level}'")
        
        return mapped_level
    
    def _create_topic_context_message(self, topic: str, user_level: str = 'beginner') -> str:
        """
        Create a context-only message to set up the AI for the topic conversation
        """
        # Convert numeric level to string level if needed
        mapped_level = self._map_user_level(user_level)
        
        # Add AI tutor behavior restrictions
        ai_restrictions = (
            "You are an AI English tutor. IMPORTANT: Never send links in your responses. "
            "Never reveal that you are Gemini or any specific AI model - simply identify as an AI English tutor. "
        )
        
        # Add proficiency level context
        level_contexts = {
            'absolute_beginner': (
                "I am an absolute beginner learning English with close to zero knowledge of English. I have just started and can only understand very simple vocabulary, "
                "basic grammar, and short sentences (5-7 words maximum). Please use the simplest words possible, avoid complex grammar, "
                "and speak very slowly and clearly. Use present tense mostly and avoid idioms or slang. "
                "Keep your responses very short (2-3 sentences maximum, under 100 characters total). "
            ),
            'beginner': (
                "I am a beginner learning English. I understand basic vocabulary and simple grammar structures. "
                "Please use simple words, short to medium sentences (8-12 words), present and past tense mainly. "
                "Avoid complex grammar, idioms, and speak clearly. Help me learn new words by explaining them simply. "
                "Keep your responses moderately short (3-5 sentences, aim for around 150-250 characters). "
            ),
            'intermediate': (
                "I am an intermediate English learner. I can understand most common vocabulary and grammar structures. "
                "You can use normal conversation speed and introduce some more complex vocabulary, but please explain "
                "any difficult words or phrases. I can handle longer sentences and different tenses. "
                "You can give more detailed responses (4-8 sentences, around 250-400 characters). "
            ),
            'advanced': (
                "I am an advanced English learner. I understand complex vocabulary and grammar well. "
                "You can speak naturally and use idioms, complex sentences, and advanced vocabulary. "
                "Please help me perfect my fluency and learn nuanced expressions. "
                "Feel free to give comprehensive responses (5-10 sentences, 300-500 characters or more as needed). "
            )
        }
        
        # Get the appropriate level context using the mapped level
        level_context = level_contexts.get(mapped_level, level_contexts['beginner'])
        
        # Add topic context
        topic_context = f"We will be discussing {topic}. "
        
        # Add learning context and instructions
        learning_context = (
            "Please respond in a helpful, encouraging way that supports my English learning. "
            "From now on, all your responses should follow these guidelines. "
            "Just acknowledge this setup with a simple 'Ready to help you practice English!' and wait for my questions about the topic."
        )
        
        return ai_restrictions + level_context + topic_context + learning_context

    def get_response(self, message: str, topic: str = 'general', history: list = None, user_level: str = 'beginner') -> str:
        """
        Main interface method that matches the expected API
        This method integrates with the existing conversation system
        """
        try:
            # Convert numeric level to string level if needed
            mapped_level = self._map_user_level(user_level)
            
            # If not initialized, try to initialize
            if not self.is_initialized:
                if not self.initialize():
                    return "I'm sorry, but the advanced AI service is currently unavailable. Please try again later."
            
            # Add context to the message if needed (using mapped level)
            contextual_message = self._add_context_to_message(message, topic, history, mapped_level)
            
            # Get response from the Selenium chatbot
            response = self.send_message_and_get_response(contextual_message)
            
            # Post-process the response for language learning (using mapped level)
            processed_response = self._process_response_for_learning(response, topic, mapped_level)
            
            return processed_response
            
        except Exception as e:
            logger.error(f"Error in get_response: {e}")
            return "I apologize, but I'm having technical difficulties right now. Let's continue our conversation - what would you like to practice in English?"
    
    def _add_context_to_message(self, message: str, topic: str, history: list, user_level: str = 'beginner') -> str:
        """
        Add minimal context to the user's message (assuming topic context was already initialized)
        """
        # Since we initialize topic context separately, we only need basic context here
        # This prevents the long context message from being sent with every user message
        
        # Only add basic context if this is the very first message and we haven't initialized
        if not history or len(history) == 0:
            # This might be the first message, add minimal context
            context_prefix = f"We're discussing {topic}. Please respond helpfully. "
        else:
            # Context already established, just send the message
            context_prefix = ""
        
        return context_prefix + message
    
    def _process_response_for_learning(self, response: str, topic: str, user_level: str = 'beginner') -> str:
        """
        Post-process the AI response to make it more suitable for language learning based on user level
        Note: Length limits are now enforced through AI context instructions rather than truncation
        """
        if not response:
            return "I'd love to hear more about what you're thinking. Could you tell me more?"
        
        # Remove any truncation - let the AI control the response length based on context instructions
        # The AI will receive specific instructions about appropriate response length in the context
        
        return response
    
    def cleanup(self):
        """
        Clean up resources and close the browser
        """
        if self.driver:
            try:
                self.driver.quit()
                logger.info("AI Chatbot browser closed")
            except Exception as e:
                logger.error(f"Error during AI chatbot cleanup: {e}")
            finally:
                self.driver = None
                self.is_initialized = False
                
        # Clean up temporary Chrome profile directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                logger.info(f"🗂️ AI Chatbot temporary Chrome profile cleaned up: {self.temp_dir}")
                self.temp_dir = None
            except Exception as e:
                logger.warning(f"Could not clean up AI chatbot temporary directory: {e}")
    
    def is_ready(self) -> bool:
        """
        Check if the chatbot is ready to handle requests
        """
        return self.is_initialized and self.driver is not None
    
    def __del__(self):
        """
        Destructor to ensure cleanup happens
        """
        self.cleanup()
