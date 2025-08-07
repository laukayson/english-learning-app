# Flask Application for Render Deployment with Turso Database
# English Learning App - Render + Turso FULL VERSION (with Voice Features!)

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
from datetime import datetime
import logging
from functools import wraps
import time
import hashlib
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration (FULL VERSION)
from config import RENDER_CONFIG, FEATURES, LEVEL_TOPICS, TOPIC_DETAILS, SELENIUM_CONFIG

# Import services
from turso_service import get_db_service
from ai_models import AIModels  # Use original AI models (with Selenium support)
from translation_service import TranslationService
from conversational_ai import ConversationalAI

# Voice and browser services (ENABLED on Render!)
try:
    from voice_service import VoiceService
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    logger.warning("Voice service not available")

try:
    from web_stt_service import get_web_stt_service
    WEB_STT_AVAILABLE = True
except ImportError:
    WEB_STT_AVAILABLE = False
    logger.warning("Web STT service not available")

# Import progress tracker
try:
    from services.progress_tracker import ProgressTracker
    
    # Create a simple progress tracker wrapper for database service
    class DatabaseProgressTracker:
        def __init__(self, db_service):
            self.db_service = db_service
        
        def get_user_progress(self, user_id):
            """Get user progress from database service"""
            try:
                # Use the database service's existing methods
                return self.db_service.get_user_progress(user_id)
            except Exception as e:
                logger.warning(f"Progress tracker error: {e}")
                return {
                    'level': 1,
                    'experience_points': 0,
                    'topics_completed': [],
                    'practice_sessions': 0
                }
        
        def initialize_user_progress(self, user_id, level):
            """Initialize user progress"""
            try:
                return self.db_service.initialize_user_progress(user_id, level)
            except Exception as e:
                logger.warning(f"Progress initialization error: {e}")
                return False
    
    PROGRESS_TRACKER_AVAILABLE = True
except ImportError:
    # Create a fallback progress tracker
    class DatabaseProgressTracker:
        def __init__(self, db_service):
            self.db_service = db_service
        
        def get_user_progress(self, user_id):
            return {
                'level': 1,
                'experience_points': 0,
                'topics_completed': [],
                'practice_sessions': 0
            }
        
        def initialize_user_progress(self, user_id, level):
            return True
    
    PROGRESS_TRACKER_AVAILABLE = False

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

# Initialize services
db_service = get_db_service()
ai_models = AIModels()
translation_service = TranslationService()
conversational_ai = ConversationalAI()
progress_tracker = DatabaseProgressTracker(db_service)
rate_limiter = RateLimiter()

# Initialize voice services if available
voice_service = None
web_stt_service = None

if VOICE_AVAILABLE and FEATURES['voice_features']:
    try:
        voice_service = VoiceService()
        logger.info("✅ Voice service initialized")
    except Exception as e:
        logger.warning(f"Voice service initialization failed: {e}")

if WEB_STT_AVAILABLE and FEATURES['web_stt']:
    try:
        web_stt_service = get_web_stt_service()
        # Don't initialize during startup - do it lazily when first needed
        logger.info("✅ Web STT service created (will initialize on first use)")
    except Exception as e:
        logger.warning(f"Web STT service creation failed: {e}")

# Global conversational AI instance
conversation_ai = None
if FEATURES['selenium_chatbot']:
    try:
        from conversational_ai import ConversationalAI
        conversation_ai = ConversationalAI()
        logger.info("✅ Conversational AI initialized")
    except Exception as e:
        logger.warning(f"Conversational AI initialization failed: {e}")
        conversation_ai = None

