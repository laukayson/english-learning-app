from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sqlite3
import json
from datetime import datetime
import logging
from functools import wraps
import time
import hashlib
import secrets
import signal
import atexit

# Import our custom modules
from ai_models import AIModels
from translation_service import TranslationService
from voice_service import VoiceService
from web_stt_service import get_web_stt_service
# from services.image_service import ImageService  # Commented out due to PIL dependency
from services.progress_tracker import ProgressTracker
from rate_limiter import RateLimiter

# Configure logging
logging.basicConfig(level=logging.INFO)
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

app = Flask(__name__)
CORS(app)

# Configure static file serving for frontend
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static frontend files"""
    try:
        frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
        file_path = os.path.join(frontend_dir, filename)
        
        # Security check - make sure we're not serving files outside frontend directory
        if not os.path.commonpath([frontend_dir, file_path]) == frontend_dir:
            return "Access denied", 403
            
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return "File not found", 404
    except Exception as e:
        logger.error(f"Error serving static file {filename}: {e}")
        return "Error serving file", 500

@app.route('/app')
@app.route('/index.html')
def serve_frontend():
    """Serve the main frontend HTML file"""
    try:
        frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
        return send_file(os.path.join(frontend_dir, 'index.html'))
    except Exception as e:
        logger.error(f"Error serving frontend: {e}")
        return "Error loading application", 500

# Initialize services
ai_models = AIModels()
translation_service = TranslationService()
voice_service = VoiceService()
web_stt_service = get_web_stt_service()
# image_service = ImageService({})  # Commented out due to PIL dependency

# Pre-initialize STT service for immediate voice recording availability
logger.info("🎤 Initializing SpeechTexter window on startup...")
logger.info("🌐 SpeechTexter browser window will open automatically for voice recording")
web_stt_initialization_success = web_stt_service.initialize()
if web_stt_initialization_success:
    logger.info("✅ SpeechTexter window opened successfully - voice recording ready")
    logger.info("📺 You should see a Chrome browser window with SpeechTexter loaded")
else:
    logger.error("❌ SpeechTexter window failed to open - voice recording unavailable")
    logger.error("🔧 Check Chrome installation and network connectivity")

# Get absolute path to database
import os
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "db", "language_app.db")

def get_db_connection():
    """Get optimized database connection for PythonAnywhere"""
    conn = sqlite3.connect(db_path)
    # SQLite optimizations
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL') 
    conn.execute('PRAGMA cache_size=10000')
    conn.execute('PRAGMA temp_store=MEMORY')
    return conn

progress_tracker = ProgressTracker(db_path)
rate_limiter = RateLimiter()

# Initialize global conversational AI instance
try:
    from conversational_ai import ConversationalAI
    conversation_ai = ConversationalAI()
    logger.info("Global conversational AI instance initialized")
except Exception as e:
    logger.warning(f"Failed to initialize global conversational AI: {e}")
    conversation_ai = None

# Database initialization
def init_database():
    """Initialize SQLite database with required tables"""
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # SQLite optimizations for PythonAnywhere
    cursor.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging for better concurrency
    cursor.execute('PRAGMA synchronous=NORMAL')  # Balanced safety/performance
    cursor.execute('PRAGMA cache_size=10000')  # Increase cache size
    cursor.execute('PRAGMA temp_store=MEMORY')  # Store temporary tables in memory
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            level INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            settings TEXT DEFAULT '{}'
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
            completion_date TIMESTAMP,
            phrases_learned INTEGER DEFAULT 0,
            practice_sessions INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            messages TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Spaced repetition table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spaced_repetition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            phrase_id TEXT NOT NULL,
            interval_days INTEGER DEFAULT 1,
            ease_factor REAL DEFAULT 2.5,
            repetitions INTEGER DEFAULT 0,
            next_review DATE NOT NULL,
            quality INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Daily challenges table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            challenge_date DATE NOT NULL,
            challenge_type TEXT NOT NULL,
            target_count INTEGER DEFAULT 3,
            current_count INTEGER DEFAULT 0,
            completed BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

# Rate limiting decorator
def rate_limit(endpoint_type='default'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            if not rate_limiter.allow_request(client_ip, endpoint_type):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please wait before trying again.'
                }), 429
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Error handler decorator
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': 'Internal server error',
                'message': str(e),  # Always show error message for debugging
                'details': traceback.format_exc()
            }), 500
    return decorated_function

# Root endpoint - serve frontend
@app.route('/', methods=['GET'])
def root():
    """Serve the main frontend application"""
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_file(os.path.join(frontend_dir, 'index.html'))

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'ai_models': ai_models.is_ready(),
            'translation': translation_service.is_ready(),
            'voice': voice_service.is_ready()
            # 'image': image_service.is_ready()  # Commented out due to PIL dependency
        }
    })

# Conversation session management
@app.route('/api/chat/session/end', methods=['POST'])
@rate_limit('default')
@handle_errors
def end_chat_session():
    """End a conversation session and cleanup resources"""
    try:
        data = request.json
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        
        logger.info(f"Ending chat session for user {user_id}, session {session_id}")
        
        # Global cleanup for now (in a real app, each user would have their own instance)
        global conversation_ai
        if conversation_ai:
            try:
                conversation_ai.end_session()
                logger.info("Conversational AI session ended successfully")
            except Exception as e:
                logger.warning(f"Could not end conversational AI session: {e}")
        
        return jsonify({
            'status': 'success',
            'message': 'Session ended successfully',
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error ending chat session: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to end session: {str(e)}'
        }), 500

@app.route('/api/chat/clear', methods=['POST'])
@rate_limit('default')
@handle_errors
def clear_conversation():
    """Clear conversation history while maintaining session"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        logger.info(f"Clearing conversation history for user {user_id}")
        
        # Global conversation AI instance (in a real app, each user would have their own)
        global conversation_ai
        if conversation_ai:
            try:
                conversation_ai.clear_conversation_history()
                logger.info("Conversation history cleared successfully")
            except Exception as e:
                logger.warning(f"Could not clear conversation history: {e}")
        
        return jsonify({
            'status': 'success',
            'message': 'Conversation history cleared'
        })
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to clear conversation: {str(e)}'
        }), 500

