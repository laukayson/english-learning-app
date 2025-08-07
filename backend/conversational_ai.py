"""
Advanced Conversational AI for Language Learning
Pure Selenium-based implementation - no fallbacks
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ConversationalAI:
    def __init__(self):
        self.conversation_history = []
        self.user_context = {
            'name': None,
            'interests': [],
            'current_topic': 'general',
            'language_level': 'beginner',
            'session_start': datetime.now(),
            'session_id': None
        }
        
        # Initialize Render Selenium client
        self.selenium_client = None
        self.use_selenium = True  # Flag to enable/disable Selenium chatbot
        self.session_active = False  # Track if session is active
        self._initialize_selenium_chatbot()
    
    def _initialize_selenium_chatbot(self):
        """Initialize the original Selenium-based chatbot service"""
        try:
            # Import and initialize your original selenium chatbot
            from selenium_chatbot import SeleniumChatbot
            import uuid
            
            # Generate unique session ID
            self.user_context['session_id'] = str(uuid.uuid4())
            
            # Create the selenium chatbot instance but don't initialize yet
            self.selenium_client = SeleniumChatbot(
                headless=True,  # Run headless on Render
                timeout=30
            )
            
            # Don't initialize during startup - do it lazily when first needed
            self.session_active = False
            logger.info(f"🤖 Selenium chatbot created (session: {self.user_context['session_id']}) - will initialize on first use")
                
        except Exception as e:
            logger.error(f"Failed to create Selenium chatbot service: {str(e)}")
            self.selenium_client = None
            self.session_active = False
    
    def _create_educational_response(self, message: str, topic: str, user_level: str) -> str:
        """Create an educational response when selenium fails"""
        # This is a backup method that creates contextually appropriate responses
        response_templates = {
            'beginner': [
                f"That's interesting! When talking about {topic}, I would say: ",
                f"Good question about {topic}! Let me help you practice: ",
                f"Nice! For {topic} conversations, try saying: "
            ],
            'intermediate': [
                f"Great point about {topic}! You could also express that as: ",
                f"I understand your question about {topic}. Consider this perspective: ",
                f"That's a thoughtful observation about {topic}. Another way to think about it: "
            ],
            'advanced': [
                f"Excellent insight regarding {topic}! This reminds me of: ",
                f"Your question about {topic} touches on an important aspect. Consider: ",
                f"That's a sophisticated point about {topic}. You might also explore: "
            ]
        }
        
        templates = response_templates.get(user_level, response_templates['beginner'])
        import random
        template = random.choice(templates)
        
        # Generate contextual response based on topic
        topic_responses = {
            'family': "spending quality time with family members and sharing stories about our daily lives.",
            'work': "balancing professional responsibilities while pursuing personal growth and learning opportunities.",
            'hobbies': "discovering new activities that bring joy and help us connect with like-minded people.",
            'food': "exploring different cuisines and the cultural stories behind traditional dishes.",
            'travel': "experiencing new places and learning about different cultures and ways of life."
        }
        
        topic_content = topic_responses.get(topic, f"exploring different aspects of {topic} and sharing personal experiences.")
        
        return f"{template}{topic_content} What are your thoughts on this?"
    
    def get_response(self, message: str, topic: str = 'general', history: List = None, user_level: str = 'beginner') -> str:
        """
        Main method to get AI response - PURE SELENIUM ONLY
        """
        # Set current topic context
        self.user_context['current_topic'] = topic
        self.user_context['language_level'] = user_level
        
        # Use conversation history if provided
        if history:
            self.conversation_history = history
        
        # SELENIUM ONLY - no fallbacks
        if not self.selenium_client:
            logger.error("❌ Selenium client not created")
            return f"ERROR: Selenium client not created. Check selenium_chatbot import."
        
        if not self.use_selenium:
            logger.error("❌ Selenium disabled")
            return f"ERROR: Selenium chatbot is disabled"
        
        try:
            # Initialize selenium chatbot lazily on first use
            if not self.session_active:
                logger.info("🔄 Initializing selenium chatbot on first use...")
                if self.selenium_client.initialize():
                    self.session_active = True
                    logger.info("✅ Selenium chatbot initialized successfully")
                else:
                    error_msg = "❌ Selenium chatbot initialization failed"
                    logger.error(error_msg)
                    return f"ERROR: {error_msg}. Check Chrome installation and permissions."
            
            # Use the selenium chatbot implementation
            logger.info(f"🤖 Calling selenium_client.get_response() with message: '{message[:50]}...'")
            response = self.selenium_client.get_response(
                message=message,
                topic=topic,
                history=history,
                user_level=user_level
            )
            
            if response and response.strip():
                logger.info(f"✅ Selenium response received: '{response[:100]}...'")
                # Add this interaction to our conversation history
                self._update_conversation_history(message, response)
                return response
            else:
                error_msg = "❌ Selenium chatbot returned empty/invalid response"
                logger.error(error_msg)
                return f"ERROR: {error_msg}. Response was: '{response}'"
                
        except Exception as e:
            error_msg = f"❌ Selenium chatbot service failed: {str(e)}"
            logger.error(error_msg)
            self.session_active = False
            return f"ERROR: {error_msg}"
    
    def _update_conversation_history(self, user_message: str, ai_response: str):
        """Update conversation history with the latest exchange"""
        self.conversation_history.append({
            'user_message': user_message,
            'ai_response': ai_response,
            'timestamp': datetime.now(),
            'source': 'render_chatbot'
        })

    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get statistics about the current conversation"""
        stats = {
            'messages_exchanged': len(self.conversation_history),
            'session_duration': str(datetime.now() - self.user_context['session_start']),
            'primary_intents': [msg.get('context', {}).get('intent', 'unknown') for msg in self.conversation_history[-5:] if isinstance(msg, dict)],
            'engagement_level': 'high' if len(self.conversation_history) > 10 else 'moderate',
            'render_chatbot_active': self.selenium_client is not None and self.use_selenium
        }
        
        # Add Render service status if available
        if self.selenium_client:
            try:
                stats['render_service_ready'] = self.selenium_client.health_check()
            except:
                stats['render_service_ready'] = False
        
        return stats
    
    def toggle_selenium_chatbot(self, enabled: bool):
        """Enable or disable the Render chatbot service"""
        self.use_selenium = enabled
        if enabled and not self.selenium_client:
            self._initialize_selenium_chatbot()
        logger.info(f"Selenium chatbot {'enabled' if enabled else 'disabled'}")
    
    def cleanup(self):
        """Clean up resources, especially the Render chatbot service"""
        if self.selenium_client:
            try:
                # Render service cleanup is handled by the service itself
                self.selenium_client = None
                self.session_active = False
                logger.info(f"Conversational AI session {self.user_context.get('session_id', 'unknown')} cleaned up successfully")
            except Exception as e:
                logger.error(f"Error during ConversationalAI cleanup: {e}")
                
    def end_session(self):
        """End the current session and cleanup resources"""
        session_id = self.user_context.get('session_id', 'unknown')
        logger.info(f"Ending session: {session_id}")
        self.cleanup()
        
    def clear_conversation_history(self):
        """Clear conversation history while maintaining session"""
        self.conversation_history = []
        logger.info(f"Conversation history cleared for session: {self.user_context.get('session_id', 'unknown')}")
        
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        return {
            'session_id': self.user_context.get('session_id'),
            'session_active': self.session_active,
            'selenium_available': self.selenium_chatbot is not None,
            'session_start': self.user_context['session_start'].isoformat(),
            'current_topic': self.user_context['current_topic']
        }
    
    def get_topic_starter(self, topic: str, user_level: str = 'beginner') -> str:
        """Get a conversation starter for a specific topic"""
        topic_starters = {
            'family': [
                "Hello! Let's talk about family today. Tell me about your family members!",
                "Family is so important! How many people are in your family?",
                "I'd love to hear about your family. Who do you live with?"
            ],
            'work': [
                "Let's discuss work and careers! What kind of work do you do?",
                "Work is a big part of life. Tell me about your job or studies!",
                "I'm curious about your work. What does a typical day look like for you?"
            ],
            'hobbies': [
                "Time to talk about hobbies! What do you like to do in your free time?",
                "Hobbies make life interesting! What activities do you enjoy?",
                "Let's chat about what you love doing. What are your favorite hobbies?"
            ],
            'food': [
                "Food brings people together! What's your favorite dish?",
                "Let's talk about food. What do you like to eat?",
                "I love discussing food! Tell me about your favorite cuisine."
            ],
            'travel': [
                "Travel opens our minds! Have you visited any interesting places?",
                "Let's explore the world through conversation! Where would you like to travel?",
                "Travel stories are the best! Tell me about a place you'd love to visit."
            ],
            'general': [
                "Hello! I'm excited to practice English with you today. How are you feeling?",
                "Welcome! Let's have a great conversation. What would you like to talk about?",
                "Hi there! Ready to practice English? Tell me how your day is going!"
            ]
        }
        
        starters = topic_starters.get(topic, topic_starters['general'])
        import random
        starter = random.choice(starters)
        
        # Adjust for user level
        if user_level == 'absolute_beginner':
            starter = "Hello! " + starter.split('!', 1)[-1] if '!' in starter else starter
        
        return starter
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# For testing
if __name__ == "__main__":
    ai = ConversationalAI()
    
    test_messages = [
        "Hello there!",
        "How are you doing today?",
        "I'm learning English and it's quite difficult",
        "My family is from Afghanistan and we moved here recently",
        "What should I do to improve my speaking?",
        "I love reading books in English"
    ]
    
    print("Conversational AI Test:")
    print("=" * 50)
    
    for msg in test_messages:
        response = ai.generate_contextual_response(msg)
        print(f"User: {msg}")
        print(f"AI: {response}")
        print("-" * 30)
    
    print("\nConversation Statistics:")
    stats = ai.get_conversation_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
