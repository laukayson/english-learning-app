# Flask Application for Render Deployment with Turso Database
# English Learning App - Render + Turso version

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

# Import configuration (FULL VERSION)
from config_render_full import RENDER_CONFIG, FEATURES, LEVEL_TOPICS, TOPIC_DETAILS, SELENIUM_CONFIG

# Import services
from turso_service import get_db_service
from ai_models import AIModels  # Use original AI models (with Selenium support)
from translation_service import TranslationService

# Voice and browser services (ENABLED on Render!)
try:
    from voice_service import VoiceService
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    # logger.warning("Voice service not available") - defined later

try:
    from web_stt_service import get_web_stt_service
    WEB_STT_AVAILABLE = True
except ImportError:
    WEB_STT_AVAILABLE = False
    # logger.warning("Web STT service not available") - defined later

# Import progress tracker (will be updated for Turso)
try:
    from services.progress_tracker import ProgressTracker
except ImportError:
    # Create a mock progress tracker if not available
    class ProgressTracker:
        def __init__(self, db_service):
            self.db_service = db_service
        
        def get_user_progress(self, user_id):
            return self.db_service.get_user_progress(user_id)
        
        def initialize_user_progress(self, user_id, level):
            return self.db_service.initialize_user_progress(user_id, level)

from rate_limiter import RateLimiter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log warnings for missing services after logger is configured
if not VOICE_AVAILABLE:
    logger.warning("Voice service not available")
if not WEB_STT_AVAILABLE:
    logger.warning("Web STT service not available")

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
progress_tracker = ProgressTracker(db_service)
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
        # Initialize with headless mode for Render
        if os.environ.get('RENDER'):
            web_stt_service.initialize(headless=True)
        logger.info("✅ Web STT service initialized")
    except Exception as e:
        logger.warning(f"Web STT service initialization failed: {e}")

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
            'web_stt': web_stt_service.is_ready() if web_stt_service else False,
            'conversation_ai': conversation_ai is not None,
            'database': True
        }
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
            'success': False,
            'message': 'Voice features not available'
        }), 501
    
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
            'success': False,
            'message': 'Voice features not available'
        }), 501
    
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

# User registration endpoint
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
    existing_user = db_service.get_user_by_username(username)
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 409
    
    # Create new user
    user_id = f"user_{int(time.time() * 1000)}"
    hashed_password = hash_password(password)
    
    # Create user in database
    success = db_service.create_user(user_id, username, hashed_password, data['name'], age, level)
    
    if success:
        # Initialize user progress
        progress_tracker.initialize_user_progress(user_id, level)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'username': username,
            'name': data['name'],
            'age': age,
            'level': level,
            'message': 'User registered successfully'
        })
    else:
        return jsonify({'error': 'Failed to create user'}), 500

# User login endpoint
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

# Translation endpoint
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

# Progress tracking endpoints
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

# Topics endpoint
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
        'limitations': {
            'voice_features': 'Disabled - browser automation not supported',
            'selenium_features': 'Disabled - browser automation not supported',
            'image_generation': 'Disabled - dependency limitations'
        },
        'available_features': [
            'Text-based chat with AI tutor',
            'English-Farsi translation',
            'Progress tracking and gamification',
            'User registration and login',
            'Topic-based learning'
        ]
    })

# Disabled endpoints (for compatibility)
@app.route('/api/stt', methods=['POST'])
@app.route('/api/stt/start', methods=['POST'])
@app.route('/api/stt/stop', methods=['POST'])
def disabled_stt():
    """STT endpoints disabled on Render"""
    return jsonify({
        'error': 'Voice features disabled',
        'message': 'Speech-to-text is not available on Render deployment',
        'alternative': 'Use text input for conversations'
    }), 501

@app.route('/api/tts', methods=['POST'])
def disabled_tts():
    """TTS endpoint disabled on Render"""
    return jsonify({
        'error': 'Voice features disabled',
        'message': 'Text-to-speech is not available on Render deployment'
    }), 501

# Favicon route
@app.route('/favicon.ico')
def favicon():
    return '', 204

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

# Debug endpoint for database repair
@app.route('/api/debug/repair-db')
def repair_database():
    """Repair and verify database structure"""
    repair_info = {
        'timestamp': datetime.now().isoformat(),
        'operations': []
    }
    
    try:
        # Step 1: Check if user_progress table exists
        try:
            result = db_service.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='user_progress'")
            if result:
                repair_info['operations'].append({
                    'step': 'check_table_exists',
                    'success': True,
                    'message': 'user_progress table exists'
                })
            else:
                repair_info['operations'].append({
                    'step': 'check_table_exists', 
                    'success': False,
                    'message': 'user_progress table does not exist'
                })
        except Exception as e:
            repair_info['operations'].append({
                'step': 'check_table_exists',
                'success': False,
                'error': str(e)
            })
        
        # Step 2: Drop and recreate user_progress table
        try:
            db_service.execute_update("DROP TABLE IF EXISTS user_progress")
            repair_info['operations'].append({
                'step': 'drop_table',
                'success': True,
                'message': 'Dropped user_progress table'
            })
        except Exception as e:
            repair_info['operations'].append({
                'step': 'drop_table',
                'success': False,
                'error': str(e)
            })
        
        # Step 3: Recreate table with clean structure
        try:
            create_query = '''
            CREATE TABLE user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                experience_points INTEGER DEFAULT 0,
                total_experience INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            '''
            db_service.execute_update(create_query)
            repair_info['operations'].append({
                'step': 'create_table',
                'success': True,
                'message': 'Created clean user_progress table'
            })
        except Exception as e:
            repair_info['operations'].append({
                'step': 'create_table',
                'success': False,
                'error': str(e)
            })
        
        # Step 4: Test the repaired table
        try:
            result = db_service.execute_query("SELECT COUNT(*) as count FROM user_progress")
            repair_info['operations'].append({
                'step': 'test_table',
                'success': True,
                'message': f'Table test successful, count: {result[0]["count"] if result else 0}'
            })
        except Exception as e:
            repair_info['operations'].append({
                'step': 'test_table',
                'success': False,
                'error': str(e)
            })
        
        # Step 5: Test insert
        try:
            test_user_id = 'test_user_repair'
            db_service.execute_update(
                "INSERT OR REPLACE INTO user_progress (user_id, level, experience_points, total_experience, created_at) VALUES (?, ?, 0, 0, ?)",
                (test_user_id, 1, datetime.now().isoformat())
            )
            repair_info['operations'].append({
                'step': 'test_insert',
                'success': True,
                'message': 'Test insert successful'
            })
            
            # Clean up test data
            db_service.execute_update("DELETE FROM user_progress WHERE user_id = ?", (test_user_id,))
            
        except Exception as e:
            repair_info['operations'].append({
                'step': 'test_insert',
                'success': False,
                'error': str(e)
            })
        
        repair_info['overall_success'] = all(op.get('success', False) for op in repair_info['operations'])
        
    except Exception as e:
        repair_info['overall_error'] = str(e)
        repair_info['overall_success'] = False
    
    return jsonify(repair_info)