# Chat endpoint (updated to track session)
@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages and return AI responses"""
    try:
        data = request.json
        message = data.get('message', '')
        topic = data.get('topic', 'general')
        user_id = data.get('user_id')
        user_level = data.get('user_level', 'beginner')  # Get from frontend first
        history = data.get('history', [])
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get user's proficiency level from database if user is logged in and level not provided
        if user_id and user_level == 'beginner':  # Only query DB if no level provided from frontend
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT level FROM users WHERE id = ?', (user_id,))
                result = cursor.fetchone()
                if result:
                    user_level = result[0] or 'beginner'
                conn.close()
            except Exception as e:
                app.logger.warning(f"Failed to get user level: {e}")
        
        # Import conversational AI module
        global conversation_ai
        
        # Log the user level for debugging
        app.logger.info(f"Processing chat for user_level: {user_level}, topic: {topic}")
        
        # Use global AI instance or create new one if not available
        if conversation_ai is None:
            from conversational_ai import ConversationalAI
            conversation_ai = ConversationalAI()
            
        ai_response = conversation_ai.get_response(message, topic, history, user_level)
        
        # Note: XP is only awarded when conversation is completed, not per message
        # This prevents XP gain when users leave conversations early
        
        # Generate Farsi translation
        try:
            farsi_translation = translation_service.translate_english_to_farsi(ai_response)
        except Exception as e:
            app.logger.warning(f"Failed to translate to Farsi: {e}")
            farsi_translation = "ترجمه در دسترس نیست"  # "Translation not available"
        
        return jsonify({
            'success': True,
            'ai_response': ai_response,
            'farsi_translation': farsi_translation,
            'topic': topic,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Chat error: {e}")
        return jsonify({'error': 'Failed to process chat message'}), 500

@app.route('/api/chat/init-topic', methods=['POST'])
def init_topic_context():
    """Initialize AI context when a topic is chosen (doesn't return AI response to user)"""
    try:
        data = request.json
        topic = data.get('topic', 'general')
        user_id = data.get('user_id')
        user_level = data.get('user_level', 'beginner')
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        # Get user's proficiency level from database if user is logged in and level not provided
        if user_id and user_level == 'beginner':
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT level FROM users WHERE id = ?', (user_id,))
                result = cursor.fetchone()
                if result:
                    user_level = result[0] or 'beginner'
                conn.close()
            except Exception as e:
                app.logger.warning(f"Failed to get user level: {e}")
        
        # Initialize topic context with AI
        global conversation_ai
        
        app.logger.info(f"Initializing topic context for: {topic}, level: {user_level}")
        
        # Use global AI instance or create new one if not available
        if conversation_ai is None:
            from conversational_ai import ConversationalAI
            conversation_ai = ConversationalAI()
        
        # Check if we have Selenium chatbot available
        success = False
        if hasattr(conversation_ai, 'selenium_chatbot') and conversation_ai.selenium_chatbot:
            success = conversation_ai.selenium_chatbot.initialize_topic_context(topic, user_level)
        else:
            app.logger.info("Selenium chatbot not available, context will be sent with first message")
            success = True  # Not an error, just different behavior
        
        return jsonify({
            'success': True,
            'topic': topic,
            'user_level': user_level,
            'context_initialized': success,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Topic context initialization error: {e}")
        return jsonify({'error': 'Failed to initialize topic context'}), 500

@app.route('/api/user/register', methods=['POST'])
# @rate_limit('default')  # Temporarily disabled for debugging
# @handle_errors  # Temporarily disabled for debugging
def register_user():
    print("=== REGISTRATION ENDPOINT CALLED ===")
    try:
        print("Step 1: Getting JSON data...")
        data = request.get_json()
        print(f"DEBUG: Registration request received: {data}")
        print(f"DEBUG: Request content type: {request.content_type}")
        print(f"DEBUG: Request method: {request.method}")
        
        if data is None:
            print("DEBUG: No JSON data received")
            return jsonify({'error': 'No JSON data provided'}), 400
        
        print("Step 2: Validating required fields...")
        required_fields = ['username', 'password', 'name', 'age', 'level']
        for field in required_fields:
            if field not in data:
                print(f"DEBUG: Missing field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate username
        username = data['username'].strip()
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters long'}), 400
        if len(username) > 50:
            return jsonify({'error': 'Username must be less than 50 characters'}), 400
        
        # Validate password
        password = data['password']
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        if len(password) > 100:
            return jsonify({'error': 'Password is too long'}), 400
        
        print("Step 3: Validating age...")
        try:
            age = int(data['age'])
            if not (5 <= age <= 100):
                print(f"DEBUG: Invalid age: {age}")
                return jsonify({'error': 'Age must be between 5 and 100'}), 400
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Age conversion error: {e}")
            return jsonify({'error': 'Age must be a valid number'}), 400
        
        print("Step 4: Validating level...")
        try:
            level = int(data['level'])
            if not (1 <= level <= 4):
                print(f"DEBUG: Invalid level: {level}")
                return jsonify({'error': 'Level must be between 1 and 4'}), 400
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Level conversion error: {e}")
            return jsonify({'error': 'Level must be a valid number'}), 400
        
        print("Step 5: Validation passed, checking username availability...")
        
        # Check if username already exists
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                return jsonify({'error': 'Username already exists'}), 409
        
        print("Step 6: Username available, creating user...")
        
        # Create unique user ID
        print("Step 7: Generating user ID...")
        user_id = f"user_{int(time.time() * 1000)}"
        print(f"DEBUG: Generated user_id: {user_id}")
        
        # Try to initialize user progress in the database
        print("Step 8: Initializing progress tracker...")
        try:
            print("DEBUG: Calling progress_tracker.initialize_user_progress...")
            success = progress_tracker.initialize_user_progress(user_id, level)
            print(f"DEBUG: Progress tracker result: {success}")
        except Exception as progress_error:
            print(f"DEBUG: Progress tracker error: {str(progress_error)}")
            import traceback
            traceback.print_exc()
            logger.error(f"Progress tracker error: {str(progress_error)}")
            # Continue without progress tracker if it fails
            success = True
            print("DEBUG: Continuing without progress tracker...")
        
        if success:
            print("Step 9: Creating user in main database...")
            # Hash the password
            hashed_password = hash_password(password)
            
            # Update user details in main database
            try:
                print(f"DEBUG: Connecting to database: {db_path}")
                print(f"DEBUG: Database exists: {os.path.exists(db_path)}")
                
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    print("DEBUG: Creating users table if needed...")
                    # Ensure the table has all required columns
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            id TEXT PRIMARY KEY,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL,
                            name TEXT NOT NULL,
                            age INTEGER NOT NULL,
                            level INTEGER NOT NULL,
                            created_at TEXT NOT NULL,
                            last_active TEXT DEFAULT CURRENT_TIMESTAMP,
                            settings TEXT DEFAULT '{}'
                        )
                    ''')
                    
                    # Add missing columns if they don't exist (for existing tables)
                    print("DEBUG: Checking and adding missing columns...")
                    try:
                        cursor.execute('ALTER TABLE users ADD COLUMN username TEXT')
                        print("DEBUG: Added username column")
                    except sqlite3.OperationalError:
                        print("DEBUG: Username column already exists")
                    
                    try:
                        cursor.execute('ALTER TABLE users ADD COLUMN password TEXT')
                        print("DEBUG: Added password column")
                    except sqlite3.OperationalError:
                        print("DEBUG: Password column already exists")
                    
                    try:
                        cursor.execute('ALTER TABLE users ADD COLUMN age INTEGER DEFAULT 25')
                        print("DEBUG: Added age column")
                    except sqlite3.OperationalError:
                        print("DEBUG: Age column already exists")
                    
                    try:
                        cursor.execute('ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1')
                        print("DEBUG: Added level column")
                    except sqlite3.OperationalError:
                        print("DEBUG: Level column already exists")
                    
                    try:
                        cursor.execute('ALTER TABLE users ADD COLUMN created_at TEXT DEFAULT ""')
                        print("DEBUG: Added created_at column")
                    except sqlite3.OperationalError:
                        print("DEBUG: Created_at column already exists")
                    
                    print("DEBUG: Inserting user data...")
                    # Insert user data
                    cursor.execute('''
                        INSERT OR REPLACE INTO users (id, username, password, name, age, level, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, username, hashed_password, data['name'], age, level, datetime.now().isoformat()))
                    
                    conn.commit()
                    print("DEBUG: User data committed to database successfully")
                    
                print("DEBUG: Database operation completed")
                logger.info(f"User {user_id} registered successfully")
                
            except Exception as db_error:
                print(f"DEBUG: Database error: {str(db_error)}")
                import traceback
                traceback.print_exc()
                logger.error(f"Database error: {str(db_error)}")
                return jsonify({'error': 'Database operation failed'}), 500
                
            print("Step 10: Creating response...")
            response_data = {
                'success': True,
                'user_id': user_id,
                'username': username,
                'name': data['name'],
                'age': age,
                'level': level,
                'message': 'User registered successfully'
            }
            print(f"DEBUG: Response data: {response_data}")
            
            print("Step 10: Returning success response")
            return jsonify(response_data)
        else:
            print("DEBUG: Progress tracker initialization failed")
            return jsonify({'error': 'Failed to initialize user progress'}), 500
            
    except Exception as e:
        print(f"DEBUG: MAIN EXCEPTION CAUGHT: {str(e)}")
        import traceback
        traceback.print_exc()
        logger.error(f"Error registering user: {str(e)}")
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500
        
    print("DEBUG: Registration function completed normally (this should not print)")
    return jsonify({'error': 'Unexpected end of function'}), 500

@app.route('/api/user/login', methods=['POST'])
@rate_limit('default')  # 10 requests per 5 minutes
@handle_errors
def login_user():
    data = request.get_json()
    
    # Check for required fields
    if 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password are required'}), 400
    
    username = data['username'].strip()
    password = data['password']
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get user by username
    cursor.execute('''
        SELECT id, username, password, name, age, level, settings, last_active
        FROM users 
        WHERE username = ?
        LIMIT 1
    ''', (username,))
    
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Verify password
    stored_password = user[2]
    if not verify_password(stored_password, password):
        conn.close()
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Update last active timestamp
    cursor.execute('''
        UPDATE users SET last_active = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (user[0],))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'user_id': user[0],
        'username': user[1],
        'name': user[3],
        'age': user[4],
        'level': user[5],
        'settings': json.loads(user[6] or '{}'),
        'last_active': user[7]
    })

@app.route('/api/user/logout', methods=['POST'])
@rate_limit('default')
@handle_errors
def logout_user():
    """Logout endpoint - mainly for client-side session cleanup"""
    data = request.get_json()
    user_id = data.get('user_id') if data else None
    
    if user_id:
        # Update last active timestamp on logout
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET last_active = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating last active on logout: {e}")
    
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/user/verify', methods=['POST'])
@rate_limit('default')
@handle_errors 
def verify_user():
    """Verify if a user still exists in the database"""
    data = request.get_json()
    username = data.get('username') if data else None
    
    if not username:
        return jsonify({'error': 'Missing username'}), 400
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user_exists = cursor.fetchone() is not None
    
    conn.close()
    
    if not user_exists:
        return jsonify({'error': 'User not found', 'user_exists': False}), 404
    
    return jsonify({'user_exists': True})

@app.route('/api/user/profile', methods=['GET', 'PUT'])
@rate_limit('default')
@handle_errors
def user_profile():
    user_id = request.args.get('user_id') or request.json.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT name, age, level, settings, created_at, last_active
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        conn.close()
        return jsonify({
            'name': user[0],
            'age': user[1],
            'level': user[2],
            'settings': json.loads(user[3] or '{}'),
            'created_at': user[4],
            'last_active': user[5]
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        update_fields = []
        values = []
        
        if 'level' in data:
            if not (1 <= int(data['level']) <= 4):
                return jsonify({'error': 'Level must be between 1 and 4'}), 400
            update_fields.append('level = ?')
            values.append(data['level'])
        
        if 'settings' in data:
            update_fields.append('settings = ?')
            values.append(json.dumps(data['settings']))
        
        if update_fields:
            values.append(user_id)
            cursor.execute(f'''
                UPDATE users SET {', '.join(update_fields)}
                WHERE id = ?
            ''', values)
            conn.commit()
        
        conn.close()
        return jsonify({'message': 'Profile updated successfully'})

# Simple test endpoint
@app.route('/api/test', methods=['GET', 'POST'])
def test_endpoint():
    return jsonify({
        'success': True,
        'message': 'Test endpoint working',
        'ai_response': 'Hello! I am your AI tutor. How can I help you today?',
        'farsi_translation': 'سلام! من معلم هوشمند شما هستم. چطور می‌تونم کمکتون کنم؟'
    })

# Translation endpoint
@app.route('/api/translate', methods=['POST'])
@rate_limit('default')
@handle_errors
def translate_text():
    data = request.get_json()
    
    if 'text' not in data:
        return jsonify({'error': 'Missing required field: text'}), 400
    
    text = data['text']
    source_lang = data.get('source', 'en')
    target_lang = data.get('target', 'fa')
    
    if source_lang == 'en' and target_lang == 'fa':
        translation = translation_service.translate_english_to_farsi(text)
    elif source_lang == 'fa' and target_lang == 'en':
        translation = translation_service.translate_farsi_to_english(text)
    else:
        return jsonify({'error': 'Unsupported language pair'}), 400
    
    return jsonify({
        'original': text,
        'translation': translation,
        'source_lang': source_lang,
        'target_lang': target_lang
    })

# Text-to-Speech endpoint
@app.route('/api/tts', methods=['POST'])
@rate_limit('voice_processing')
@handle_errors
def text_to_speech():
    data = request.get_json()
    
    if 'text' not in data:
        return jsonify({'error': 'Missing required field: text'}), 400
    
    text = data['text']
    language = data.get('language', 'en')
    
    audio_data = voice_service.generate_speech(text, language)
    
    if audio_data:
        return send_file(
            audio_data,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='speech.wav'
        )
    else:
        return jsonify({'error': 'Failed to generate speech'}), 500

# Speech-to-Text endpoint (Web-based unlimited STT)
@app.route('/api/stt', methods=['POST'])
@rate_limit('voice_processing')
@handle_errors
def speech_to_text():
    # Check if this is a request to start/stop web-based STT
    action = request.form.get('action', 'file')
    language = request.form.get('language', 'en')
    timeout = int(request.form.get('timeout', '10'))
    
    if action == 'microphone':
        # Use web-based STT for live microphone input
        logger.info("Using web-based STT service for microphone input")
        
        # Perform web-based speech recognition (service already initialized at startup)
        result = web_stt_service.transcribe_speech(language, timeout)
        return jsonify(result)
    
    elif action == 'file' and 'audio' in request.files:
        # Handle audio file uploads using traditional methods
        audio_file = request.files['audio']
        expected_text = request.form.get('expected_text', '')
        
        logger.info("Processing audio file upload")
        
        # Use web STT service for audio file transcription as well
        logger.info("Processing audio file with web STT service")
        
        # For audio file uploads, we'll save the file and point user to microphone option
        # since web STT service is designed for live microphone input
        result = {
            'success': False,
            'text': '',
            'error': 'AUDIO_FILE_NOT_SUPPORTED_BY_WEB_STT',
            'message': 'Audio file uploads are not supported with web-based STT. Please use the microphone recording feature instead.',
            'alternative': 'Use action=microphone for live speech recording',
            'suggestion': 'Click the microphone button in the interface to record speech directly'
        }
        
        return jsonify(result)
    
    else:
        return jsonify({
            'success': False,
            'error': 'INVALID_REQUEST',
            'message': 'Invalid STT request. Use action=microphone for live input or action=file with audio file',
            'supported_actions': ['microphone', 'file'],
            'examples': {
                'microphone': 'POST with action=microphone&language=en&timeout=10',
                'file': 'POST with action=file and audio file in form data'
            }
        }), 400

# Web STT Service Management endpoint
@app.route('/api/stt/status', methods=['GET'])
@handle_errors
def web_stt_status():
    """Get status of web-based STT service"""
    status = web_stt_service.get_service_status()
    return jsonify(status)

@app.route('/api/stt/initialize', methods=['POST'])
@handle_errors  
def initialize_web_stt():
    """Initialize web-based STT service"""
    # Import configuration for STT headless setting
    from chatbot_config import ChatbotConfig
    
    # Use configuration setting or request parameter
    if request.is_json and 'headless' in request.json:
        headless = request.json.get('headless', True)
    else:
        headless = ChatbotConfig.STT_HEADLESS  # Use config setting
    
    if web_stt_service.is_ready():
        return jsonify({
            'success': True,
            'message': 'Web STT service already initialized',
            'headless_mode': headless,
            'status': web_stt_service.get_service_status()
        })
    
    success = web_stt_service.initialize(headless=headless)
    
    if success:
        return jsonify({
            'success': True,
            'message': f'Web STT service initialized successfully (headless: {headless})',
            'headless_mode': headless,
            'status': web_stt_service.get_service_status()
        })
    else:
        return jsonify({
            'success': False,
            'error': 'INITIALIZATION_FAILED',
            'message': 'Failed to initialize web STT service',
            'headless_mode': headless,
            'status': web_stt_service.get_service_status()
        }), 500

@app.route('/api/stt/cleanup', methods=['POST'])
@handle_errors
def cleanup_web_stt():
    """Clean up web-based STT service"""
    web_stt_service.cleanup()
    return jsonify({
        'success': True,
        'message': 'Web STT service cleaned up successfully'
    })

# New STT endpoints for start/stop recording control
@app.route('/api/stt/start', methods=['POST'])
@rate_limit('voice_processing')
@handle_errors
def start_stt_recording():
    """Start STT recording - corresponds to pressing hold-to-speak button"""
    data = request.get_json() or {}
    language = data.get('language', 'en')
    
    logger.info(f"🎤 Voice recording requested")
    
    # Initialize STT service if not ready (should be rare since we pre-initialize)
    if not web_stt_service.is_ready():
        logger.info("STT service not ready, quick-initializing...")
        init_success = web_stt_service.initialize()
        if not init_success:
            logger.error("❌ Failed to initialize STT service")
            return jsonify({
                'success': False,
                'message': 'Voice recording service unavailable',
                'recording': False
            }), 500
    
    # Check if already recording
    if web_stt_service.is_recording_active():
        logger.debug("Recording already active")
        return jsonify({
            'success': True,
            'message': 'Recording already in progress',
            'recording': True
        })
    
    result = web_stt_service.start_recording(language)
    
    if result['success']:
        logger.info(f"✅ Voice recording started")
    else:
        logger.error(f"❌ Voice recording failed: {result.get('message', 'Unknown error')}")
    
    return jsonify(result)

@app.route('/api/stt/stop', methods=['POST'])
@rate_limit('voice_processing')
@handle_errors
def stop_stt_recording():
    """Stop STT recording and get transcribed text - corresponds to releasing hold-to-speak button"""
    logger.info("⏹️ Stopping STT recording")
    
    if not web_stt_service.is_ready():
        logger.error("❌ STT service not initialized when trying to stop recording")
        return jsonify({
            'success': False,
            'text': '',
            'message': 'STT service not initialized',
            'recording': False
        }), 400
    
    # Check if recording is actually active
    if not web_stt_service.is_recording_active():
        logger.warning("⚠️ Stop requested but no recording in progress")
        # Try to get any current text anyway (might have been recording externally)
        current_text = web_stt_service.get_current_text()
        return jsonify({
            'success': False,
            'text': current_text,
            'message': 'No recording in progress',
            'recording': False,
            'note': 'Returned any available text'
        })
    
    result = web_stt_service.stop_recording()
    
    if result['success']:
        logger.info(f"✅ STT recording stopped, transcription: '{result.get('text', '')}'")
    else:
        logger.error(f"❌ Failed to stop STT recording: {result.get('message', 'Unknown error')}")
    
    return jsonify(result)

@app.route('/api/stt/current-text', methods=['GET'])
@handle_errors
def get_current_stt_text():
    """Get current transcribed text without stopping recording (for real-time display)"""
    if not web_stt_service.is_ready():
        return jsonify({
            'text': '',
            'recording': False
        })
    
    current_text = web_stt_service.get_current_text()
    is_recording = web_stt_service.is_recording_active()
    
    return jsonify({
        'text': current_text,
        'recording': is_recording
    })

@app.route('/api/stt/recording-status', methods=['GET'])
@handle_errors
def get_stt_recording_status():
    """Check if STT recording is currently active"""
    if not web_stt_service.is_ready():
        return jsonify({
            'recording': False,
            'service_ready': False
        })
    
    is_recording = web_stt_service.is_recording_active()
    
    return jsonify({
        'recording': is_recording,
        'service_ready': True
    })

# Configuration management endpoints
@app.route('/api/config/headless', methods=['GET'])
@handle_errors
def get_headless_config():
    """Get current headless mode configuration"""
    from chatbot_config import ChatbotConfig
    return jsonify({
        'chatbot_headless': ChatbotConfig.CHATBOT_HEADLESS,
        'stt_headless': ChatbotConfig.STT_HEADLESS,
        'legacy_selenium_headless': ChatbotConfig.SELENIUM_HEADLESS
    })

@app.route('/api/config/headless', methods=['POST'])
@handle_errors
def set_headless_config():
    """Set headless mode configuration"""
    from chatbot_config import ChatbotConfig
    
    data = request.get_json()
    response = {'success': True, 'changes': []}
    
    if 'chatbot_headless' in data:
        ChatbotConfig.set_chatbot_headless(data['chatbot_headless'])
        response['changes'].append(f"AI Chatbot headless: {data['chatbot_headless']}")
    
    if 'stt_headless' in data:
        ChatbotConfig.set_stt_headless(data['stt_headless'])
        response['changes'].append(f"STT headless: {data['stt_headless']}")
    
    if 'enable_debug' in data and data['enable_debug']:
        ChatbotConfig.enable_debug_mode()
        response['changes'].append("Debug mode enabled (both services visible)")
    
    response['current_config'] = {
        'chatbot_headless': ChatbotConfig.CHATBOT_HEADLESS,
        'stt_headless': ChatbotConfig.STT_HEADLESS
    }
    
    return jsonify(response)

# Pronunciation checking endpoint
@app.route('/api/pronunciation', methods=['POST'])
@rate_limit('voice_processing')
@handle_errors
def check_pronunciation():
    if 'audio' not in request.files:
        return jsonify({'error': 'Missing audio file'}), 400
    
    audio_file = request.files['audio']
    expected_text = request.form.get('expected_text', '')
    
    if not expected_text:
        return jsonify({'error': 'Missing expected_text'}), 400
    
    result = voice_service.check_pronunciation(audio_file, expected_text)
    
    return jsonify(result)

# Voice service status endpoint
@app.route('/api/voice/status', methods=['GET'])
@handle_errors
def voice_service_status():
    """Get the status of voice services"""
    try:
        # Get web STT service status
        web_stt_status = web_stt_service.get_service_status()
        mock_status = voice_service.get_voice_settings()
        
        return jsonify({
            'web_stt': web_stt_status,
            'mock_service': mock_status,
            'active_service': 'web_stt',
            'speech_recognition_upgrade': {
                'service': 'SpeechTexter Voice Input (Web-based)',
                'daily_limit': 'Unlimited usage',
                'per_request_limit': 'No time limits',
                'cost': 'Completely free',
                'account_required': 'No',
                'api_key_required': 'No',
                'browser_required': 'Yes (automated)',
                'initialization': 'Browser opens at app startup for immediate use'
            },
            'current_setup': {
                'name': 'SpeechTexter STT',
                'status': 'Ready' if web_stt_service.is_ready() else 'Not initialized',
                'description': 'Unlimited voice recognition via SpeechTexter',
                'pros': ['Unlimited usage', 'No API limits', 'High accuracy', '70+ languages', 'Real-time transcription'],
                'cons': ['Requires browser automation', 'Browser window stays open during use'],
                'browser_behavior': 'Browser window opens at startup and stays open for better performance'
            },
            'usage_info': {
                'current_limits': 'No limits - unlimited voice recordings',
                'upgrade_note': 'Upgraded from limited SpeechRecognition API to unlimited Google Translate STT',
                'no_costs': 'No credit card or payment required ever',
                'reliability': 'Uses Google Translate voice input automation'
            }
        })
    except Exception as e:
        logger.error(f"Error getting voice service status: {e}")
        return jsonify({'error': 'Failed to get service status'}), 500

# Test SpeechTexter STT endpoint
@app.route('/api/test-speechtexter', methods=['POST'])
@handle_errors
def test_speechtexter():
    """
    Test endpoint to verify SpeechTexter is working and visible
    """
    try:
        logger.info("🧪 Testing SpeechTexter STT service...")
        
        # Get test parameters
        data = request.get_json() or {}
        timeout = data.get('timeout', 5)  # Shorter timeout for testing
        language = data.get('language', 'en')
        
        # Test the service
        if not web_stt_service.is_ready():
            return jsonify({
                'success': False,
                'error': 'SpeechTexter service not initialized',
                'message': 'Please restart the server to initialize SpeechTexter'
            }), 500
        
        logger.info(f"🎤 Starting {timeout}-second SpeechTexter test...")
        logger.info("📺 Watch the SpeechTexter browser window for visual confirmation!")
        
        # Perform the test transcription
        result = web_stt_service.transcribe_speech(language, timeout)
        
        # Add debugging information
        result['test_info'] = {
            'service': 'SpeechTexter STT',
            'browser_visible': not web_stt_service.speechtexter_stt.headless,
            'url': web_stt_service.speechtexter_stt.speechtexter_url,
            'test_duration': timeout,
            'instructions': [
                '1. Watch the SpeechTexter browser window',
                '2. The microphone button should be highlighted in RED when clicked',
                '3. The text editor should be highlighted in BLUE',
                '4. Speak clearly when recording starts',
                '5. Text should appear in real-time as you speak'
            ]
        }
        
        logger.info(f"🧪 SpeechTexter test completed: {result}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ SpeechTexter test failed: {e}")
        return jsonify({
            'success': False,
            'error': 'Test failed',
            'message': str(e)
        }), 500

# Debug SpeechTexter elements endpoint
@app.route('/api/debug-speechtexter', methods=['GET'])
@handle_errors
def debug_speechtexter():
    """
    Debug endpoint to check SpeechTexter page elements
    """
    try:
        logger.info("🔍 Debugging SpeechTexter page elements...")
        
        if not web_stt_service.is_ready():
            return jsonify({
                'success': False,
                'error': 'SpeechTexter service not initialized',
                'message': 'Please restart the server to initialize SpeechTexter'
            }), 500
        
        # Test page elements
        result = web_stt_service.speechtexter_stt.test_page_elements()
        
        logger.info(f"🔍 Debug result: {result}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ SpeechTexter debug failed: {e}")
        return jsonify({
            'success': False,
            'error': 'Debug failed',
            'message': str(e)
        }), 500

# Image generation endpoint
@app.route('/api/generate-image', methods=['POST'])
@rate_limit('image_generation')  # 10 requests per 5 minutes for image generation
@handle_errors
def generate_image():
    data = request.get_json()
    
    if 'prompt' not in data:
        return jsonify({'error': 'Missing required field: prompt'}), 400
    
    prompt = data['prompt']
    style = data.get('style', 'educational')
    
    # Image service temporarily disabled due to PIL dependency
    # image_url = image_service.generate_image(prompt, style)
    
    # Return a placeholder response
    return jsonify({'error': 'Image generation temporarily disabled'}), 503

# Progress tracking endpoints
@app.route('/api/progress', methods=['GET', 'POST'])
@rate_limit('default')
@handle_errors
def handle_progress():
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        progress_data = progress_tracker.get_user_progress(user_id)
        
        return jsonify(progress_data)
    
    elif request.method == 'POST':
        # Handle conversation completion XP awarding
        data = request.get_json()
        
        required_fields = ['user_id', 'action', 'topic']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        user_id = data['user_id']
        action = data['action']
        topic = data['topic']
        duration_minutes = data.get('duration_minutes', 0)
        message_count = data.get('message_count', 0)
        
        if action == 'complete_conversation':
            try:
                # Award XP for completing a conversation
                tracker = ProgressTracker(db_path)
                
                # Award base completion XP
                base_xp_result = tracker.add_experience_points(user_id, 'conversation_complete')
                base_xp = base_xp_result.get('xp_gained', 25)
                
                # Award bonus XP based on duration and engagement
                bonus_xp = 0
                if duration_minutes >= 10:  # Minimum meaningful conversation time
                    bonus_xp += min(duration_minutes * 2, 40)  # Up to 40 bonus XP for longer conversations
                
                if message_count >= 10:  # Good engagement
                    bonus_xp += min(message_count, 30)  # Up to 30 bonus XP for message count
                
                # Award bonus XP using a custom action (if we need to add it to XP_REWARDS)
                if bonus_xp > 0:
                    # Calculate bonus multiplier based on bonus amount
                    bonus_multiplier = max(1, bonus_xp // 5)  # Each 5 bonus XP = 1 multiplier
                    bonus_result = tracker.add_experience_points(user_id, 'help_other', bonus_multiplier)
                    actual_bonus = bonus_result.get('xp_gained', 0)
                else:
                    actual_bonus = 0
                
                logger.info(f"Awarded {base_xp + actual_bonus} XP to user {user_id} for completing {topic} conversation")
                
                return jsonify({
                    'success': True,
                    'base_xp': base_xp,
                    'bonus_xp': actual_bonus,
                    'total_xp': base_xp + actual_bonus,
                    'message': 'Conversation completed successfully'
                })
                
            except Exception as e:
                logger.error(f"Error awarding conversation completion XP: {e}")
                return jsonify({'error': 'Failed to award XP'}), 500
        else:
            # Redirect to update endpoint for other actions
            result = progress_tracker.update_progress(user_id, topic, action)
            return jsonify(result)

@app.route('/api/progress/update', methods=['POST'])
@rate_limit('default')
@handle_errors
def update_progress():
    data = request.get_json()
    
    required_fields = ['user_id', 'topic', 'action']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    user_id = data['user_id']
    topic = data['topic']
    action = data['action']  # 'complete_topic', 'practice_session', 'learn_phrase'
    
    result = progress_tracker.update_progress(user_id, topic, action)
    
    return jsonify(result)

@app.route('/api/user-level-info/<user_id>', methods=['GET'])
@rate_limit('default')
@handle_errors
def get_user_level_info(user_id):
    """Get user's level and experience information"""
    try:
        level_info = progress_tracker.get_user_level_info(user_id)
        return jsonify(level_info)
    except Exception as e:
        logger.error(f"Error getting user level info: {str(e)}")
        return jsonify({'error': 'Failed to get level info'}), 500

@app.route('/api/track-message', methods=['POST'])
@rate_limit('default')
@handle_errors
def track_message():
    """Track conversation message and award XP"""
    data = request.get_json()
    
    if not data or 'user_id' not in data:
        return jsonify({'error': 'Missing user_id'}), 400
    
    user_id = data['user_id']
    topic_id = data.get('topic_id')
    message_type = data.get('type', 'text')  # 'text' or 'voice'
    
    try:
        if message_type == 'voice':
            result = progress_tracker.track_voice_message(user_id, topic_id)
        else:
            result = progress_tracker.track_conversation_message(user_id, topic_id)
        
        return jsonify({'success': result})
    except Exception as e:
        logger.error(f"Error tracking message: {str(e)}")
        return jsonify({'error': 'Failed to track message'}), 500

@app.route('/api/track-login', methods=['POST'])
@rate_limit('default')
@handle_errors
def track_login():
    """Track daily login and award XP"""
    data = request.get_json()
    
    if not data or 'user_id' not in data:
        logger.warning("Track login called without user_id")
        return jsonify({'error': 'Missing user_id'}), 400
    
    user_id = data['user_id']
    logger.info(f"Tracking daily login for user: {user_id}")
    
    try:
        result = progress_tracker.track_daily_login(user_id)
        logger.info(f"Daily login tracking result for {user_id}: {result}")
        return jsonify({'success': result, 'first_login_today': result})
    except Exception as e:
        logger.error(f"Error tracking login for {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to track login'}), 500

# Daily challenge endpoints
@app.route('/api/daily-challenge', methods=['GET'])
@rate_limit('default')
@handle_errors
def get_daily_challenge():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    
    challenge = progress_tracker.get_daily_challenge(user_id)
    
    return jsonify(challenge)

@app.route('/api/daily-challenge/complete', methods=['POST'])
@rate_limit('default')
@handle_errors
def complete_daily_challenge():
    data = request.get_json()
    
    if 'user_id' not in data:
        return jsonify({'error': 'Missing user_id'}), 400
    
    result = progress_tracker.complete_daily_challenge(data['user_id'])
    
    return jsonify(result)

# Topics endpoint
@app.route('/api/topics', methods=['GET'])
@rate_limit('default')
@handle_errors
def get_topics():
    level = request.args.get('level')
    
    if not level:
        return jsonify({'error': 'Missing level parameter'}), 400
    
    from config import LEVEL_TOPICS, TOPIC_DETAILS
    
    topics = LEVEL_TOPICS.get(str(level), [])
    topic_details = []
    
    for topic in topics:
        details = TOPIC_DETAILS.get(topic, {})
        topic_details.append({
            'id': topic,
            'name': details.get('name', topic.title()),
            'emoji': details.get('emoji', '📚'),
            'farsi': details.get('farsi', '')
        })
    
    return jsonify({
        'level': level,
        'topics': topic_details
    })

# Debug endpoint to get all user data
@app.route('/api/user-progress-all', methods=['GET'])
@rate_limit('default')
@handle_errors
def get_all_user_progress():
    """Get all users and their progress for debugging"""
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all users
            cursor.execute('''
                SELECT u.id, u.name, u.age, u.level, u.created_at,
                       up.level as progress_level, up.experience_points, 
                       up.total_experience, up.created_at as progress_created_at
                FROM users u
                LEFT JOIN user_progress up ON u.id = up.user_id
                ORDER BY u.created_at DESC
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append(dict(row))
            
            return jsonify({
                'success': True,
                'users': users,
                'count': len(users)
            })
            
    except Exception as e:
        logger.error(f"Error getting all user progress: {str(e)}")
        return jsonify({'error': 'Failed to get user progress'}), 500

# Favicon route to prevent 404 errors
@app.route('/favicon.ico')
def favicon():
    return '', 204  # No Content

# Health check endpoint
@app.route('/api/health')
def api_health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected'
    })

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Setup cleanup handler
    import atexit
    def cleanup_on_exit():
        global conversation_ai
        if conversation_ai:
            try:
                conversation_ai.cleanup()
                logger.info("Application cleanup completed")
            except Exception as e:
                logger.error(f"Error during application cleanup: {e}")
    
    atexit.register(cleanup_on_exit)
def cleanup_on_exit():
    """Cleanup function to close browser windows on app shutdown"""
    logger.info("🧹 App shutting down - cleaning up browser windows...")
    try:
        web_stt_service.force_cleanup()
        logger.info("✅ Browser cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def signal_handler(signum, frame):
    """Handle CTRL+C and other termination signals"""
    logger.info("🛑 Received termination signal - shutting down gracefully...")
    cleanup_on_exit()
    exit(0)

# Register cleanup handlers
atexit.register(cleanup_on_exit)
signal.signal(signal.SIGINT, signal_handler)  # CTRL+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

if __name__ == '__main__':
    try:
        # Start the Flask application
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('DEBUG', 'False').lower() == 'true'
        
        logger.info(f"🚀 Starting English Learning App server on port {port}")
        
        if web_stt_initialization_success:
            logger.info("🎤 ✅ SpeechTexter window opened - voice recording ready")
            logger.info("📺 Chrome browser with SpeechTexter should be visible on your screen")
        else:
            logger.warning("🎤 ❌ SpeechTexter window failed to open")
        
        logger.info("🌐 App ready! Open http://localhost:5000 in your browser")
        app.run(host='0.0.0.0', port=port, debug=debug)
    except KeyboardInterrupt:
        logger.info("🛑 Received CTRL+C - shutting down...")
        cleanup_on_exit()
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        cleanup_on_exit()
        raise
