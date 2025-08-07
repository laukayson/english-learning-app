# Add this to the top of your app_pythonanywhere.py imports
from render_selenium_client import init_selenium_client, get_selenium_client

# Add this after your other service initializations
# Initialize Render Selenium client
RENDER_SELENIUM_URL = "https://your-app-name.onrender.com"  # Replace with your Render URL
init_selenium_client(RENDER_SELENIUM_URL)

# Update your existing chat endpoint
@app.route('/api/chat', methods=['POST'])
@rate_limit_decorator
def chat():
    """Handle chat messages using Render Selenium service"""
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
        selenium_client = get_selenium_client()
        if selenium_client and selenium_client.health_check():
            # Map numeric level to string
            level_map = {1: 'absolute_beginner', 2: 'beginner', 3: 'intermediate', 4: 'advanced'}
            user_level = level_map.get(level, 'beginner')
            
            response = selenium_client.send_chatbot_message(
                message=user_message,
                topic=topic,
                level=level,
                user_level=user_level
            )
        else:
            # Fallback response if Selenium service is unavailable
            logger.warning("Selenium service unavailable, using fallback")
            response = f"I understand you're saying: '{user_message}'. This is a fallback response as the AI service is currently unavailable. Please try again later."
        
        # Save conversation to database (existing code)
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

# Update your topic initialization endpoint  
@app.route('/api/chat/init-topic', methods=['POST'])
@rate_limit_decorator
def init_topic():
    """Initialize a conversation topic using Render Selenium service"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        topic_id = data.get('topic')
        user_id = data.get('user_id')
        level = data.get('level', 1)
        
        if not all([topic_id, user_id]):
            return jsonify({'error': 'Topic and user_id are required'}), 400
        
        logger.info(f"Initializing topic {topic_id} for user {user_id}")
        
        # Initialize context using Render Selenium service
        selenium_client = get_selenium_client()
        if selenium_client and selenium_client.health_check():
            level_map = {1: 'absolute_beginner', 2: 'beginner', 3: 'intermediate', 4: 'advanced'}
            user_level = level_map.get(level, 'beginner')
            
            success = selenium_client.init_chatbot_context(
                topic=topic_id,
                level=level,
                user_level=user_level
            )
            
            return jsonify({
                'status': 'success' if success else 'warning',
                'topic': topic_id,
                'message': 'Topic initialized successfully' if success else 'Topic initialization had issues but continuing'
            })
        else:
            # Continue without initialization if service unavailable
            return jsonify({
                'status': 'warning',
                'topic': topic_id,
                'message': 'Topic context could not be initialized, but conversation can continue'
            })
        
    except Exception as e:
        logger.error(f"Topic initialization error: {str(e)}")
        return jsonify({'error': 'Failed to initialize topic'}), 500