# Debug endpoint for database repair
@app.route('/api/debug/chrome')
def debug_chrome():
    """Debug endpoint to check Chrome installation status"""
    import subprocess
    import shutil
    
    debug_info = {
        'timestamp': datetime.now().isoformat(),
        'chrome_tests': []
    }
    
    # Test 1: Check for Chrome binaries
    chrome_paths = [
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/local/bin/google-chrome',
        '/usr/local/bin/chrome',
        '/usr/local/bin/chromium'
    ]
    
    for path in chrome_paths:
        try:
            if os.path.exists(path):
                debug_info['chrome_tests'].append({
                    'path': path,
                    'exists': True,
                    'executable': os.access(path, os.X_OK)
                })
            else:
                debug_info['chrome_tests'].append({
                    'path': path,
                    'exists': False,
                    'executable': False
                })
        except Exception as e:
            debug_info['chrome_tests'].append({
                'path': path,
                'error': str(e)
            })
    
    # Test 2: Check command availability
    commands = ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']
    for cmd in commands:
        try:
            path = shutil.which(cmd)
            debug_info['chrome_tests'].append({
                'command': cmd,
                'which_path': path,
                'available': path is not None
            })
        except Exception as e:
            debug_info['chrome_tests'].append({
                'command': cmd,
                'error': str(e)
            })
    
    # Test 3: Try to get Chrome version
    for cmd in ['google-chrome-stable', 'google-chrome', 'chromium-browser', 'chromium']:
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            debug_info['chrome_tests'].append({
                'version_test': cmd,
                'success': result.returncode == 0,
                'output': result.stdout.strip(),
                'error': result.stderr.strip()
            })
            if result.returncode == 0:
                break  # Found working Chrome
        except Exception as e:
            debug_info['chrome_tests'].append({
                'version_test': cmd,
                'error': str(e)
            })
    
    # Test 4: Environment variables
    debug_info['environment'] = {
        'GOOGLE_CHROME_BIN': os.environ.get('GOOGLE_CHROME_BIN'),
        'CHROMEDRIVER_PATH': os.environ.get('CHROMEDRIVER_PATH'),
        'PATH': os.environ.get('PATH'),
        'RENDER': os.environ.get('RENDER'),
        'SELENIUM_HEADLESS': os.environ.get('SELENIUM_HEADLESS')
    }
    
    return jsonify(debug_info)

# Debug endpoint for testing database queries
@app.route('/api/debug/db')
def debug_database():
    """Debug endpoint to test database queries and see result structure"""
    debug_info = {
        'timestamp': datetime.now().isoformat(),
        'database_type': 'Turso' if db_service.is_turso else 'SQLite',
        'tests': []
    }
    
    # Test simple query
    try:
        logger.info("🔍 DEBUG: Testing simple COUNT query...")
        result = db_service.execute_query("SELECT COUNT(*) as user_count FROM users")
        logger.info(f"🔍 DEBUG: Query result: {result}")
        debug_info['tests'].append({
            'query': 'SELECT COUNT(*) as user_count FROM users',
            'success': True,
            'result': result,
            'result_type': str(type(result))
        })
    except Exception as e:
        logger.error(f"❌ DEBUG: Query failed: {e}")
        debug_info['tests'].append({
            'query': 'SELECT COUNT(*) as user_count FROM users',
            'success': False,
            'error': str(e),
            'error_type': str(type(e))
        })
    
    # Test table existence
    try:
        logger.info("🔍 DEBUG: Testing table existence query...")
        result = db_service.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        logger.info(f"🔍 DEBUG: Tables result: {result}")
        debug_info['tests'].append({
            'query': 'SELECT name FROM sqlite_master WHERE type=\'table\'',
            'success': True,
            'result': result,
            'result_type': str(type(result))
        })
    except Exception as e:
        logger.error(f"❌ DEBUG: Table query failed: {e}")
        debug_info['tests'].append({
            'query': 'SELECT name FROM sqlite_master WHERE type=\'table\'',
            'success': False,
            'error': str(e),
            'error_type': str(type(e))
        })
    
    return jsonify(debug_info)

# API health check
@app.route('/api/health')
def api_health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': db_service.health_check()
    })

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