# Configure static file serving for frontend
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static frontend files"""
    try:
        frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
        file_path = os.path.join(frontend_dir, filename)
        
        # Security check
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
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
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
        'environment': 'render',
        'database': db_service.health_check(),
        'features': FEATURES,
        'services': {
            'ai_models': ai_models.is_ready(),
            'translation': translation_service.is_ready(),
            'voice': voice_service.is_ready() if voice_service else False,
            'web_stt': web_stt_service is not None,  # Don't call is_ready() until initialized
            'conversation_ai': conversation_ai is not None,
            'database': True
        }
    })

@app.route('/api/chrome-status', methods=['GET'])
def chrome_status():
    """Check Chrome installation status"""
    import shutil
    import os
    import subprocess
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'chrome_binaries': {},
        'environment_vars': {},
        'chrome_version': None,
        'chromedriver_available': False
    }
    
    # Check environment variables
    for env_var in ['GOOGLE_CHROME_BIN', 'CHROMEDRIVER_PATH']:
        status['environment_vars'][env_var] = os.environ.get(env_var, 'Not set')
    
    # Check for Chrome binaries
    chrome_names = ['chromium-browser', 'google-chrome-stable', 'google-chrome', 'chromium']
    for name in chrome_names:
        binary_path = shutil.which(name)
        status['chrome_binaries'][name] = binary_path or 'Not found'
    
    # Check specific paths
    chrome_paths = [
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium',
        '/opt/google/chrome/chrome'
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            status['chrome_binaries'][f'path_{path}'] = 'Found'
        else:
            status['chrome_binaries'][f'path_{path}'] = 'Not found'
    
    # Try to get Chrome version
    for binary in ['chromium-browser', 'google-chrome-stable', 'google-chrome']:
        try:
            result = subprocess.run([binary, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                status['chrome_version'] = result.stdout.strip()
                break
        except:
            continue
    
    # Check if chromedriver is available
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        chromedriver_path = ChromeDriverManager().install()
        status['chromedriver_available'] = True
        status['chromedriver_path'] = chromedriver_path
    except Exception as e:
        status['chromedriver_error'] = str(e)
    
    return jsonify(status)

@app.route('/api/test-db', methods=['GET'])
def test_database():
    """Test database connection and show all users"""
    try:
        # Get all users from database
        query = 'SELECT id, username, name, age, level, created_at FROM users ORDER BY created_at DESC LIMIT 10'
        users = db_service.execute_query(query)
        
        return jsonify({
            'status': 'success',
            'database_type': 'turso' if db_service.is_turso else 'sqlite',
            'user_count': len(users),
            'recent_users': users,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

# Chat initialization endpoint
@app.route('/api/chat/init-topic', methods=['POST'])
@rate_limit('default')
@handle_errors
def init_topic():
    """Initialize chat topic and return welcome message"""
    data = request.json
    topic = data.get('topic', 'general')
    user_level = data.get('user_level', 'beginner')
    user_id = data.get('user_id')
    
    # Get conversation starter for the topic
    try:
        conversation_starter = conversational_ai.get_topic_starter(topic, user_level)
        
        return jsonify({
            'response': conversation_starter,
            'topic': topic,
            'user_level': user_level,
            'session_id': f"session_{user_id}_{topic}_{int(time.time())}" if user_id else None
        })
    except Exception as e:
        logger.error(f"Error initializing topic: {e}")
        return jsonify({
            'response': f"Welcome! Let's practice {topic}. How are you today?",
            'topic': topic,
            'user_level': user_level
        })

# Chat endpoint (FULL VERSION with AI)
@app.route('/api/chat', methods=['POST'])
@rate_limit('default')
@handle_errors
def chat():
    """Handle chat messages and return AI responses"""
    data = request.json
    message = data.get('message', '')
    topic = data.get('topic', 'general')
    user_id = data.get('user_id')
    user_level = data.get('user_level', 'beginner')
    history = data.get('history', [])
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Get user's proficiency level from database if user is logged in
    if user_id and user_level == 'beginner':
        try:
            user = db_service.get_user_by_id(user_id)
            if user:
                user_level = user.get('level', 1)
        except Exception as e:
            logger.warning(f"Failed to get user level: {e}")
    
    # Use conversational AI if available, otherwise fallback to basic AI
    try:
        if conversation_ai:
            ai_response = conversation_ai.get_response(message, topic, history, user_level)
        else:
            ai_response = ai_models.generate_response(message, user_level, topic, {'history': history})
    except Exception as e:
        logger.error(f"AI response error: {e}")
        ai_response = "I'm sorry, I'm having trouble responding right now. Could you try again?"
    
    # Generate Farsi translation
    try:
        farsi_translation = translation_service.translate_english_to_farsi(ai_response)
    except Exception as e:
        logger.warning(f"Failed to translate to Farsi: {e}")
        farsi_translation = "ترجمه در دسترس نیست"
    
    return jsonify({
        'success': True,
        'ai_response': ai_response,
        'farsi_translation': farsi_translation,
        'topic': topic,
        'timestamp': datetime.now().isoformat()
    })

# Chat session end endpoint
@app.route('/api/chat/session/end', methods=['POST'])
@rate_limit('default')
@handle_errors
def end_chat_session():
    """End chat session"""
    data = request.json
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    
    # For now, just return success
    return jsonify({
        'success': True,
        'message': 'Session ended successfully'
    })

# STT endpoints (ENABLED on Render!)
@app.route('/api/stt', methods=['POST'])
@rate_limit('voice_processing')
@handle_errors
def speech_to_text():
    """Speech-to-text endpoint using web-based STT"""
    if not web_stt_service or not FEATURES['web_stt']:
        return jsonify({
            'error': 'Voice features not available',
            'message': 'Web STT service not initialized'
        }), 501
    
    action = request.form.get('action', 'microphone')
    language = request.form.get('language', 'en')
    timeout = int(request.form.get('timeout', '10'))
    
    if action == 'microphone':
        result = web_stt_service.transcribe_speech(language, timeout)
        return jsonify(result)
    else:
        return jsonify({
            'success': False,
            'error': 'Only microphone action supported',
            'message': 'Use action=microphone for live speech recording'
        }), 400

@app.route('/api/stt/start', methods=['POST'])
@rate_limit('voice_processing')
@handle_errors
def start_stt_recording():
    """Start STT recording"""
    if not web_stt_service or not FEATURES['web_stt']:
        return jsonify({
            'success': True,
            'message': 'Voice recording simulated (STT service not available)',
            'recording': True
        })
    
    # Initialize STT service lazily on first use
    if not hasattr(web_stt_service, 'is_initialized') or not web_stt_service.is_initialized:
        logger.info("Initializing Web STT service on first use...")
        try:
            if os.environ.get('RENDER'):
                web_stt_service.initialize(headless=True)
            else:
                web_stt_service.initialize(headless=False)
        except Exception as e:
            logger.error(f"STT initialization failed: {e}")
            return jsonify({
                'success': False,
                'error': 'STT service initialization failed'
            })
    
    data = request.get_json() or {}
    language = data.get('language', 'en')
    
    result = web_stt_service.start_recording(language)
    return jsonify(result)

@app.route('/api/stt/stop', methods=['POST'])
@rate_limit('voice_processing')
@handle_errors
def stop_stt_recording():
    """Stop STT recording"""
    if not web_stt_service or not FEATURES['web_stt']:
        return jsonify({
            'success': True,
            'message': 'Voice recording simulated (STT service not available)',
            'recording': False,
            'transcript': 'Voice features will be available soon!'
        })
    
    result = web_stt_service.stop_recording()
    return jsonify(result)

# TTS endpoint (if voice service available)
@app.route('/api/tts', methods=['POST'])
@rate_limit('voice_processing')
@handle_errors
def text_to_speech():
    """Text-to-speech endpoint"""
    if not voice_service or not FEATURES['voice_features']:
        return jsonify({
            'error': 'Voice features not available',
            'message': 'TTS service not initialized'
        }), 501
    
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

# API user endpoints
@app.route('/api/user', methods=['GET', 'POST'])
@handle_errors
def api_user():
    """Handle general /api/user requests"""
    if request.method == 'GET':
        return jsonify({
            'message': 'User API endpoints',
            'available_endpoints': {
                'register': '/api/user/register (POST)',
                'login': '/api/user/login (POST)'
            }
        })
    elif request.method == 'POST':
        # Redirect POST requests to register endpoint
        return register_user()

# User registration endpoint (same as before)
@app.route('/api/user/register', methods=['POST'])
@rate_limit('default')
@handle_errors
def register_user():
    """Register a new user"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    required_fields = ['username', 'password', 'name', 'age', 'level']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate input
    username = data['username'].strip()
    if len(username) < 3 or len(username) > 50:
        return jsonify({'error': 'Username must be between 3 and 50 characters'}), 400
    
    password = data['password']
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long'}), 400
    
    try:
        age = int(data['age'])
        if not (5 <= age <= 100):
            return jsonify({'error': 'Age must be between 5 and 100'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Age must be a valid number'}), 400
    
    try:
        level = int(data['level'])
        if not (1 <= level <= 4):
            return jsonify({'error': 'Level must be between 1 and 4'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Level must be a valid number'}), 400
    
    # Check if username already exists
    try:
        existing_user = db_service.get_user_by_username(username)
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 409
    except Exception as e:
        logger.error(f"Error checking existing user: {e}")
        return jsonify({'error': 'Database error during user check'}), 500
    
    # Create new user
    user_id = f"user_{int(time.time() * 1000)}"
    hashed_password = hash_password(password)
    
    # Create user in database
    try:
        success = db_service.create_user(user_id, username, hashed_password, data['name'], age, level)
        logger.info(f"Database create_user result: {success}")
        
        if not success:
            logger.error("Database create_user returned False")
            return jsonify({'error': 'Failed to create user in database'}), 500
        
        # Verify user was created by trying to retrieve it
        try:
            created_user = db_service.get_user_by_username(username)
            if created_user:
                logger.info(f"User verification successful: {created_user['username']}")
            else:
                logger.error("User verification failed - user not found after creation")
                return jsonify({'error': 'User creation verification failed'}), 500
        except Exception as verify_error:
            logger.error(f"Error verifying user creation: {verify_error}")
        
        # Initialize user progress
        try:
            db_service.initialize_user_progress(user_id, level)
            logger.info(f"User progress initialized for {username}")
        except Exception as progress_error:
            logger.warning(f"Failed to initialize user progress: {progress_error}")
        
        logger.info(f"✅ User registered successfully: {username}")
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id,
            'username': username
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating user in database: {e}")
        return jsonify({'error': 'Database error during user creation'}), 500

# User login endpoint (same as before)
@app.route('/api/user/login', methods=['POST'])
@rate_limit('default')
@handle_errors
def login_user():
    """Login user"""
    data = request.get_json()
    
    if 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password are required'}), 400
    
    username = data['username'].strip()
    password = data['password']
    
    # Get user by username
    user = db_service.get_user_by_username(username)
    
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Verify password
    if not verify_password(user['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Update last active timestamp
    db_service.update_user_last_active(user['id'])
    
    return jsonify({
        'user_id': user['id'],
        'username': user['username'],
        'name': user['name'],
        'age': user['age'],
        'level': user['level'],
        'settings': json.loads(user.get('settings', '{}')),
        'last_active': user.get('last_active')
    })

# User verification endpoint
@app.route('/api/user/verify', methods=['POST'])
@rate_limit('default')
@handle_errors
def verify_user():
    """Verify if a user exists"""
    data = request.get_json()
    
    if 'username' not in data:
        return jsonify({'error': 'Username is required'}), 400
    
    username = data['username'].strip()
    user = db_service.get_user_by_username(username)
    
    if user:
        return jsonify({'user_exists': True, 'user_id': user['id']})
    else:
        return jsonify({'user_exists': False})

# User level info endpoint
@app.route('/api/user-level-info/<user_id>', methods=['GET'])
@rate_limit('default')
@handle_errors
def get_user_level_info(user_id):
    """Get user level and progress information"""
    try:
        user = db_service.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        progress = db_service.get_user_progress(user_id)
        
        return jsonify({
            'user_id': user['id'],
            'level': user['level'],
            'level_name': f"Level {user['level']}",
            'experience_points': progress.get('experience_points', 0),
            'topics_completed': progress.get('topics_completed', []),
            'practice_sessions': progress.get('practice_sessions', 0)
        })
    except Exception as e:
        logger.error(f"Error getting user level info: {e}")
        return jsonify({'error': 'Failed to get user info'}), 500

# Login tracking endpoint
@app.route('/api/track-login', methods=['POST'])
@rate_limit('default')
@handle_errors
def track_login():
    """Track user login for daily bonus"""
    data = request.get_json()
    
    if 'user_id' not in data:
        return jsonify({'error': 'User ID is required'}), 400
    
    user_id = data['user_id']
    
    # For now, just return success - implement actual tracking later
    return jsonify({
        'success': True,
        'first_login_today': True,
        'bonus_xp': 10
    })

# Message tracking endpoint
@app.route('/api/track-message', methods=['POST'])
@rate_limit('default')
@handle_errors
def track_message():
    """Track message for progress"""
    data = request.get_json()
    
    # For now, just return success - implement actual tracking later
    return jsonify({'success': True})

# Translation endpoint (same as before)
@app.route('/api/translate', methods=['POST'])
@rate_limit('default')
@handle_errors
def translate_text():
    """Translate text between English and Farsi"""
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

# Progress tracking endpoints (same as before)
@app.route('/api/progress', methods=['GET'])
@rate_limit('default')
@handle_errors
def get_progress():
    """Get user progress"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    
    progress_data = progress_tracker.get_user_progress(user_id)
    
    return jsonify(progress_data)

# Topics endpoint (same as before)
@app.route('/api/topics', methods=['GET'])
@rate_limit('default')
@handle_errors
def get_topics():
    """Get topics for a specific level"""
    level = request.args.get('level')
    
    if not level:
        return jsonify({'error': 'Missing level parameter'}), 400
    
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

# Feature status endpoint
@app.route('/api/features', methods=['GET'])
def get_features():
    """Get available features for this deployment"""
    return jsonify({
        'platform': 'render',
        'database': 'turso',
        'features': FEATURES,
        'voice_status': {
            'web_stt_available': web_stt_service is not None,
            'voice_service_available': voice_service is not None,
            'conversation_ai_available': conversation_ai is not None
        },
        'available_features': [
            'Text-based chat with AI tutor',
            'Advanced conversational AI',
            'Voice recognition (STT)',
            'Text-to-speech (TTS)',
            'English-Farsi translation',
            'Progress tracking and gamification',
            'User registration and login',
            'Topic-based learning'
        ]
    })

# Favicon route
@app.route('/favicon.ico')
def favicon():
    return '', 204

# API health check
@app.route('/api/health')
def api_health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': db_service.health_check()
    })

@app.route('/api/admin/rate-limit-reset', methods=['POST'])
def reset_rate_limit():
    """Reset rate limiting for development purposes"""
    try:
        data = request.get_json() or {}
        client_ip = data.get('client_ip') or request.remote_addr
        
        # Reset the client's rate limiting data
        rate_limiter.reset_client(client_ip)
        
        return jsonify({
            'success': True,
            'message': f'Rate limiting reset for client {client_ip}',
            'client_ip': client_ip
        })
    except Exception as e:
        logger.error(f"Error resetting rate limit: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/rate-limit-status', methods=['GET'])
def get_rate_limit_status():
    """Get current rate limiting status"""
    try:
        client_ip = request.remote_addr
        status = rate_limiter.get_client_status(client_ip)
        
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = RENDER_CONFIG['port']
    host = RENDER_CONFIG['host']
    debug = RENDER_CONFIG['debug']
    
    logger.info(f"🚀 Starting English Learning App (Render + Turso FULL VERSION) on {host}:{port}")
    logger.info(f"🗄️ Database: {'Turso' if db_service.is_turso else 'SQLite'}")
    logger.info(f"🎯 Features: {', '.join([k for k, v in FEATURES.items() if v])}")
    logger.info(f"🎤 Voice Features: {'Enabled' if FEATURES['voice_features'] else 'Disabled'}")
    logger.info(f"🤖 Selenium Features: {'Enabled' if FEATURES['selenium_chatbot'] else 'Disabled'}")
    
    app.run(host=host, port=port, debug=debug)
