from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sqlite3
import json
from datetime import datetime
import logging
import traceback
from functools import wraps
import time
import hashlib
import secrets

# Import PythonAnywhere-specific configuration
from config_pythonanywhere import config

# Import our custom modules
from conversational_ai import ConversationalAI
from translation_service import TranslationService
from voice_service import VoiceService
# from services.image_service import ImageService  # Disabled for PythonAnywhere
from services.progress_tracker import ProgressTracker
from rate_limiter import RateLimiter

# Configure logging for both PythonAnywhere and local development
try:
    # Create logs directory if it doesn't exist
    if os.name == 'nt':  # Windows
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'logs')
        log_file = os.path.join(log_dir, 'app.log')
    else:
        log_dir = '/home/laukayson/englishlearningapp/data/logs'
        log_file = '/home/laukayson/englishlearningapp/data/logs/app.log'
    
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,  # More verbose for debugging
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
except Exception as e:
    # Fallback to console logging only if file logging fails
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        handlers=[logging.StreamHandler()]
    )
logger = logging.getLogger(__name__)

# Password hashing functions
def hash_password(password):
    """Hash a password with salt"""
    salt = secrets.token_hex(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt + pwdhash.hex()

def verify_password(stored_password, provided_password):
    """Verify a password against its hash"""
    salt = stored_password[:64]
    stored_hash = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return stored_hash == pwdhash.hex()

# Initialize Flask app with PythonAnywhere configuration
try:
    app = Flask(__name__)
    app.config.from_object(config['production'])
    
    # Configure CORS for PythonAnywhere
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    
    logger.info("Flask app initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Flask app: {str(e)}")
    # Fallback configuration
    app = Flask(__name__)
    app.config['DATABASE_PATH'] = '/home/laukayson/englishlearningapp/data/db/language_app.db'
    CORS(app)

# Configure static file serving for frontend
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static frontend files"""
    try:
        if os.name == 'nt':  # Windows
            frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        else:
            frontend_dir = '/home/laukayson/englishlearningapp/frontend'
        
        file_path = os.path.join(frontend_dir, filename)
        
        # Security check - make sure we're not serving files outside frontend directory
        if not os.path.commonpath([frontend_dir, file_path]) == frontend_dir:
            return jsonify({'error': 'Invalid file path'}), 400
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_file(file_path)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error serving static file {filename}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/')
def serve_index():
    """Serve the main index.html file"""
    if os.name == 'nt':  # Windows
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    else:
        frontend_dir = '/home/laukayson/englishlearningapp/frontend'
    
    index_path = os.path.join(frontend_dir, 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path)
    else:
        return jsonify({'error': 'Frontend not found'}), 404

# Service availability helper functions
def is_service_available(service):
    """Check if a service is available and properly initialized"""
    return service is not None

def get_translation_service():
    """Get translation service with availability check"""
    if is_service_available(translation_service):
        return translation_service
    return None

def get_voice_service():
    """Get voice service with availability check"""
    if is_service_available(voice_service):
        return voice_service
    return None

def get_progress_tracker():
    """Get progress tracker with availability check"""
    if is_service_available(progress_tracker):
        return progress_tracker
    return None

def get_rate_limiter():
    """Get rate limiter with availability check"""
    if is_service_available(rate_limiter):
        return rate_limiter
    return None

def get_service_details():
    """Get detailed service information for debugging"""
    details = {}
    
    # Check conversational_ai
    try:
        if conversational_ai is not None:
            details['conversational_ai'] = {'status': 'available', 'type': str(type(conversational_ai))}
        else:
            details['conversational_ai'] = {'status': 'unavailable', 'error': 'Service is None'}
    except NameError:
        details['conversational_ai'] = {'status': 'unavailable', 'error': 'Service not defined'}
    
    # Check translation_service
    try:
        if translation_service is not None:
            details['translation_service'] = {'status': 'available', 'type': str(type(translation_service))}
            # Check if translate_text method exists
            if hasattr(translation_service, 'translate_text'):
                details['translation_service']['has_translate_text'] = True
            else:
                details['translation_service']['has_translate_text'] = False
                details['translation_service']['available_methods'] = [method for method in dir(translation_service) if not method.startswith('_')]
        else:
            details['translation_service'] = {'status': 'unavailable', 'error': 'Service is None'}
    except NameError:
        details['translation_service'] = {'status': 'unavailable', 'error': 'Service not defined'}
    
    # Check voice_service
    try:
        if voice_service is not None:
            details['voice_service'] = {'status': 'available', 'type': str(type(voice_service))}
        else:
            details['voice_service'] = {'status': 'unavailable', 'error': 'Service is None'}
    except NameError:
        details['voice_service'] = {'status': 'unavailable', 'error': 'Service not defined'}
    
    # Check progress_tracker
    try:
        if progress_tracker is not None:
            details['progress_tracker'] = {'status': 'available', 'type': str(type(progress_tracker))}
        else:
            details['progress_tracker'] = {'status': 'unavailable', 'error': 'Service is None'}
    except NameError:
        details['progress_tracker'] = {'status': 'unavailable', 'error': 'Service not defined'}
    
    # Check rate_limiter
    try:
        if rate_limiter is not None:
            details['rate_limiter'] = {'status': 'available', 'type': str(type(rate_limiter))}
        else:
            details['rate_limiter'] = {'status': 'unavailable', 'error': 'Service is None'}
    except NameError:
        details['rate_limiter'] = {'status': 'unavailable', 'error': 'Service not defined'}
    
    return details

# Database setup with PythonAnywhere path
DATABASE_PATH = app.config['DATABASE_PATH']

def get_db_connection():
    """Get database connection with proper error handling"""
    try:
        logger.info(f"Attempting to connect to database: {DATABASE_PATH}")
        conn = sqlite3.connect(DATABASE_PATH, timeout=20)
        conn.row_factory = sqlite3.Row
        logger.info("Database connection successful")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {str(e)}")
        logger.error(f"Database path: {DATABASE_PATH}")
        raise

def init_db():
    """Initialize the database with all required tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                age INTEGER NOT NULL,
                learning_level TEXT NOT NULL DEFAULT 'beginner',
                level INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                level INTEGER NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                xp_earned INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                level INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                user_message TEXT,
                ai_response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        ''')
        
        # User stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_xp INTEGER DEFAULT 0,
                current_level INTEGER DEFAULT 1,
                total_conversations INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                study_time_minutes INTEGER DEFAULT 0,
                conversations_completed INTEGER DEFAULT 0,
                topics_completed INTEGER DEFAULT 0,
                streak_days INTEGER DEFAULT 0,
                last_activity_date DATE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

def migrate_database():
    """Migrate existing database to add missing columns"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if display_name column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add missing columns if they don't exist
        if 'display_name' not in columns:
            logger.info("Adding display_name column to users table")
            cursor.execute('ALTER TABLE users ADD COLUMN display_name TEXT')
            # Set default display_name to username for existing users
            cursor.execute('UPDATE users SET display_name = username WHERE display_name IS NULL')
            
        if 'age' not in columns:
            logger.info("Adding age column to users table")
            cursor.execute('ALTER TABLE users ADD COLUMN age INTEGER DEFAULT 25')
            
        if 'learning_level' not in columns:
            logger.info("Adding learning_level column to users table")
            cursor.execute('ALTER TABLE users ADD COLUMN learning_level TEXT DEFAULT "beginner"')
            
        # Make email nullable (remove UNIQUE constraint by recreating table if needed)
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        table_sql = cursor.fetchone()
        if table_sql and 'email TEXT UNIQUE NOT NULL' in table_sql[0]:
            logger.info("Updating email column to be nullable")
            # Create new table with correct schema
            cursor.execute('''
                CREATE TABLE users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    age INTEGER NOT NULL DEFAULT 25,
                    learning_level TEXT NOT NULL DEFAULT 'beginner',
                    level INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # Copy data from old table
            cursor.execute('''
                INSERT INTO users_new (id, username, email, password_hash, display_name, age, learning_level, level, created_at, last_login)
                SELECT id, username, email, password_hash, 
                       COALESCE(display_name, username), 
                       COALESCE(age, 25), 
                       COALESCE(learning_level, 'beginner'), 
                       level, created_at, last_login
                FROM users
            ''')
            
            # Replace old table
            cursor.execute('DROP TABLE users')
            cursor.execute('ALTER TABLE users_new RENAME TO users')
            
        # Migrate user_stats table
        cursor.execute("PRAGMA table_info(user_stats)")
        stats_columns = [column[1] for column in cursor.fetchall()]
        
        if 'total_conversations' not in stats_columns:
            logger.info("Adding total_conversations column to user_stats table")
            cursor.execute('ALTER TABLE user_stats ADD COLUMN total_conversations INTEGER DEFAULT 0')
            
        if 'total_messages' not in stats_columns:
            logger.info("Adding total_messages column to user_stats table")
            cursor.execute('ALTER TABLE user_stats ADD COLUMN total_messages INTEGER DEFAULT 0')
            
        if 'study_time_minutes' not in stats_columns:
            logger.info("Adding study_time_minutes column to user_stats table")
            cursor.execute('ALTER TABLE user_stats ADD COLUMN study_time_minutes INTEGER DEFAULT 0')
            
        conn.commit()
        conn.close()
        logger.info("Database migration completed successfully")
        
    except Exception as e:
        logger.error(f"Database migration error: {str(e)}")
        # Don't raise - continue with app startup
        if 'conn' in locals():
            conn.close()

# Initialize and migrate database on startup
init_db()
migrate_database()

# Initialize services
try:
    logger.info("Initializing services...")
    
    # Initialize ConversationalAI
    try:
        conversational_ai = ConversationalAI()
        logger.info("ConversationalAI initialized")
    except Exception as e:
        logger.error(f"ConversationalAI initialization failed: {str(e)}")
        conversational_ai = None
    
    # Initialize TranslationService  
    try:
        translation_service = TranslationService()
        logger.info("TranslationService initialized")
    except Exception as e:
        logger.error(f"TranslationService initialization failed: {str(e)}")
        translation_service = None
    
    # Initialize VoiceService
    try:
        voice_service = VoiceService()
        logger.info("VoiceService initialized")
    except Exception as e:
        logger.error(f"VoiceService initialization failed: {str(e)}")
        voice_service = None
    
    # Initialize ProgressTracker
    try:
        progress_tracker = ProgressTracker(app.config['DATABASE_PATH'])
        logger.info("ProgressTracker initialized")
    except Exception as e:
        logger.error(f"ProgressTracker initialization failed: {str(e)}")
        progress_tracker = None
    
    # Initialize RateLimiter
    try:
        rate_limiter = RateLimiter()
        logger.info("RateLimiter initialized")
    except Exception as e:
        logger.error(f"RateLimiter initialization failed: {str(e)}")
        rate_limiter = None
    
    logger.info("Service initialization completed")
    
    # Initialize Render Selenium client
    try:
        from render_selenium_client import init_selenium_client, get_selenium_client
        RENDER_SELENIUM_URL = "https://selenium-services.onrender.com"  # Replace with your Render URL
        init_selenium_client(RENDER_SELENIUM_URL)
        logger.info("Render Selenium client initialized")
    except Exception as e:
        logger.error(f"Render Selenium client initialization failed: {str(e)}")
        # Define fallback functions when Selenium client is not available
        class FallbackSeleniumClient:
            def health_check(self):
                return False
            def send_chatbot_message(self, **kwargs):
                return "I'm currently offline. Please try again later."
            def start_stt_session(self, language='en'):
                return None
            def get_stt_result(self, session_id):
                return ""
            def stop_stt_session(self, session_id):
                return ""
            def get_service_status(self):
                return {"status": "unavailable", "reason": "selenium client not initialized"}
        
        def get_selenium_client():
            return FallbackSeleniumClient()
        def init_selenium_client(url):
            pass
        # Continue without Selenium service - will use fallbacks
except Exception as e:
    logger.error(f"Service initialization error: {str(e)}")
    logger.error(f"Full service initialization traceback: {traceback.format_exc()}")
    # Define fallback functions for when services fail
    class FallbackSeleniumClient:
        def health_check(self):
            return False
        def send_chatbot_message(self, **kwargs):
            return "I'm currently offline. Please try again later."
        def start_stt_session(self, language='en'):
            return None
        def get_stt_result(self, session_id):
            return ""
        def stop_stt_session(self, session_id):
            return ""
        def get_service_status(self):
            return {"status": "unavailable", "reason": "service initialization failed"}
            
    def get_selenium_client():
        return FallbackSeleniumClient()
    def init_selenium_client(url):
        pass
    # Continue without failing services for PythonAnywhere compatibility

# Rate limiting decorator
def rate_limit_decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check if rate_limiter is available
            rate_limiter_svc = get_rate_limiter()
            if rate_limiter_svc:
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                if not rate_limiter_svc.is_allowed(client_ip):
                    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
            else:
                logger.warning("Rate limiter not available, skipping rate limiting")
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            # Continue without rate limiting if there's an error
            return f(*args, **kwargs)
    return decorated_function

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# API Routes
@app.route('/api/chat', methods=['POST'])
@rate_limit_decorator
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message']
        topic = data.get('topic', 'general')
        level = data.get('level', 1)
        user_id = data.get('user_id', 1)
        
        logger.info(f"Processing chat message from user {user_id}: {user_message[:50]}...")
        
        # Get AI response using Render Selenium service
        try:
            # Get user's actual learning level from database
            user_level = "beginner"  # Default fallback
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT learning_level FROM users WHERE id = ?', (user_id,))
                user_data = cursor.fetchone()
                if user_data:
                    user_level = user_data[0] or "beginner"
                conn.close()
            except Exception as db_error:
                logger.warning(f"Could not fetch user learning level: {str(db_error)}")
            
            selenium_client = get_selenium_client()
            if selenium_client and selenium_client.health_check():
                # Use Render Selenium service for AI responses
                logger.info(f"Using Render Selenium service for AI response with user_level: {user_level}")
                response = selenium_client.send_chatbot_message(
                    message=user_message,
                    topic=topic,
                    level=level,
                    user_level=user_level
                )
            elif conversational_ai:
                # Fallback to conversational_ai which will use Render as well
                logger.warning("Render service direct call failed, trying conversational_ai")
                response = conversational_ai.get_response(
                    message=user_message,
                    topic=topic,
                    user_level=user_level
                )
            else:
                # Final fallback response if no AI service is available
                logger.warning("No AI service available, using fallback response")
                response = f"I understand you're saying: '{user_message}'. I'm currently experiencing technical difficulties. Please try again later."
        except Exception as ai_error:
            logger.error(f"AI service error: {str(ai_error)}")
            response = f"I'm sorry, I'm having trouble processing your message right now. Could you please try again?"
        
        # Save conversation to database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get or create conversation
            cursor.execute('''
                SELECT id FROM conversations 
                WHERE user_id = ? AND topic = ? AND level = ? AND ended_at IS NULL
                ORDER BY started_at DESC LIMIT 1
            ''', (user_id, topic, level))
            
            conversation = cursor.fetchone()
            
            if not conversation:
                cursor.execute('''
                    INSERT INTO conversations (user_id, topic, level) 
                    VALUES (?, ?, ?)
                ''', (user_id, topic, level))
                conversation_id = cursor.lastrowid
            else:
                conversation_id = conversation[0]
            
            # Save message
            cursor.execute('''
                INSERT INTO messages (conversation_id, user_message, ai_response) 
                VALUES (?, ?, ?)
            ''', (conversation_id, user_message, response))
            
            # Update conversation message count
            cursor.execute('''
                UPDATE conversations 
                SET total_messages = total_messages + 1 
                WHERE id = ?
            ''', (conversation_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as db_error:
            logger.error(f"Database error in chat: {str(db_error)}")
            # Continue without saving to database
        
        return jsonify({
            'response': response,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': 'Failed to process message'}), 500

@app.route('/api/translate', methods=['POST'])
@rate_limit_decorator
def translate():
    """Handle translation requests"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text']
        target_lang = data.get('target_lang', 'fa')
        source_lang = data.get('source_lang', 'en')
        
        # Get translation using Render service
        selenium_client = get_selenium_client()
        if selenium_client and selenium_client.health_check():
            # Use Render service for translation
            translation = selenium_client.translate_text(text, target_lang, source_lang)
        else:
            # Fallback when Render service is unavailable
            translation = f"Render translation service unavailable. Original text: {text}"
        
        return jsonify({
            'translation': translation,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return jsonify({'error': 'Translation failed'}), 500

@app.route('/api/tts', methods=['POST'])
@rate_limit_decorator
def text_to_speech():
    """Handle text-to-speech requests"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text']
        lang = data.get('lang', 'en')
        
        # Generate audio
        voice_svc = get_voice_service()
        if voice_svc:
            audio_data = voice_svc.text_to_speech(text, lang)
        else:
            audio_data = None
        
        if audio_data:
            return jsonify({
                'audio_data': audio_data,
                'status': 'success'
            })
        else:
            return jsonify({'error': 'TTS generation failed'}), 500
        
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        return jsonify({'error': 'TTS failed'}), 500

@app.route('/api/stt/start', methods=['POST'])
@rate_limit_decorator
def start_speech_to_text():
    """Start speech-to-text session using Render service"""
    try:
        data = request.get_json() or {}
        language = data.get('language', 'en')
        
        selenium_client = get_selenium_client()
        if selenium_client and selenium_client.health_check():
            session_id = selenium_client.start_stt_session(language)
            if session_id:
                return jsonify({
                    'session_id': session_id,
                    'status': 'success',
                    'message': 'STT session started'
                })
            else:
                return jsonify({'error': 'Failed to start STT session'}), 500
        else:
            return jsonify({'error': 'Render STT service unavailable'}), 503
            
    except Exception as e:
        logger.error(f"STT start error: {str(e)}")
        return jsonify({'error': 'Failed to start speech-to-text'}), 500

@app.route('/api/stt/result/<session_id>', methods=['GET'])
@rate_limit_decorator
def get_speech_to_text_result(session_id):
    """Get current STT transcription"""
    try:
        selenium_client = get_selenium_client()
        if selenium_client:
            text = selenium_client.get_stt_result(session_id)
            return jsonify({
                'text': text,
                'session_id': session_id,
                'status': 'success'
            })
        else:
            return jsonify({'error': 'Render STT service unavailable'}), 503
            
    except Exception as e:
        logger.error(f"STT result error: {str(e)}")
        return jsonify({'error': 'Failed to get STT result'}), 500

@app.route('/api/stt/stop/<session_id>', methods=['POST'])
@rate_limit_decorator
def stop_speech_to_text(session_id):
    """Stop STT session and get final result"""
    try:
        selenium_client = get_selenium_client()
        if selenium_client:
            final_text = selenium_client.stop_stt_session(session_id)
            return jsonify({
                'text': final_text,
                'session_id': session_id,
                'status': 'success',
                'message': 'STT session stopped'
            })
        else:
            return jsonify({'error': 'Render STT service unavailable'}), 503
            
    except Exception as e:
        logger.error(f"STT stop error: {str(e)}")
        return jsonify({'error': 'Failed to stop STT session'}), 500

@app.route('/api/progress', methods=['GET', 'POST'])
@rate_limit_decorator
def handle_progress():
    """Handle progress tracking"""
    try:
        if request.method == 'GET':
            user_id = request.args.get('user_id', 1)
            
            # Get user progress
            progress_tracker_svc = get_progress_tracker()
            if progress_tracker_svc:
                progress_data = progress_tracker_svc.get_user_progress(user_id)
            else:
                progress_data = {"message": "Progress tracker unavailable", "user_id": user_id}
            
            return jsonify({
                'progress': progress_data,
                'status': 'success'
            })
            
        elif request.method == 'POST':
            data = request.get_json()
            user_id = data.get('user_id', 1)
            action = data.get('action', 'conversation_completion')
            
            if action == 'conversation_completion':
                # Award XP for conversation completion
                topic = data.get('topic', 'general')
                level = data.get('level', 1)
                duration_minutes = data.get('duration_minutes', 0)
                message_count = data.get('message_count', 0)
                
                # Base XP for completion
                base_xp = 25
                
                # Duration bonus (up to 30 XP for 15+ minutes)
                duration_bonus = min(30, duration_minutes * 2)
                
                # Engagement bonus (up to 40 XP for 20+ messages)
                engagement_bonus = min(40, message_count * 2)
                
                total_xp = base_xp + duration_bonus + engagement_bonus
                
                # Award XP
                progress_tracker_svc = get_progress_tracker()
                if progress_tracker_svc:
                    progress_tracker_svc.add_experience_points(user_id, 'conversation_completion', total_xp)
                else:
                    logger.warning("Progress tracker unavailable for XP award")
                
                # Mark conversation as completed
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        UPDATE conversations 
                        SET completed = TRUE, ended_at = CURRENT_TIMESTAMP 
                        WHERE user_id = ? AND topic = ? AND level = ? AND ended_at IS NULL
                    ''', (user_id, topic, level))
                    
                    conn.commit()
                    conn.close()
                    
                except Exception as db_error:
                    logger.error(f"Database error marking completion: {str(db_error)}")
                
                return jsonify({
                    'xp_awarded': total_xp,
                    'breakdown': {
                        'base': base_xp,
                        'duration_bonus': duration_bonus,
                        'engagement_bonus': engagement_bonus
                    },
                    'status': 'success'
                })
            
            else:
                # Regular action
                progress_tracker_svc = get_progress_tracker()
                if progress_tracker_svc:
                    progress_tracker_svc.add_experience_points(user_id, action)
                else:
                    logger.warning("Progress tracker unavailable for action tracking")
                
                return jsonify({
                    'status': 'success',
                    'action': action
                })
        
    except Exception as e:
        logger.error(f"Progress error: {str(e)}")
        return jsonify({'error': 'Progress tracking failed'}), 500

@app.route('/api/user/<int:user_id>', methods=['GET'])
@rate_limit_decorator
def get_user_by_id(user_id):
    """Get user data by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, display_name, age, learning_level, email, created_at 
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return jsonify(dict(user_data))
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting user by ID: {str(e)}")
        return jsonify({'error': 'Failed to get user data'}), 500

@app.route('/api/user', methods=['GET', 'POST', 'PUT'])
@rate_limit_decorator
def handle_user():
    """Handle user-related requests"""
    try:
        if request.method == 'GET':
            user_id = request.args.get('user_id', 1)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, u.email, u.level, u.created_at,
                       s.total_xp, s.current_level, s.conversations_completed,
                       s.topics_completed, s.streak_days
                FROM users u
                LEFT JOIN user_stats s ON u.id = s.user_id
                WHERE u.id = ?
            ''', (user_id,))
            
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data:
                return jsonify({
                    'user': dict(user_data),
                    'status': 'success'
                })
            else:
                return jsonify({'error': 'User not found'}), 404
        
        elif request.method == 'POST':
            data = request.get_json()
            
            # Add debugging log
            logger.info(f"Received POST data: {data}")
            logger.info(f"Request headers: {dict(request.headers)}")
            logger.info(f"Request method: {request.method}")
            
            if not data:
                logger.error("No JSON data received")
                return jsonify({'error': 'No JSON data received'}), 400
                
            action = data.get('action')
            logger.info(f"Action: {action}")
            
            if action == 'create' or action == 'register':
                try:
                    username = data.get('username')
                    email = data.get('email')
                    password = data.get('password')
                    display_name = data.get('displayName')
                    age = data.get('age')
                    learning_level = data.get('learningLevel')
                    
                    logger.info(f"Registration attempt - username: {username}, display_name: {display_name}, age: {age}, learning_level: {learning_level}")
                    
                    if not all([username, password, display_name, age, learning_level]):
                        missing_fields = []
                        if not username: missing_fields.append('username')
                        if not password: missing_fields.append('password')
                        if not display_name: missing_fields.append('displayName')
                        if not age: missing_fields.append('age')
                        if not learning_level: missing_fields.append('learningLevel')
                        
                        error_msg = f'Missing required fields: {", ".join(missing_fields)}'
                        logger.error(error_msg)
                        return jsonify({'error': error_msg}), 400
                    
                    # Generate email if not provided
                    if not email:
                        email = f"{username}@englishapp.local"
                    
                    # Hash password
                    password_hash = hash_password(password)
                    
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    try:
                        cursor.execute('''
                            INSERT INTO users (username, email, password_hash, display_name, age, learning_level) 
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (username, email, password_hash, display_name, age, learning_level))
                        
                        user_id = cursor.lastrowid
                        
                        # Create user stats with all required columns
                        cursor.execute('''
                            INSERT INTO user_stats (user_id, total_conversations, total_messages, study_time_minutes) 
                            VALUES (?, 0, 0, 0)
                        ''', (user_id,))
                        
                        conn.commit()
                        conn.close()
                        
                        logger.info(f"User created successfully: {username} with ID {user_id}")
                        
                        return jsonify({
                            'user_id': user_id,
                            'status': 'success'
                        })
                        
                    except sqlite3.IntegrityError as e:
                        conn.close()
                        logger.error(f"User creation failed - duplicate: {str(e)}")
                        return jsonify({'error': 'Username or email already exists'}), 400
                    
                    except Exception as e:
                        conn.close()
                        logger.error(f"User creation failed - unexpected error: {str(e)}")
                        return jsonify({'error': 'Registration failed'}), 500
                        
                except Exception as e:
                    logger.error(f"Registration validation failed: {str(e)}")
                    return jsonify({'error': f'Registration validation error: {str(e)}'}), 400
            
            elif action == 'login':
                username = data.get('username')
                password = data.get('password')
                
                if not all([username, password]):
                    return jsonify({'error': 'Username and password required'}), 400
                
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, password_hash FROM users WHERE username = ?
                ''', (username,))
                
                user = cursor.fetchone()
                
                if user and verify_password(user[1], password):
                    # Update last login
                    cursor.execute('''
                        UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
                    ''', (user[0],))
                    
                    conn.commit()
                    conn.close()
                    
                    return jsonify({
                        'user_id': user[0],
                        'status': 'success'
                    })
                else:
                    conn.close()
                    return jsonify({'error': 'Invalid credentials'}), 401
            
            else:
                logger.error(f"Invalid action received: {action}")
                return jsonify({'error': f'Invalid action: {action}'}), 400
        
        elif request.method == 'PUT':
            # Handle user profile updates (learning level, display name, etc.)
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No JSON data received'}), 400
            
            user_id = data.get('user_id')
            if not user_id:
                return jsonify({'error': 'User ID is required'}), 400
            
            # Get fields to update
            learning_level = data.get('learning_level')
            display_name = data.get('display_name')
            age = data.get('age')
            
            if not any([learning_level, display_name, age]):
                return jsonify({'error': 'At least one field to update is required'}), 400
            
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
                if not cursor.fetchone():
                    conn.close()
                    return jsonify({'error': 'User not found'}), 404
                
                # Build dynamic update query
                update_fields = []
                update_values = []
                
                if learning_level:
                    # Validate learning level
                    valid_levels = ['absolute_beginner', 'beginner', 'intermediate', 'advanced']
                    if learning_level not in valid_levels:
                        conn.close()
                        return jsonify({'error': f'Invalid learning level. Must be one of: {", ".join(valid_levels)}'}), 400
                    update_fields.append('learning_level = ?')
                    update_values.append(learning_level)
                
                if display_name:
                    update_fields.append('display_name = ?')
                    update_values.append(display_name.strip())
                
                if age:
                    if not isinstance(age, int) or age < 1 or age > 120:
                        conn.close()
                        return jsonify({'error': 'Age must be a number between 1 and 120'}), 400
                    update_fields.append('age = ?')
                    update_values.append(age)
                
                # Execute update
                update_values.append(user_id)  # For WHERE clause
                update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
                
                cursor.execute(update_query, update_values)
                
                if cursor.rowcount == 0:
                    conn.close()
                    return jsonify({'error': 'No changes made'}), 400
                
                conn.commit()
                
                # Get updated user data
                cursor.execute('''
                    SELECT id, username, display_name, age, learning_level, email, created_at 
                    FROM users WHERE id = ?
                ''', (user_id,))
                
                updated_user = cursor.fetchone()
                conn.close()
                
                logger.info(f"User {user_id} profile updated successfully. Changed fields: {', '.join([f.split(' = ')[0] for f in update_fields])}")
                
                return jsonify({
                    'status': 'success',
                    'message': 'Profile updated successfully',
                    'user': dict(updated_user) if updated_user else None,
                    'updated_fields': [f.split(' = ')[0] for f in update_fields]
                })
                
            except Exception as e:
                if 'conn' in locals():
                    conn.close()
                logger.error(f"Profile update failed: {str(e)}")
                return jsonify({'error': 'Profile update failed'}), 500
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"User handling error: {str(e)}")
        logger.error(f"Full traceback: {error_details}")
        return jsonify({
            'error': 'User operation failed',
            'details': str(e),
            'traceback': error_details
        }), 500

@app.route('/api/user-level-info/<int:user_id>', methods=['GET'])
@rate_limit_decorator
def get_user_level_info(user_id):
    """Get user level and progress information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user basic info
        cursor.execute('''
            SELECT u.id, u.username, u.display_name, u.learning_level, u.level, u.created_at,
                   COALESCE(s.total_xp, 0) as total_xp,
                   COALESCE(s.current_level, 1) as current_level,
                   COALESCE(s.conversations_completed, 0) as conversations_completed,
                   COALESCE(s.topics_completed, 0) as topics_completed,
                   COALESCE(s.streak_days, 0) as streak_days,
                   COALESCE(s.total_conversations, 0) as total_conversations,
                   COALESCE(s.total_messages, 0) as total_messages,
                   COALESCE(s.study_time_minutes, 0) as study_time_minutes
            FROM users u
            LEFT JOIN user_stats s ON u.id = s.user_id
            WHERE u.id = ?
        ''', (user_id,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Calculate level progress
        total_xp = user_data['total_xp'] or 0
        current_level = user_data['current_level'] or 1
        
        # XP required for each level (exponential growth)
        def xp_for_level(level):
            return level * 100
        
        current_level_xp = xp_for_level(current_level - 1) if current_level > 1 else 0
        next_level_xp = xp_for_level(current_level)
        current_xp = total_xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp
        
        if xp_needed > 0:
            xp_progress_percent = (current_xp / xp_needed) * 100
        else:
            xp_progress_percent = 100
        
        level_info = {
            'user_id': user_data['id'],
            'username': user_data['username'],
            'display_name': user_data['display_name'],
            'level': current_level,
            'total_xp': total_xp,
            'current_xp': current_xp,
            'next_level_xp': next_level_xp,
            'xp_progress_percent': min(100, max(0, xp_progress_percent)),
            'conversations_completed': user_data['conversations_completed'],
            'topics_completed': user_data['topics_completed'],
            'current_streak': user_data['streak_days'],
            'total_conversations': user_data['total_conversations'],
            'total_messages': user_data['total_messages'],
            'study_time_minutes': user_data['study_time_minutes']
        }
        
        return jsonify(level_info)
        
    except Exception as e:
        logger.error(f"Error getting user level info: {str(e)}")
        return jsonify({'error': 'Failed to get user level info'}), 500

@app.route('/api/user/<int:user_id>/learning-level', methods=['PUT'])
@rate_limit_decorator
def update_user_learning_level(user_id):
    """Update user's learning level specifically"""
    try:
        data = request.get_json()
        
        if not data or 'learning_level' not in data:
            return jsonify({'error': 'Learning level is required'}), 400
        
        learning_level = data['learning_level']
        
        # Validate learning level
        valid_levels = ['absolute_beginner', 'beginner', 'intermediate', 'advanced']
        if learning_level not in valid_levels:
            return jsonify({
                'error': f'Invalid learning level. Must be one of: {", ".join(valid_levels)}'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists and get current level
        cursor.execute('SELECT learning_level FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        old_level = user_data[0]
        
        # Update learning level
        cursor.execute('UPDATE users SET learning_level = ? WHERE id = ?', (learning_level, user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Failed to update learning level'}), 500
        
        conn.commit()
        conn.close()
        
        logger.info(f"User {user_id} learning level updated from '{old_level}' to '{learning_level}'")
        
        return jsonify({
            'status': 'success',
            'message': 'Learning level updated successfully',
            'old_level': old_level,
            'new_level': learning_level,
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Error updating learning level: {str(e)}")
        return jsonify({'error': 'Failed to update learning level'}), 500

@app.route('/api/chat/init-topic', methods=['POST'])
@rate_limit_decorator
def init_topic():
    """Initialize a conversation topic"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        topic_id = data.get('topic')
        user_id = data.get('user_id')
        
        if not all([topic_id, user_id]):
            return jsonify({'error': 'Topic and user_id are required'}), 400
        
        logger.info(f"Initializing topic {topic_id} for user {user_id}")
        
        # For now, just return success - the actual topic initialization
        # would depend on your conversation system
        return jsonify({
            'status': 'success',
            'topic': topic_id,
            'message': 'Topic initialized successfully'
        })
        
    except Exception as e:
        logger.error(f"Topic initialization error: {str(e)}")
        return jsonify({'error': 'Failed to initialize topic'}), 500

@app.route('/api/track-login', methods=['POST'])
@rate_limit_decorator
def track_login():
    """Track daily login for XP"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({'error': 'User ID is required'}), 400
        
        user_id = data['user_id']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user already logged in today
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT last_login FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        last_login = user[0] or ''
        first_login_today = not last_login.startswith(today)
        
        if first_login_today:
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user_id,))
            
            # Award daily login XP
            cursor.execute('''
                UPDATE user_stats 
                SET total_xp = total_xp + 10,
                    streak_days = streak_days + 1
                WHERE user_id = ?
            ''', (user_id,))
            
            # If user_stats doesn't exist, create it
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO user_stats (user_id, total_xp, streak_days, total_conversations, total_messages, study_time_minutes) 
                    VALUES (?, 10, 1, 0, 0, 0)
                ''', (user_id,))
            
            conn.commit()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'first_login_today': first_login_today,
            'xp_awarded': 10 if first_login_today else 0
        })
        
    except Exception as e:
        logger.error(f"Error tracking login: {str(e)}")
        return jsonify({'error': 'Failed to track login'}), 500

@app.route('/api/track-message', methods=['POST'])
@rate_limit_decorator
def track_message():
    """Track message for XP and progress"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({'error': 'User ID is required'}), 400
        
        user_id = data['user_id']
        topic_id = data.get('topic_id')
        message_type = data.get('type', 'text')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Award XP for message (5 XP per message)
        xp_awarded = 5
        cursor.execute('''
            UPDATE user_stats 
            SET total_xp = total_xp + ?,
                total_messages = total_messages + 1
            WHERE user_id = ?
        ''', (xp_awarded, user_id))
        
        # If user_stats doesn't exist, create it
        if cursor.rowcount == 0:
            cursor.execute('''
                INSERT INTO user_stats (user_id, total_xp, total_messages, total_conversations, study_time_minutes) 
                VALUES (?, ?, 1, 0, 0)
            ''', (user_id, xp_awarded))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'xp_awarded': xp_awarded
        })
        
    except Exception as e:
        logger.error(f"Error tracking message: {str(e)}")
        return jsonify({'error': 'Failed to track message'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        
        # Check Render Selenium service
        render_status = "unavailable"
        try:
            selenium_client = get_selenium_client()
            if selenium_client:
                render_status = "available" if selenium_client.health_check() else "unhealthy"
            else:
                render_status = "not_initialized"
        except Exception as selenium_error:
            logger.error(f"Selenium client error in health check: {str(selenium_error)}")
            render_status = f"error: {str(selenium_error)}"
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'render_selenium': render_status,
            'render_chatbot': render_status,
            'render_translation': render_status,
            'render_stt': render_status,
            'timestamp': datetime.now().isoformat(),
            'environment': 'pythonanywhere'
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'database': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/service-status', methods=['GET'])
@rate_limit_decorator
def service_status():
    """Get detailed service status for debugging"""
    try:
        status = {
            'services': {},
            'render_integration': {},
            'environment': 'pythonanywhere',
            'timestamp': datetime.now().isoformat()
        }
        
        # Check local services
        status['services']['conversational_ai'] = 'available' if is_service_available(conversational_ai) else 'unavailable'
        status['services']['translation_service'] = 'available' if is_service_available(translation_service) else 'unavailable'
        status['services']['voice_service'] = 'available' if is_service_available(voice_service) else 'unavailable'
        status['services']['progress_tracker'] = 'available' if is_service_available(progress_tracker) else 'unavailable'
        status['services']['rate_limiter'] = 'available' if is_service_available(rate_limiter) else 'unavailable'
        
        # Add detailed service information
        status['service_details'] = get_service_details()
        
        # Check Render integration
        try:
            selenium_client = get_selenium_client()
            if selenium_client:
                status['render_integration']['client'] = 'initialized'
                try:
                    status['render_integration']['health'] = 'healthy' if selenium_client.health_check() else 'unhealthy'
                except Exception as health_error:
                    status['render_integration']['health'] = f'health_check_error: {str(health_error)}'
                
                try:
                    service_status_response = selenium_client.get_service_status()
                    status['render_integration']['detailed_status'] = service_status_response
                except Exception as service_error:
                    status['render_integration']['detailed_status'] = f'service_status_error: {str(service_error)}'
            else:
                status['render_integration']['client'] = 'not_initialized'
                status['render_integration']['health'] = 'unavailable'
                status['render_integration']['detailed_status'] = 'selenium client not available'
        except Exception as selenium_error:
            status['render_integration']['client'] = 'error'
            status['render_integration']['health'] = f'error: {str(selenium_error)}'
            status['render_integration']['detailed_status'] = f'selenium_error: {str(selenium_error)}'
        
        # Test translation service
        if 'translation_service' in globals():
            try:
                # Use the correct method names for the actual translation service
                test_translation = translation_service.translate_english_to_farsi("Hello")
                status['services']['translation_test'] = 'working' if test_translation else 'failed'
            except AttributeError as attr_error:
                # Check what methods are actually available
                available_methods = [method for method in dir(translation_service) if not method.startswith('_')]
                status['services']['translation_test'] = f'method_error: available methods are {available_methods}'
            except Exception as trans_error:
                status['services']['translation_test'] = f'error: {str(trans_error)}'
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Service status check failed: {str(e)}")
        return jsonify({
            'error': 'Service status check failed',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/test-registration', methods=['POST'])
def test_registration():
    """Simple test registration without dependencies"""
    try:
        data = request.get_json() or {}
        username = data.get('username', 'testuser')
        password = data.get('password', 'testpass')
        
        return jsonify({
            'message': 'Test registration endpoint working',
            'received_username': username,
            'password_length': len(password),
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Test registration failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'failed'
        }), 500

@app.route('/api/test-database', methods=['GET'])
def test_database():
    """Test database operations comprehensively"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test 1: Check if users table exists and structure
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        users_table = cursor.fetchone()
        
        # Test 2: Count existing users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Test 3: Try a simple insert/delete test
        test_username = f"test_user_{int(time.time())}"
        test_password = "test_password"
        test_password_hash = hashlib.sha256(test_password.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, display_name, age, learning_level)
            VALUES (?, ?, ?, ?, ?)
        """, (test_username, test_password_hash, "Test User", 25, "beginner"))
        
        test_user_id = cursor.lastrowid
        
        # Clean up test user
        cursor.execute("DELETE FROM users WHERE id = ?", (test_user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'users_table_exists': users_table is not None,
            'users_table_sql': users_table[0] if users_table else None,
            'current_user_count': user_count,
            'test_insert_success': True,
            'test_user_id_created': test_user_id,
            'database_path': DATABASE_PATH
        })
        
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        return jsonify({
            'status': 'failed',
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@app.route('/debug-registration')
def debug_registration():
    """Debug registration page - serves the debug HTML directly"""
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registration Debug Tool</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .test-section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .result { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 3px; white-space: pre-wrap; font-family: monospace; }
        .error { background: #ffe6e6; border-left: 4px solid #ff0000; }
        .success { background: #e6ffe6; border-left: 4px solid #00aa00; }
        button { padding: 10px 15px; margin: 5px; cursor: pointer; }
        input, select { padding: 8px; margin: 5px; width: 200px; }
        label { display: inline-block; width: 120px; }
    </style>
</head>
<body>
    <h1>Registration Debug Tool</h1>
    
    <div class="test-section">
        <h3>1. Health Check</h3>
        <button onclick="testHealth()">Test Health Endpoint</button>
        <div id="healthResult" class="result"></div>
    </div>
    
    <div class="test-section">
        <h3>2. Database Test</h3>
        <button onclick="testDatabase()">Test Database Operations</button>
        <div id="databaseResult" class="result"></div>
    </div>
    
    <div class="test-section">
        <h3>3. Simple Registration Test</h3>
        <button onclick="testSimpleRegistration()">Test Simple Registration Endpoint</button>
        <div id="simpleResult" class="result"></div>
    </div>
    
    <div class="test-section">
        <h3>4. Full Registration Test</h3>
        <div>
            <label>Username:</label><input type="text" id="testUsername" value="testuser123"><br>
            <label>Password:</label><input type="password" id="testPassword" value="testpass123"><br>
            <label>Confirm Password:</label><input type="password" id="testConfirmPassword" value="testpass123"><br>
            <label>Display Name:</label><input type="text" id="testDisplayName" value="Test User"><br>
            <label>Age:</label><input type="number" id="testAge" value="25"><br>
            <label>Learning Level:</label>
            <select id="testLearningLevel">
                <option value="absolute_beginner">Absolute Beginner</option>
                <option value="beginner" selected>Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
            </select><br>
        </div>
        <button onclick="testFullRegistration()">Test Full Registration</button>
        <div id="fullResult" class="result"></div>
    </div>
    
    <div class="test-section">
        <h3>5. Original Registration Endpoint Test</h3>
        <button onclick="testOriginalRegistration()">Test Original /api/user Endpoint</button>
        <div id="originalResult" class="result"></div>
    </div>

    <div class="test-section">
        <h3>6. Database Reset (Danger Zone)</h3>
        <p style="color: red;">⚠️ This will delete all users and recreate the database!</p>
        <button onclick="resetDatabase()" style="background: red; color: white;">Reset Database</button>
        <div id="resetResult" class="result"></div>
    </div>

    <script>
        const BASE_URL = window.location.origin;
        
        async function makeRequest(url, options = {}) {
            try {
                const response = await fetch(BASE_URL + url, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                });
                
                const text = await response.text();
                let data;
                try {
                    data = JSON.parse(text);
                } catch (e) {
                    data = { raw_response: text };
                }
                
                return {
                    status: response.status,
                    ok: response.ok,
                    data: data
                };
            } catch (error) {
                return {
                    status: 'ERROR',
                    ok: false,
                    data: { error: error.message }
                };
            }
        }
        
        function displayResult(elementId, result) {
            const element = document.getElementById(elementId);
            element.className = result.ok ? 'result success' : 'result error';
            element.textContent = JSON.stringify(result, null, 2);
        }
        
        async function testHealth() {
            const result = await makeRequest('/api/health');
            displayResult('healthResult', result);
        }
        
        async function testDatabase() {
            const result = await makeRequest('/api/test-database');
            displayResult('databaseResult', result);
        }
        
        async function testSimpleRegistration() {
            const result = await makeRequest('/api/test-registration', {
                method: 'POST',
                body: JSON.stringify({
                    username: 'simpletest',
                    password: 'simplepass'
                })
            });
            displayResult('simpleResult', result);
        }
        
        async function testFullRegistration() {
            const data = {
                username: document.getElementById('testUsername').value,
                password: document.getElementById('testPassword').value,
                confirmPassword: document.getElementById('testConfirmPassword').value,
                displayName: document.getElementById('testDisplayName').value,
                age: parseInt(document.getElementById('testAge').value),
                learningLevel: document.getElementById('testLearningLevel').value
            };
            
            const result = await makeRequest('/api/test-real-registration', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            displayResult('fullResult', result);
        }
        
        async function testOriginalRegistration() {
            const data = {
                username: document.getElementById('testUsername').value,
                password: document.getElementById('testPassword').value,
                confirmPassword: document.getElementById('testConfirmPassword').value,
                displayName: document.getElementById('testDisplayName').value,
                age: parseInt(document.getElementById('testAge').value),
                learningLevel: document.getElementById('testLearningLevel').value,
                action: 'create'
            };
            
            const result = await makeRequest('/api/user', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            displayResult('originalResult', result);
        }
        
        async function resetDatabase() {
            if (!confirm('Are you sure? This will delete ALL users and recreate the database!')) {
                return;
            }
            
            const result = await makeRequest('/api/reset-database', {
                method: 'POST'
            });
            displayResult('resetResult', result);
        }
    </script>
</body>
</html>'''
    return html_content

@app.route('/api/test-real-registration', methods=['POST'])
def test_real_registration():
    """Test the actual registration process step by step"""
    try:
        data = request.get_json()
        logger.info(f"Test registration received data: {data}")
        
        if not data:
            return jsonify({'error': 'No JSON data received', 'step': 'data_validation'}), 400
            
        # Extract and validate required fields
        username = data.get('username', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirmPassword', '')
        display_name = data.get('displayName', '').strip()
        age = data.get('age')
        learning_level = data.get('learningLevel', '').strip()
        
        logger.info(f"Extracted fields: username={username}, display_name={display_name}, age={age}, learning_level={learning_level}")
        
        # Validation checks
        if not username:
            return jsonify({'error': 'Username is required', 'step': 'username_validation'}), 400
        if not password:
            return jsonify({'error': 'Password is required', 'step': 'password_validation'}), 400
        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match', 'step': 'password_match_validation'}), 400
        if not display_name:
            return jsonify({'error': 'Display name is required', 'step': 'display_name_validation'}), 400
        if not age or not str(age).isdigit():
            return jsonify({'error': 'Valid age is required', 'step': 'age_validation'}), 400
        if not learning_level:
            return jsonify({'error': 'Learning level is required', 'step': 'learning_level_validation'}), 400
            
        # Check if username exists
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                conn.close()
                return jsonify({'error': 'Username already exists', 'step': 'username_uniqueness'}), 400
                
            # Create password hash
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            logger.info(f"Password hash created successfully")
            
            # Insert user
            cursor.execute("""
                INSERT INTO users (username, password_hash, display_name, age, learning_level)
                VALUES (?, ?, ?, ?, ?)
            """, (username, password_hash, display_name, int(age), learning_level))
            
            user_id = cursor.lastrowid
            logger.info(f"User inserted with ID: {user_id}")
            
            # Create user stats
            cursor.execute("""
                INSERT INTO user_stats (user_id, total_conversations, total_messages, study_time_minutes)
                VALUES (?, 0, 0, 0)
            """, (user_id,))
            
            conn.commit()
            logger.info(f"User stats created for user ID: {user_id}")
            
            conn.close()
            
            return jsonify({
                'message': 'User registered successfully',
                'user_id': user_id,
                'username': username,
                'step': 'complete'
            })
            
        except Exception as db_error:
            logger.error(f"Database error during registration: {str(db_error)}")
            if 'conn' in locals():
                conn.close()
            return jsonify({
                'error': f'Database error: {str(db_error)}',
                'step': 'database_operation',
                'error_type': type(db_error).__name__
            }), 500
            
    except Exception as e:
        logger.error(f"Registration test failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'step': 'general_error',
            'error_type': type(e).__name__
        }), 500

@app.route('/api/reset-database', methods=['POST'])
def reset_database():
    """Reset database - DANGER: Deletes all data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Drop all tables
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS progress") 
        cursor.execute("DROP TABLE IF EXISTS conversations")
        cursor.execute("DROP TABLE IF EXISTS messages")
        cursor.execute("DROP TABLE IF EXISTS user_stats")
        
        conn.commit()
        conn.close()
        
        # Recreate database
        init_db()
        
        return jsonify({
            'status': 'success',
            'message': 'Database reset successfully',
            'tables_recreated': ['users', 'progress', 'conversations', 'messages', 'user_stats']
        })
        
    except Exception as e:
        logger.error(f"Database reset failed: {str(e)}")
        return jsonify({
            'status': 'failed',
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'Rate limit exceeded'}), 429

if __name__ == '__main__':
    # This won't be called on PythonAnywhere, but useful for local testing
    app.run(debug=False, host='0.0.0.0', port=5000)
