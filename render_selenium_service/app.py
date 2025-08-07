"""
Render Selenium Service API
Consolidates all Selenium operations for the English Learning App
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
import time
import json
from concurrent.futures import ThreadPoolExecutor
import threading

# Import our Selenium services
from services.chatbot_service import ChatbotService
from services.stt_service import STTService
from services.browser_manager import BrowserManager

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log successful service imports
logger.info("Successfully imported all services")

# Initialize start time for uptime tracking
start_time = time.time()

# Thread pool for concurrent requests
executor = ThreadPoolExecutor(max_workers=3)  # Limit concurrent browsers
browser_manager = BrowserManager()

# Root endpoint for debugging
@app.route('/', methods=['GET'])
def root():
    """Root endpoint to verify service is running"""
    return jsonify({
        'message': 'Selenium Service API is running',
        'status': 'healthy',
        'endpoints': ['/health', '/api/health', '/api/chatbot/send-message', '/api/stt/start-recording'],
        'timestamp': time.time()
    })

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check for Render"""
    return jsonify({
        'status': 'healthy',
        'service': 'selenium-api',
        'timestamp': time.time()
    })

@app.route('/api/health', methods=['GET'])
def api_health_check():
    """Health check for Render (alternative path)"""
    logger.info("Health check endpoint accessed")
    return jsonify({
        'status': 'healthy',
        'service': 'selenium-api',
        'timestamp': time.time()
    })

# Chatbot API endpoints
@app.route('/api/chatbot/send-message', methods=['POST'])
def chatbot_send_message():
    """Send message to AI chatbot via Selenium"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message']
        topic = data.get('topic', 'general')
        level = data.get('level', 1)
        user_level = data.get('user_level', 'beginner')
        
        logger.info(f"Processing chatbot message: {message[:50]}...")
        
        # Create chatbot service instance
        chatbot = ChatbotService(browser_manager)
        
        # Get response from AI (persist session by default for conversation continuity)
        persist = data.get('persist_session', True)
        response = chatbot.get_ai_response(message, topic, level, user_level, persist_session=persist)
        
        return jsonify({
            'response': response,
            'status': 'success',
            'service': 'chatbot'
        })
        
    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'service': 'chatbot'
        }), 500

@app.route('/api/chatbot/end-conversation', methods=['POST'])
def chatbot_end_conversation():
    """End the current conversation and release resources"""
    try:
        logger.info("Ending chatbot conversation")
        
        chatbot = ChatbotService(browser_manager)
        success = chatbot.end_conversation()
        
        return jsonify({
            'success': success,
            'status': 'success',
            'message': 'Conversation ended'
        })
        
    except Exception as e:
        logger.error(f"Error ending conversation: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/chatbot/init-context', methods=['POST'])
def chatbot_init_context():
    """Initialize chatbot context for a topic"""
    try:
        data = request.get_json()
        
        if not data or 'topic' not in data:
            return jsonify({'error': 'Topic is required'}), 400
        
        topic = data['topic']
        level = data.get('level', 1)
        user_level = data.get('user_level', 'beginner')
        
        logger.info(f"Initializing chatbot context for topic: {topic}")
        
        chatbot = ChatbotService(browser_manager)
        success = chatbot.initialize_context(topic, level, user_level)
        
        return jsonify({
            'success': success,
            'topic': topic,
            'status': 'success',
            'service': 'chatbot'
        })
        
    except Exception as e:
        logger.error(f"Context initialization error: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'service': 'chatbot'
        }), 500

# Speech-to-Text API endpoints
@app.route('/api/stt/start-recording', methods=['POST'])
def stt_start_recording():
    """Start speech recognition session"""
    try:
        data = request.get_json()
        language = data.get('language', 'en') if data else 'en'
        
        logger.info("Starting STT recording session")
        
        stt = STTService(browser_manager)
        session_id = stt.start_session(language)
        
        return jsonify({
            'session_id': session_id,
            'status': 'recording_started',
            'service': 'stt'
        })
        
    except Exception as e:
        logger.error(f"STT start error: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'service': 'stt'
        }), 500

@app.route('/api/stt/get-result/<session_id>', methods=['GET'])
def stt_get_result(session_id):
    """Get speech recognition result"""
    try:
        logger.info(f"Getting STT result for session: {session_id}")
        
        stt = STTService(browser_manager)
        result = stt.get_result(session_id)
        
        return jsonify({
            'text': result,
            'session_id': session_id,
            'status': 'success',
            'service': 'stt'
        })
        
    except Exception as e:
        logger.error(f"STT result error: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'service': 'stt'
        }), 500

@app.route('/api/stt/stop-recording/<session_id>', methods=['POST'])
def stt_stop_recording(session_id):
    """Stop speech recognition session"""
    try:
        logger.info(f"Stopping STT session: {session_id}")
        
        stt = STTService(browser_manager)
        result = stt.stop_session(session_id)
        
        return jsonify({
            'text': result,
            'session_id': session_id,
            'status': 'stopped',
            'service': 'stt'
        })
        
    except Exception as e:
        logger.error(f"STT stop error: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'service': 'stt'
        }), 500

# Service management endpoints
@app.route('/api/service/status', methods=['GET'])
def service_status():
    """Get status of all services"""
    try:
        status = {
            'browser_manager': browser_manager.get_status(),
            'active_sessions': browser_manager.get_active_sessions(),
            'memory_usage': browser_manager.get_memory_usage(),
            'uptime': time.time() - start_time
        }
        
        return jsonify({
            'status': status,
            'service': 'management'
        })
        
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'service': 'management'
        }), 500

@app.route('/api/service/cleanup', methods=['POST'])
def service_cleanup():
    """Cleanup inactive sessions and browsers"""
    try:
        logger.info("Running service cleanup")
        
        cleaned = browser_manager.cleanup_inactive_sessions()
        
        return jsonify({
            'cleaned_sessions': cleaned,
            'status': 'success',
            'service': 'management'
        })
        
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'service': 'management'
        }), 500

# Global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}")
    return jsonify({
        'error': 'Internal server error',
        'status': 'error'
    }), 500

if __name__ == '__main__':
    start_time = time.time()
    
    # Get port from environment (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting Selenium Service on port {port}")
    logger.info("Services available: Chatbot, STT, Browser Management")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
else:
    # For Gunicorn deployment
    logger.info("Starting Selenium Service via Gunicorn")
    logger.info("Services available: Chatbot, STT, Browser Management")
    logger.info(f"Available routes: {[rule.rule for rule in app.url_map.iter_rules()]}")
