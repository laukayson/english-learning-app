"""
Web-based Speech-to-Text Service using SpeechTexter
Uses Selenium to interact with SpeechTexter's voice input feature
Provides unlimited STT without API costs or limits
"""

import logging
import time
import tempfile
import os
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class SpeechTexterSTT:
    """
    Speech-to-Text service using SpeechTexter's voice input
    """
    
    def __init__(self, headless: bool = False, timeout: int = 30):
        self.driver = None
        self.headless = headless
        self.timeout = timeout
        self.is_initialized = False
        self.speechtexter_url = "https://tinyurl.com/3wvyuhzs"
        self.is_recording = False
        self.current_text = ""
        self.temp_dir = None  # Track temporary Chrome profile directory for cleanup
        
        # Selectors for SpeechTexter microphone button
        self.mic_button_selectors = [
            '#mic-outer-div',  # Primary selector you provided
            'div[id="mic-outer-div"]',
            '#mic-outer-div button',
            '#mic-outer-div div',
            'div[id*="mic"]',  # Fallback for similar mic containers
            'button[id*="mic"]',  # In case it's a button with mic in ID
            '*[onclick*="mic"]',  # Elements with mic-related onclick handlers
        ]
        
        # Selectors for the text editor output
        self.text_output_selectors = [
            '#textEditor',  # Primary selector you provided
            'div[id="textEditor"]',
            'div.note[contenteditable]',
            'div[contenteditable=""][class="note"]',
            '*[id*="textEditor"]',  # Fallback for similar text editor IDs
            'div[contenteditable="true"]',  # Generic contenteditable div
            '*[contenteditable][class*="note"]',  # Elements with note class and contenteditable
        ]
        
        # Language selector (if needed)
        self.language_selectors = [
            'button[id*="language"]',
            'div[id*="language"]',
            'select[id*="language"]',
            '*[onclick*="language"]'
        ]
    
    def initialize(self) -> bool:
        """
        Initialize the Chrome webdriver and navigate to SpeechTexter
        """
        try:
            logger.info("Initializing SpeechTexter STT service...")
            
            # Set up Chrome options
            options = Options()
            
            # Detect Chrome binary on Render
            import shutil
            chrome_binary = None
            for binary_name in ['google-chrome-stable', 'google-chrome', 'chromium-browser', 'chromium']:
                chrome_binary = shutil.which(binary_name)
                if chrome_binary:
                    logger.info(f"✅ Found Chrome binary for STT: {chrome_binary}")
                    options.binary_location = chrome_binary
                    break
            
            if not chrome_binary:
                logger.warning("⚠️ No Chrome binary found for STT - using default")
            
            if self.headless:
                options.add_argument("--headless")
                logger.info("🔕 SpeechTexter STT browser running in headless mode (no window will appear)")
            else:
                logger.info("🌐 SpeechTexter STT browser running in VISIBLE mode for debugging")
                logger.info("📺 You should see the SpeechTexter browser window open shortly...")
            
            # Essential Chrome options for voice input
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-default-apps")
            
            # Fix permissions and profile issues
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-features=TranslateUI")
            options.add_argument("--disable-ipc-flooding-protection")
            
            # Additional stability options
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-first-run")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-translate")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-hang-monitor")
            options.add_argument("--disable-prompt-on-repost")
            
            # Use a temporary profile to avoid permission issues
            import tempfile
            self.temp_dir = tempfile.mkdtemp(prefix="speechtexter_chrome_")
            options.add_argument(f"--user-data-dir={self.temp_dir}")
            options.add_argument("--profile-directory=Default")
            
            logger.info(f"🗂️ Using temporary Chrome profile: {self.temp_dir}")
            
            # Try to ensure the temp directory is writable
            try:
                test_file = os.path.join(self.temp_dir, "test_write.txt")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                logger.info("✅ Temporary directory is writable")
            except Exception as e:
                logger.warning(f"⚠️ Temp directory may not be writable: {e}")
            
            # Additional permission fixes
            options.add_argument("--no-first-run")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-translate")
            options.add_argument("--disable-background-timer-throttling")
            
            # Allow microphone access without prompting
            options.add_argument("--use-fake-ui-for-media-stream")
            options.add_argument("--allow-running-insecure-content") 
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--autoplay-policy=no-user-gesture-required")
            
            # Set microphone permissions for SpeechTexter (simplified to avoid permission issues)
            prefs = {
                "profile.default_content_setting_values.media_stream_mic": 1,
                "profile.default_content_setting_values.media_stream_camera": 1,
                "profile.default_content_setting_values.notifications": 1,
                "profile.managed_default_content_settings.media_stream_mic": 1
            }
            options.add_experimental_option("prefs", prefs)
            
            # Suppress Chrome logs
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--disable-logging")
            options.add_argument("--log-level=3")
            options.add_argument("--silent")
            
            # Set up the service and driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Navigate to SpeechTexter
            logger.info(f"Navigating to {self.speechtexter_url}")
            if self.headless:
                logger.info("🔕 SpeechTexter STT running in headless mode (no window will appear)")
            else:
                logger.info("🌐 SpeechTexter STT browser window is now VISIBLE for debugging")
                logger.info("📺 You should see the SpeechTexter browser window open...")
                logger.info("🎤 This window will show the speech recognition interface for debugging")
            self.driver.get(self.speechtexter_url)
            
            # Wait for page to load and SpeechTexter to fully initialize
            logger.info("⏳ Waiting for SpeechTexter to fully load...")
            time.sleep(5)  # Give SpeechTexter more time to load and initialize
            
            # Verify we can find essential elements
            if self._find_mic_button() and self._find_text_editor():
                self.is_initialized = True
                logger.info("✅ SpeechTexter STT service initialized successfully")
                return True
            else:
                logger.error("Could not find essential elements on SpeechTexter page")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error initializing SpeechTexter STT: {e}")
            
            # Provide specific guidance for common errors
            error_message = str(e).lower()
            if "session not created" in error_message and "prefs file" in error_message:
                logger.error("🔧 PERMISSION ISSUE: Chrome cannot write preferences")
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
                    logger.info("🗂️ Cleaned up temporary directory after error")
                except:
                    pass
                self.temp_dir = None
            
            return False
    
    def _find_mic_button(self) -> Optional[object]:
        """
        Find the microphone button using multiple selector strategies
        """
        logger.info("🔍 Searching for microphone button...")
        
        for selector in self.mic_button_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                logger.debug(f"Selector '{selector}' found {len(elements)} elements")
                
                for i, element in enumerate(elements):
                    try:
                        # Check if this element is clickable and seems like a mic button
                        if element.is_displayed() and element.is_enabled():
                            # Log element details for debugging
                            tag_name = element.tag_name
                            element_id = element.get_attribute('id')
                            element_class = element.get_attribute('class')
                            element_text = element.text[:50] if element.text else "No text"
                            
                            logger.info(f"✅ Found mic button with selector: {selector}")
                            logger.info(f"   Element {i}: {tag_name} id='{element_id}' class='{element_class}' text='{element_text}'")
                            return element
                        else:
                            logger.debug(f"Element {i} not displayed or enabled")
                    except Exception as e:
                        logger.debug(f"Error checking element {i}: {e}")
            except Exception as e:
                logger.debug(f"Mic button selector {selector} failed: {e}")
                continue
        
        # If no button found, let's see what's actually on the page
        logger.error("❌ Could not find microphone button with any known selector")
        self._debug_page_elements()
        return None
    
    def _find_text_editor(self) -> Optional[object]:
        """
        Find the text editor where transcribed text appears
        """
        logger.info("🔍 Searching for text editor...")
        
        for selector in self.text_output_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    # Log element details for debugging
                    tag_name = element.tag_name
                    element_id = element.get_attribute('id')
                    element_class = element.get_attribute('class')
                    contenteditable = element.get_attribute('contenteditable')
                    
                    logger.info(f"✅ Found text editor with selector: {selector}")
                    logger.info(f"   Element: {tag_name} id='{element_id}' class='{element_class}' contenteditable='{contenteditable}'")
                    return element
            except Exception as e:
                logger.debug(f"Text editor selector {selector} failed: {e}")
                continue
        
        logger.error("❌ Could not find text editor with any known selector")
        self._debug_page_elements()
        return None
    
    def _find_transcribed_text(self) -> str:
        """
        Find and extract transcribed text from the SpeechTexter editor
        """
        logger.debug("🔍 Searching for transcribed text...")
        
        # Track all text found for debugging
        all_found_text = []
        
        # Check the main text editor first
        text_editor = self._find_text_editor()
        if text_editor:
            logger.debug("📝 Checking main text editor...")
            # Try multiple methods to get text content
            methods = [
                ('textContent', lambda: text_editor.get_attribute('textContent')),
                ('innerText', lambda: text_editor.get_attribute('innerText')),
                ('text', lambda: text_editor.text),
                ('value', lambda: text_editor.get_attribute('value')),
            ]
            
            for method_name, method_func in methods:
                try:
                    text = method_func()
                    if text and text.strip():
                        all_found_text.append(f"Main editor ({method_name}): '{text.strip()}'")
                        logger.info(f"✅ Found text using {method_name}: '{text.strip()}'")
                        
                        # If this is the phantom "LEGAL" text, log more details
                        if "legal" in text.lower():
                            logger.warning(f"🚨 PHANTOM 'LEGAL' TEXT DETECTED via {method_name}!")
                            logger.warning(f"   Full text: '{text}'")
                            logger.warning(f"   Element ID: {text_editor.get_attribute('id')}")
                            logger.warning(f"   Element class: {text_editor.get_attribute('class')}")
                            logger.warning(f"   Element visible: {text_editor.is_displayed()}")
                            
                        return text.strip()
                    else:
                        logger.debug(f"Method {method_name}: empty or None")
                except Exception as e:
                    logger.debug(f"Method {method_name} failed: {e}")
            
            # Also try innerHTML and extract text from HTML
            try:
                innerHTML = text_editor.get_attribute('innerHTML')
                logger.debug(f"innerHTML content: '{innerHTML}'")
                if innerHTML and innerHTML.strip():
                    # Simple extraction of text from HTML tags
                    import re
                    # Remove HTML tags and get clean text
                    clean_text = re.sub(r'<[^>]+>', '', innerHTML).strip()
                    # Also handle common HTML entities
                    clean_text = clean_text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
                    if clean_text:
                        all_found_text.append(f"Main editor (innerHTML): '{clean_text}'")
                        logger.info(f"✅ Found text from innerHTML: '{clean_text}'")
                        
                        if "legal" in clean_text.lower():
                            logger.warning(f"🚨 PHANTOM 'LEGAL' TEXT found in innerHTML!")
                            logger.warning(f"   Raw innerHTML: '{innerHTML}'")
                            
                        return clean_text
            except Exception as e:
                logger.debug(f"Error extracting innerHTML: {e}")
        
        # Expanded search: Look for ANY element that might contain transcribed text
        logger.debug("🔍 Scanning entire page for any text content...")
        
        # Check for elements that commonly hold transcribed text
        potential_selectors = [
            # Original selectors
            '#textEditor',
            'div[id="textEditor"]',
            'div.note[contenteditable]',
            'div[contenteditable=""][class="note"]',
            
            # Additional possibilities
            'div[contenteditable="true"]',
            'textarea',
            'input[type="text"]',
            '.transcription',
            '.speech-text',
            '.result',
            '.output',
            '[data-speech]',
            '[data-transcript]',
            
            # Look for any div that might hold text
            'div[contenteditable]',
            'div.text-input',
            'div.speech-input',
            
            # Check common SpeechTexter class patterns
            '.st-text',
            '.speech-result',
            '.voice-text',
        ]
        
        for selector in potential_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for i, element in enumerate(elements):
                    try:
                        # Get element info for debugging
                        elem_id = element.get_attribute('id')
                        elem_class = element.get_attribute('class')
                        elem_displayed = element.is_displayed()
                        
                        # Check multiple text retrieval methods
                        for method_name, method_func in [
                            ('text', lambda: element.text),
                            ('textContent', lambda: element.get_attribute('textContent')),
                            ('innerText', lambda: element.get_attribute('innerText')),
                            ('value', lambda: element.get_attribute('value')),
                            ('innerHTML', lambda: element.get_attribute('innerHTML'))
                        ]:
                            try:
                                text = method_func()
                                if text and text.strip():
                                    # Clean HTML if it's innerHTML
                                    if method_name == 'innerHTML':
                                        import re
                                        text = re.sub(r'<[^>]+>', '', text).strip()
                                        text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
                                    
                                    if text.strip():
                                        source_info = f"{selector}[{i}] using {method_name}"
                                        all_found_text.append(f"{source_info}: '{text.strip()}'")
                                        
                                        logger.info(f"✅ FOUND TEXT in element {source_info}:")
                                        logger.info(f"   Element: id='{elem_id}' class='{elem_class}' visible={elem_displayed}")
                                        logger.info(f"   Text: '{text.strip()}'")
                                        
                                        # Special handling for phantom "LEGAL" text
                                        if "legal" in text.lower():
                                            logger.error(f"🚨 PHANTOM 'LEGAL' TEXT SOURCE IDENTIFIED!")
                                            logger.error(f"   Found in: {source_info}")
                                            logger.error(f"   Element visible in browser: {elem_displayed}")
                                            logger.error(f"   This element may be hidden or contain default/placeholder text")
                                            
                                            # If this element is not visible, skip it
                                            if not elem_displayed:
                                                logger.warning(f"   ⚠️ Skipping invisible element with phantom text")
                                                continue
                                            
                                        return text.strip()
                            except Exception as e:
                                logger.debug(f"Method {method_name} failed on {selector}[{i}]: {e}")
                    except Exception as e:
                        logger.debug(f"Error checking element {i} with selector {selector}: {e}")
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        # Last resort: Check if there's any text change anywhere on the page
        try:
            logger.debug("🔍 Checking entire page body for any text changes...")
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            if page_text and isinstance(page_text, str):
                # Look for recent text that might be transcription
                lines = page_text.split('\n')
                for line in lines[-10:]:  # Check last 10 lines
                    line = line.strip()
                    if line and len(line) > 2:  # Meaningful text
                        # Skip common UI text
                        skip_phrases = ['speech', 'texter', 'microphone', 'record', 'click', 'start', 'stop', 'language']
                        if not any(phrase in line.lower() for phrase in skip_phrases):
                            all_found_text.append(f"Page body: '{line}'")
                            logger.info(f"🔍 Potential transcription found in page body: '{line}'")
                            
                            if "legal" in line.lower():
                                logger.error(f"🚨 PHANTOM 'LEGAL' TEXT found in page body!")
                                
                            return line
        except Exception as e:
            logger.debug(f"Error checking page body: {e}")
        
        # Log summary of all text found for debugging
        if all_found_text:
            logger.warning(f"📋 SUMMARY: Found {len(all_found_text)} text sources:")
            for i, text_info in enumerate(all_found_text[:5]):  # Limit to first 5
                logger.warning(f"   {i+1}. {text_info}")
        else:
            logger.info("✅ No text found anywhere on the page")
        
        logger.warning("❌ No transcribed text found anywhere on the page")
        return ""
    
    def _debug_page_elements(self):
        """
        Debug method to see what elements are actually on the page
        """
        try:
            logger.info("🔍 Debugging page elements...")
            
            # Get page title and URL
            title = self.driver.title
            url = self.driver.current_url
            logger.info(f"📄 Page title: '{title}'")
            logger.info(f"🌐 Current URL: {url}")
            
            # Look for any elements with 'mic' in their attributes
            mic_elements = self.driver.find_elements(By.XPATH, "//*[contains(@id, 'mic') or contains(@class, 'mic') or contains(text(), 'mic')]")
            logger.info(f"🎤 Found {len(mic_elements)} elements containing 'mic':")
            for i, elem in enumerate(mic_elements[:5]):  # Limit to first 5
                try:
                    tag = elem.tag_name
                    elem_id = elem.get_attribute('id')
                    elem_class = elem.get_attribute('class')
                    elem_text = elem.text[:30] if elem.text else "No text"
                    logger.info(f"   {i+1}. {tag} id='{elem_id}' class='{elem_class}' text='{elem_text}'")
                except:
                    pass
            
            # Look for contenteditable elements
            editable_elements = self.driver.find_elements(By.CSS_SELECTOR, "[contenteditable]")
            logger.info(f"📝 Found {len(editable_elements)} contenteditable elements:")
            for i, elem in enumerate(editable_elements[:3]):  # Limit to first 3
                try:
                    tag = elem.tag_name
                    elem_id = elem.get_attribute('id')
                    elem_class = elem.get_attribute('class')
                    logger.info(f"   {i+1}. {tag} id='{elem_id}' class='{elem_class}'")
                except:
                    pass
            
            # Look for buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            logger.info(f"🔘 Found {len(buttons)} button elements:")
            for i, btn in enumerate(buttons[:5]):  # Limit to first 5
                try:
                    btn_id = btn.get_attribute('id')
                    btn_class = btn.get_attribute('class')
                    btn_text = btn.text[:30] if btn.text else "No text"
                    logger.info(f"   {i+1}. button id='{btn_id}' class='{btn_class}' text='{btn_text}'")
                except:
                    pass
                    
            # Check if we're on the right page
            if 'speechtexter' not in url.lower():
                logger.error(f"❌ Not on SpeechTexter page! Current URL: {url}")
                logger.info("🔄 Attempting to navigate to SpeechTexter...")
                self.driver.get(self.speechtexter_url)
                time.sleep(3)
                
        except Exception as e:
            logger.error(f"Error during page debugging: {e}")
    
    def start_recording(self, language_code: str = 'en') -> Dict[str, Any]:
        """
        Start voice recording using SpeechTexter
        This corresponds to pressing and holding the microphone button in the app
        """
        if not self.is_initialized or not self.driver:
            return {
                'success': False,
                'message': 'SpeechTexter STT service not initialized',
                'recording': False
            }
        
        if self.is_recording:
            return {
                'success': True,
                'message': 'Recording already in progress',
                'recording': True
            }
        
        try:
            logger.info("🎤 Starting SpeechTexter recording...")
            
            # Ensure we're on the right page
            current_url = self.driver.current_url
            if 'speechtexter' not in current_url.lower():
                logger.info("🔄 Navigating back to SpeechTexter...")
                self.driver.get(self.speechtexter_url)
                time.sleep(3)
            
            # COMPREHENSIVE TEXT CLEARING - Clear any phantom text
            logger.info("🧹 Performing comprehensive text clearing...")
            
            # Method 1: Clear all contenteditable elements
            editable_elements = self.driver.find_elements(By.CSS_SELECTOR, "[contenteditable]")
            logger.info(f"📝 Found {len(editable_elements)} contenteditable elements to clear")
            for i, element in enumerate(editable_elements):
                try:
                    # Check what text is currently in this element
                    current_text = element.get_attribute('textContent') or element.text or ""
                    if current_text.strip():
                        logger.info(f"🧹 Clearing element {i}: '{current_text.strip()}'")
                    
                    # Multiple clearing methods
                    self.driver.execute_script("arguments[0].innerHTML = '';", element)
                    self.driver.execute_script("arguments[0].textContent = '';", element)
                    element.clear()
                    
                    # Verify it's cleared
                    after_text = element.get_attribute('textContent') or element.text or ""
                    if after_text.strip():
                        logger.warning(f"⚠️ Element {i} still has text after clearing: '{after_text.strip()}'")
                        # Force clear with more aggressive method
                        self.driver.execute_script("""
                            arguments[0].innerHTML = '';
                            arguments[0].textContent = '';
                            arguments[0].innerText = '';
                            arguments[0].value = '';
                        """, element)
                    else:
                        logger.debug(f"✅ Element {i} successfully cleared")
                        
                except Exception as e:
                    logger.debug(f"Error clearing element {i}: {e}")
            
            # Method 2: Specifically target the main text editor
            text_editor = self._find_text_editor()
            if text_editor:
                try:
                    # Check what's in the text editor before clearing
                    before_text = text_editor.get_attribute('textContent') or text_editor.text or ""
                    if before_text.strip():
                        logger.info(f"🧹 Main text editor contains: '{before_text.strip()}' - clearing it")
                    
                    # Aggressive clearing of main editor
                    self.driver.execute_script("""
                        var element = arguments[0];
                        element.innerHTML = '';
                        element.textContent = '';
                        element.innerText = '';
                        if (element.value !== undefined) element.value = '';
                        // Trigger any change events
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                    """, text_editor)
                    
                    # Verify main editor is cleared
                    after_text = text_editor.get_attribute('textContent') or text_editor.text or ""
                    if after_text.strip():
                        logger.error(f"❌ Main text editor STILL has text: '{after_text.strip()}'")
                    else:
                        logger.info("✅ Main text editor successfully cleared")
                        
                    # Highlight the text editor for visual confirmation
                    if not self.headless:
                        try:
                            self.driver.execute_script("""
                                arguments[0].style.border = '3px solid blue';
                                arguments[0].style.backgroundColor = '#e6f3ff';
                            """, text_editor)
                            logger.info("🔵 Text editor highlighted in blue")
                        except Exception as e:
                            logger.debug(f"Could not highlight text editor: {e}")
                except Exception as e:
                    logger.error(f"Error clearing main text editor: {e}")
            
            # Method 3: Clear any hidden or alternative text containers
            alternative_selectors = [
                'textarea', 'input[type="text"]', '.speech-text', '.transcription', 
                '.result', '.output', '[data-speech]', '[data-transcript]'
            ]
            for selector in alternative_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        try:
                            current_text = element.get_attribute('value') or element.get_attribute('textContent') or element.text or ""
                            if current_text.strip():
                                logger.info(f"🧹 Clearing {selector}: '{current_text.strip()}'")
                                element.clear()
                                self.driver.execute_script("arguments[0].value = ''; arguments[0].textContent = '';", element)
                        except:
                            pass
                except:
                    pass
            
            # Wait for clearing to take effect
            time.sleep(1)
            
            # FINAL VERIFICATION: Check if any text remains anywhere
            logger.info("🔍 Final verification - checking for any remaining text...")
            remaining_text = self._find_transcribed_text()
            if remaining_text.strip():
                logger.error(f"❌ WARNING: Text still found after clearing: '{remaining_text.strip()}'")
                logger.error("This could be phantom text that will interfere with new transcriptions!")
            else:
                logger.info("✅ All text successfully cleared")
            
            # Find and click the microphone button to start recording
            mic_button = self._find_mic_button()
            if not mic_button:
                return {
                    'success': False,
                    'message': 'Could not find microphone button on SpeechTexter page',
                    'recording': False
                }
            
            # Check if the mic button is clickable
            if not (mic_button.is_enabled() and mic_button.is_displayed()):
                return {
                    'success': False,
                    'message': 'Microphone button found but not clickable',
                    'recording': False
                }
            
            # Click the microphone button to start recording
            logger.info("🎤 Clicking microphone button to start recording...")
            mic_button.click()
            logger.info("✅ Microphone button clicked - recording started")
            
            # Highlight the microphone button for visual confirmation
            if not self.headless:
                try:
                    self.driver.execute_script("""
                        arguments[0].style.border = '3px solid red';
                        arguments[0].style.boxShadow = '0 0 10px red';
                    """, mic_button)
                    logger.info("🔴 Microphone button highlighted in red - recording active")
                except Exception as e:
                    logger.debug(f"Could not highlight mic button: {e}")
            
            # Wait a moment and check if any phantom text appears immediately
            time.sleep(1)
            immediate_text = self._find_transcribed_text()
            if immediate_text.strip():
                logger.warning(f"⚠️ PHANTOM TEXT detected immediately after clicking mic: '{immediate_text.strip()}'")
                # Clear it again
                if text_editor:
                    self.driver.execute_script("arguments[0].innerHTML = ''; arguments[0].textContent = '';", text_editor)
                    logger.info("🧹 Cleared phantom text")
            
            self.is_recording = True
            self.current_text = ""
            
            return {
                'success': True,
                'message': 'Recording started successfully',
                'recording': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error starting SpeechTexter recording: {e}")
            return {
                'success': False,
                'message': f'Failed to start recording: {str(e)}',
                'recording': False
            }
    
    def stop_recording(self) -> Dict[str, Any]:
        """
        Stop voice recording and get the transcribed text
        This corresponds to releasing the microphone button in the app
        """
        if not self.is_initialized or not self.driver:
            logger.error("❌ STT service not initialized when trying to stop recording")
            return {
                'success': False,
                'text': '',
                'message': 'SpeechTexter STT service not initialized',
                'recording': False
            }
        
        if not self.is_recording:
            logger.warning(f"⚠️ No recording in progress when stop_recording called. Current state: is_recording={self.is_recording}")
            logger.info("🔍 This might happen if:")
            logger.info("   1. Recording was never started")
            logger.info("   2. Service was restarted/reinitialized")
            logger.info("   3. Browser was closed or refreshed")
            logger.info("   4. Recording was already stopped")
            
            # Try to detect the actual state
            if self.driver:
                try:
                    url = self.driver.current_url
                    title = self.driver.title
                    logger.info(f"🌐 Current browser state: URL={url}, Title='{title}'")
                    
                    # Check if we can find the mic button and if it's in recording state
                    mic_button = self._find_mic_button()
                    if mic_button:
                        logger.info("🎤 Microphone button found - attempting to stop anyway")
                        # Try to click the mic button to stop any potential recording
                        mic_button.click()
                        time.sleep(0.5)
                    else:
                        logger.error("❌ Cannot find microphone button")
                        
                except Exception as e:
                    logger.error(f"Error checking browser state: {e}")
            
            return {
                'success': False,
                'text': '',
                'message': 'No recording in progress',
                'recording': False,
                'debug_info': {
                    'is_initialized': self.is_initialized,
                    'driver_exists': self.driver is not None,
                    'is_recording_flag': self.is_recording
                }
            }
        
        try:
            logger.info("⏹️ Stopping SpeechTexter recording...")
            
            # Click the microphone button again to stop recording
            mic_button = self._find_mic_button()
            if mic_button:
                mic_button.click()
                logger.info("⏹️ Microphone button clicked - recording stopped")
                
                # Remove highlighting
                if not self.headless:
                    try:
                        self.driver.execute_script("""
                            arguments[0].style.border = '';
                            arguments[0].style.boxShadow = '';
                        """, mic_button)
                        logger.info("🔴 Microphone button highlighting removed")
                    except Exception as e:
                        logger.debug(f"Could not remove mic button highlighting: {e}")
            else:
                logger.error("❌ Could not find microphone button to stop recording")
            
            # Wait a moment for transcription to finalize
            time.sleep(0.5)
            
            # Get the transcribed text
            final_text = self._find_transcribed_text()
            
            # Reset recording state
            self.is_recording = False
            self.current_text = final_text
            
            if final_text and final_text.strip():
                logger.info(f"✅ SpeechTexter transcription: '{final_text}'")
                
                # Filter out "LEGAL" (all caps) - common SpeechTexter glitch
                if final_text.strip() == 'LEGAL':
                    logger.warning("🚫 Filtered out 'LEGAL' transcription - treating as no speech detected")
                    return {
                        'success': False,
                        'text': '',
                        'message': 'No speech detected (filtered)',
                        'recording': False
                    }
                
                return {
                    'success': True,
                    'text': final_text.strip(),
                    'transcription': final_text.strip(),
                    'confidence': 0.9,
                    'language': 'en',
                    'service': 'speechtexter',
                    'message': 'Recording stopped and text transcribed successfully',
                    'recording': False
                }
            else:
                logger.warning("⚠️ Recording stopped but no speech was detected")
                return {
                    'success': False,
                    'text': '',
                    'message': 'Recording stopped but no speech was detected',
                    'recording': False
                }
                
        except Exception as e:
            logger.error(f"❌ Error stopping SpeechTexter recording: {e}")
            self.is_recording = False
            return {
                'success': False,
                'text': '',
                'message': f'Failed to stop recording: {str(e)}',
                'recording': False
            }
    
    def get_current_text(self) -> str:
        """
        Get the current transcribed text without stopping recording
        Useful for real-time transcription display
        """
        if not self.is_recording:
            return self.current_text
        
        try:
            current_text = self._find_transcribed_text()
            self.current_text = current_text
            return current_text
        except Exception as e:
            logger.debug(f"Error getting current text: {e}")
            return self.current_text
    
    def is_recording_active(self) -> bool:
        """
        Check if recording is currently active
        """
        return self.is_recording
    
    def transcribe_speech_from_microphone(self, language_code: str = 'en', timeout: int = 10) -> Dict[str, Any]:
        """
        DEPRECATED: Use start_recording() and stop_recording() instead for better control
        
        Start voice recording using SpeechTexter, wait for speech, and return transcription
        NOTE: Browser window stays open between recordings for better user experience
        """
        logger.warning("⚠️ transcribe_speech_from_microphone is deprecated. Use start_recording() and stop_recording() instead.")
        
        # Use the new methods for backward compatibility
        start_result = self.start_recording(language_code)
        if not start_result['success']:
            return {
                'success': False,
                'text': '',
                'error': 'RECORDING_START_FAILED',
                'message': start_result['message']
            }
        
        # Wait for the specified timeout
        logger.info(f"🎧 Listening for speech (timeout: {timeout} seconds)...")
        time.sleep(timeout)
        
        # Stop recording and get result
        stop_result = self.stop_recording()
        return stop_result
    
    def cleanup(self, force_close: bool = False):
        """
        Clean up resources and close the browser
        By default, keeps browser open for better user experience
        Set force_close=True to actually close the browser
        """
        if self.driver and force_close:
            try:
                self.driver.quit()
                logger.info("🚪 SpeechTexter STT browser closed")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            finally:
                self.driver = None
                self.is_initialized = False
                
                # Clean up temporary Chrome profile directory
                if self.temp_dir and os.path.exists(self.temp_dir):
                    try:
                        import shutil
                        shutil.rmtree(self.temp_dir)
                        logger.info(f"🗂️ Temporary Chrome profile cleaned up: {self.temp_dir}")
                        self.temp_dir = None
                    except Exception as e:
                        logger.warning(f"Could not clean up temporary directory: {e}")
        elif self.driver:
            logger.info("🌐 SpeechTexter browser window kept open for next recording")
    
    def force_cleanup(self):
        """
        Force close the browser (for app shutdown)
        """
        self.cleanup(force_close=True)
    
    def test_page_elements(self) -> Dict[str, Any]:
        """
        Test method to check if we can find essential elements
        """
        if not self.is_initialized or not self.driver:
            return {
                'success': False,
                'error': 'Service not initialized'
            }
        
        result = {
            'success': True,
            'url': self.driver.current_url,
            'title': self.driver.title,
            'mic_button_found': False,
            'text_editor_found': False,
            'mic_button_details': None,
            'text_editor_details': None,
            'page_elements_debug': []
        }
        
        # Test mic button
        mic_button = self._find_mic_button()
        if mic_button:
            result['mic_button_found'] = True
            result['mic_button_details'] = {
                'tag': mic_button.tag_name,
                'id': mic_button.get_attribute('id'),
                'class': mic_button.get_attribute('class'),
                'displayed': mic_button.is_displayed(),
                'enabled': mic_button.is_enabled()
            }
        
        # Test text editor
        text_editor = self._find_text_editor()
        if text_editor:
            result['text_editor_found'] = True
            result['text_editor_details'] = {
                'tag': text_editor.tag_name,
                'id': text_editor.get_attribute('id'),
                'class': text_editor.get_attribute('class'),
                'contenteditable': text_editor.get_attribute('contenteditable')
            }
        
        return result
    
    def is_ready(self) -> bool:
        """
        Check if the service is ready to use
        """
        return self.is_initialized and self.driver is not None
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get current service status
        """
        return {
            'service': 'SpeechTexter STT',
            'ready': self.is_ready(),
            'headless': self.headless,
            'initialized': self.is_initialized,
            'cost': 'completely free',
            'website': 'SpeechTexter.com',
            'features': {
                'microphone_input': True,
                'audio_file_input': False,
                'multiple_languages': True,  # SpeechTexter supports 70+ languages
                'unlimited_usage': True,
                'no_api_limits': True,
                'real_time_transcription': True
            },
            'supported_languages': [
                'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 'ar', 'hi', 'fa',
                'and 60+ more languages supported by SpeechTexter'
            ]
        }
    
    def __del__(self):
        """
        Destructor to ensure cleanup happens when service is destroyed
        """
        self.force_cleanup()


class WebSTTService:
    """
    Wrapper service that manages web-based STT options
    """
    
    def __init__(self):
        self.speechtexter_stt = None
        self.ready = False
        self.active_service = None
    
    def initialize(self, headless: bool = False) -> bool:
        """
        Initialize the web-based STT service
        """
        try:
            logger.info("Initializing Web STT Service...")
            
            # Import configuration for separate STT headless setting
            from chatbot_config import ChatbotConfig
            
            # Use the configured STT headless setting (respects user choice)
            stt_headless = ChatbotConfig.STT_HEADLESS
            
            if stt_headless:
                logger.info(f"🔕 STT Service running in headless mode (no browser window)")
            else:
                logger.info(f"🌐 STT Service running in visible mode for debugging")
                logger.info("🔍 SpeechTexter browser window will be VISIBLE")
            
            # Initialize SpeechTexter STT
            self.speechtexter_stt = SpeechTexterSTT(headless=stt_headless)
            if self.speechtexter_stt.initialize():
                self.active_service = 'speechtexter'
                self.ready = True
                
                # Add initialization delay to ensure SpeechTexter is fully loaded
                logger.info("⏳ Waiting for SpeechTexter to fully initialize...")
                time.sleep(3)  # Give SpeechTexter extra time to load properly
                
                visibility_mode = "headless mode" if stt_headless else "visible mode"
                logger.info(f"✅ Web STT Service initialized with SpeechTexter ({visibility_mode})")
                return True
            else:
                logger.error("❌ Failed to initialize SpeechTexter STT")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error initializing Web STT Service: {e}")
            return False
    
    def transcribe_speech(self, language: str = 'en', timeout: int = 10) -> Dict[str, Any]:
        """
        Transcribe speech from microphone
        """
        if not self.ready:
            return {
                'success': False,
                'text': '',
                'error': 'SERVICE_NOT_READY',
                'message': 'Web STT service not initialized'
            }
        
        if self.active_service == 'speechtexter':
            return self.speechtexter_stt.transcribe_speech_from_microphone(language, timeout)
        else:
            return {
                'success': False,
                'text': '',
                'error': 'NO_ACTIVE_SERVICE',
                'message': 'No active STT service available'
            }
    
    def start_recording(self, language: str = 'en') -> Dict[str, Any]:
        """
        Start voice recording - corresponds to pressing and holding microphone button
        """
        if not self.ready:
            return {
                'success': False,
                'message': 'Web STT service not initialized',
                'recording': False
            }
        
        if self.active_service == 'speechtexter':
            return self.speechtexter_stt.start_recording(language)
        else:
            return {
                'success': False,
                'message': 'No active STT service available',
                'recording': False
            }
    
    def stop_recording(self) -> Dict[str, Any]:
        """
        Stop voice recording and get transcribed text - corresponds to releasing microphone button
        """
        if not self.ready:
            return {
                'success': False,
                'text': '',
                'message': 'Web STT service not initialized',
                'recording': False
            }
        
        if self.active_service == 'speechtexter':
            return self.speechtexter_stt.stop_recording()
        else:
            return {
                'success': False,
                'text': '',
                'message': 'No active STT service available',
                'recording': False
            }
    
    def get_current_text(self) -> str:
        """
        Get current transcribed text without stopping recording (for real-time display)
        """
        if not self.ready:
            return ""
        
        if self.active_service == 'speechtexter':
            return self.speechtexter_stt.get_current_text()
        else:
            return ""
    
    def is_recording_active(self) -> bool:
        """
        Check if recording is currently active
        """
        if not self.ready:
            return False
        
        if self.active_service == 'speechtexter':
            return self.speechtexter_stt.is_recording_active()
        else:
            return False
    
    def transcribe_from_flask_file(self, flask_file, language: str = 'en') -> Dict[str, Any]:
        """
        Handle Flask file uploads (not supported by web-based services)
        """
        return {
            'success': False,
            'text': '',
            'error': 'WEB_STT_NO_FILE_SUPPORT',
            'message': 'Web-based STT services do not support audio file uploads. Use microphone input instead.',
            'alternative': 'Use the microphone recording feature in the web interface'
        }
    
    def is_ready(self) -> bool:
        """
        Check if service is ready
        """
        return self.ready
    
    def cleanup(self, force_close: bool = False):
        """
        Clean up all resources
        By default, keeps browser open for better user experience
        """
        if self.speechtexter_stt:
            self.speechtexter_stt.cleanup(force_close=force_close)
            if force_close:
                self.speechtexter_stt = None
                self.ready = False
                self.active_service = None
    
    def force_cleanup(self):
        """
        Force close all browsers (for app shutdown)
        """
        self.cleanup(force_close=True)
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get comprehensive service status
        """
        status = {
            'service': 'Web STT Service',
            'ready': self.ready,
            'active_service': self.active_service,
            'cost': 'completely free',
            'unlimited': True
        }
        
        if self.speechtexter_stt:
            status['speechtexter'] = self.speechtexter_stt.get_service_status()
        
        return status

# Singleton instance
_web_stt_service = None

def get_web_stt_service() -> WebSTTService:
    """Get singleton instance of WebSTTService"""
    global _web_stt_service
    if _web_stt_service is None:
        _web_stt_service = WebSTTService()
    return _web_stt_service
