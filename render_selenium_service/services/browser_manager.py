"""
Browser Manager for Selenium Service
Manages browser instances and sessions efficiently
"""

import time
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import uuid
import psutil
import os

class BrowserManager:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()
        self.max_sessions = 3  # Limit concurrent browsers
        # No timeout needed - Render handles 15-minute idle limit
        
    def create_browser(self, visible=False):
        """Create a new browser instance"""
        options = Options()
        
        if not visible:
            options.add_argument("--headless")
        
        # Render-specific options for containerized environment
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Performance optimizations
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")  # Can be enabled per service
        
        # Memory optimization for Render
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=2048")
        
        try:
            # Use webdriver-manager to automatically handle Chrome installation
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            raise Exception(f"Failed to create browser: {str(e)}")
    
    def get_session(self, service_type="general", create_new=True, reuse_existing=True):
        """Get or create a browser session"""
        with self.lock:
            # Clean up expired sessions first
            self._cleanup_expired_sessions()
            
            # Try to reuse existing session of same type if requested
            if reuse_existing:
                for session_id, session in self.sessions.items():
                    if (session['service_type'] == service_type and 
                        not session['in_use'] and 
                        (time.time() - session['last_used']) < 300):  # Used within 5 minutes
                        session['last_used'] = time.time()
                        return session_id, session['driver']
            
            # Check if we have too many active sessions
            if len(self.sessions) >= self.max_sessions and create_new:
                # Find oldest unused session and close it
                oldest_id = None
                oldest_time = time.time()
                for sid, session in self.sessions.items():
                    if not session['in_use'] and session['created_at'] < oldest_time:
                        oldest_time = session['created_at']
                        oldest_id = sid
                
                if oldest_id:
                    self._close_session(oldest_id)
            
            # Create new session
            if create_new:
                session_id = str(uuid.uuid4())
                driver = self.create_browser()
                
                self.sessions[session_id] = {
                    'driver': driver,
                    'service_type': service_type,
                    'created_at': time.time(),
                    'last_used': time.time(),
                    'in_use': False
                }
                
                return session_id, driver
            
            return None, None
    
    def use_session(self, session_id):
        """Mark session as in use and return driver"""
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session['last_used'] = time.time()
                session['in_use'] = True
                return session['driver']
            return None
    
    def release_session(self, session_id):
        """Mark session as not in use"""
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id]['in_use'] = False
                self.sessions[session_id]['last_used'] = time.time()
    
    def close_session(self, session_id):
        """Close a specific session"""
        with self.lock:
            self._close_session(session_id)
    
    def _close_session(self, session_id):
        """Internal method to close a session"""
        if session_id in self.sessions:
            try:
                self.sessions[session_id]['driver'].quit()
            except:
                pass  # Driver might already be closed
            del self.sessions[session_id]
    
    def _cleanup_expired_sessions(self):
        """Clean up sessions if needed (Render handles idle timeout)"""
        # Render automatically terminates after 15 minutes of inactivity
        # Just clean up any obviously dead sessions
        dead_sessions = []
        
        for session_id, session in self.sessions.items():
            try:
                # Quick check if driver is still responsive
                session['driver'].current_url
            except:
                dead_sessions.append(session_id)
        
        for session_id in dead_sessions:
            self._close_session(session_id)
    
    def cleanup_inactive_sessions(self):
        """Public method to clean up inactive sessions"""
        with self.lock:
            current_time = time.time()
            inactive_sessions = []
            
            for session_id, session in self.sessions.items():
                if not session['in_use'] and (current_time - session['last_used']) > 300:  # 5 minutes
                    inactive_sessions.append(session_id)
            
            for session_id in inactive_sessions:
                self._close_session(session_id)
            
            return len(inactive_sessions)
    
    def get_status(self):
        """Get manager status"""
        with self.lock:
            return {
                'active_sessions': len(self.sessions),
                'max_sessions': self.max_sessions,
                'sessions': {
                    sid: {
                        'service_type': session['service_type'],
                        'created_at': session['created_at'],
                        'last_used': session['last_used'],
                        'in_use': session['in_use']
                    }
                    for sid, session in self.sessions.items()
                }
            }
    
    def get_active_sessions(self):
        """Get count of active sessions"""
        return len(self.sessions)
    
    def get_memory_usage(self):
        """Get memory usage"""
        try:
            process = psutil.Process(os.getpid())
            return {
                'memory_mb': round(process.memory_info().rss / 1024 / 1024, 2),
                'memory_percent': round(process.memory_percent(), 2)
            }
        except:
            return {'memory_mb': 0, 'memory_percent': 0}
    
    def shutdown(self):
        """Shutdown all sessions"""
        with self.lock:
            for session_id in list(self.sessions.keys()):
                self._close_session(session_id)
