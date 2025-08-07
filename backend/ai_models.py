"""
Lightweight AI Models Service for Language Learning App
Uses advanced conversational AI for natural dialogue
"""

import logging
from typing import List, Dict, Any, Optional
import json
import random
import re

logger = logging.getLogger(__name__)

class AIModels:
    def __init__(self):
        self.ready = False
        self.conversational_ai = None
        self.initialize_lightweight()
    
    def initialize_lightweight(self):
        """Initialize lightweight AI service"""
        try:
            logger.info("Initializing lightweight AI models service...")
            
            # Try to import conversational AI (fallback if not available)
            try:
                from conversational_ai import ConversationalAI
                self.conversational_ai = ConversationalAI()
                logger.info("Advanced conversational AI loaded")
            except ImportError:
                logger.warning("Advanced conversational AI not available, using basic responses")
                self.conversational_ai = None
            
            self.ready = True
            logger.info("Lightweight AI models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing lightweight AI: {e}")
            self.ready = True  # Still ready with basic functionality
    
    def is_ready(self) -> bool:
        """Check if AI models are ready"""
        return self.ready

    def generate_response(self, user_message: str, level: int, topic: str, context: Dict[str, Any] = None) -> str:
        """Generate AI response to user message"""
        try:
            # TEMPORARILY DISABLE ADVANCED AI TO USE TEST PHRASES
            # Use advanced conversational AI if available
            # if self.conversational_ai:
            #     conversation_history = context.get('history', []) if context else []
            #     return self.conversational_ai.generate_contextual_response(
            #         user_message, conversation_history
            #     )
            
            # Force basic contextual responses with test phrases
            return self._generate_basic_response(user_message, level, topic)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Thank you for sharing! I'm here to help you practice English. What would you like to talk about?"
    
    def _generate_basic_response(self, user_message: str, level: int, topic: str) -> str:
        """Generate basic contextual response when advanced AI is not available"""
        message_lower = user_message.lower().strip()
        
        # Contextual responses based on content
        if any(word in message_lower for word in ['hello', 'hi', 'good morning', 'good evening']):
            greetings = [
                "Hello! It's great to meet you. What would you like to practice today?",
                "Hi there! I'm excited to help you with your English learning journey.",
                "Good to see you! Let's start with some conversation practice.",
                "Welcome! What topic interests you most for today's lesson?",
                "How was your day?",
                "What time is it where you are right now?",
                "The weather is beautiful today, isn't it?",
                "Where is the nearest restaurant you would recommend?",
                "Can you help me understand your learning goals please?"
            ]
            return random.choice(greetings)
        
        elif any(word in message_lower for word in ['fine', 'good', 'well', 'okay', 'great']):
            positive_responses = [
                "That's wonderful to hear! What would you like to talk about?",
                "I'm glad you're doing well! Shall we practice some English conversation?",
                "Excellent! Let's work on improving your English skills together.",
                "Great! What aspect of English would you like to focus on today?",
                "I am learning Persian language and finding it fascinating.",
                "I don't understand everything yet, but I'm making progress.",
                "How much does this language learning program cost?",
                "What is your favorite color when it comes to learning materials?"
            ]
            return random.choice(positive_responses)
        
        elif any(word in message_lower for word in ['learn', 'study', 'practice', 'help']):
            learning_responses = [
                "I'm here to help you learn! What specific area would you like to work on?",
                "Learning English is a great goal! Let's start with conversation practice.",
                "I'd love to help you practice! What would you like to improve - speaking, vocabulary, or grammar?",
                "That's the right attitude! Let's begin with some practical English exercises.",
                "I would like to order some traditional Persian food for dinner tonight.",
                "Could you please recommend a good book about Iranian culture and history?",
                "My grandmother used to tell me stories about her childhood in Tehran.",
                "I am planning to visit Iran next summer to learn more about the language.",
                "The Persian carpet in our living room was handmade by skilled artisans.",
                "I enjoy listening to Persian poetry, especially the works of Hafez and Rumi."
            ]
            return random.choice(learning_responses)
        
        elif any(word in message_lower for word in ['difficult', 'hard', 'challenging', 'struggle']):
            supportive_responses = [
                "I understand that English can be challenging sometimes. Don't worry - making mistakes is part of learning! What specifically is giving you trouble?",
                "It's completely normal to find English difficult. You're doing great by practicing! Can you tell me what part is most confusing?",
                "Many English learners feel this way - you're not alone! The important thing is that you're trying. What would help you feel more confident?",
                "Although I have been studying Persian for six months, I still find the writing system challenging.",
                "If I could travel anywhere in the world, I would choose to visit the ancient city of Isfahan.",
                "The professor explained that Persian literature has influenced many other cultures throughout history.",
                "While walking through the bazaar, she discovered beautiful handcrafted jewelry and spices.",
                "Because the Persian language is so rich and expressive, many poets have used it to create masterpieces."
            ]
            return random.choice(supportive_responses)
        
        elif any(word in message_lower for word in ['thank', 'thanks']):
            gratitude_responses = [
                "You're very welcome! I'm here to support your learning journey.",
                "My pleasure! Keep up the excellent work with your English practice.",
                "Happy to help! What else would you like to learn today?",
                "You're welcome! Your dedication to learning is inspiring.",
                "Artificial intelligence is transforming how we learn languages.",
                "The periodic table contains 118 chemical elements.",
                "Photosynthesis is the process by which plants convert sunlight into energy.",
                "The theory of relativity was developed by Albert Einstein in the early 20th century.",
                "Computer programming requires logical thinking and problem-solving skills."
            ]
            return random.choice(gratitude_responses)
        
        elif len(message_lower) > 20:  # Longer messages get more detailed responses
            detailed_responses = [
                "Thank you for sharing that with me! Your English expression is improving. Can you tell me more about your experience?",
                "I appreciate you explaining that. Your vocabulary use is good! What are your thoughts on this topic?",
                "That's very interesting! You're communicating well in English. How do you feel about this subject?",
                "You've expressed that clearly! I can see your English skills developing. What else would you like to discuss?",
                "Family traditions are very important in Persian culture.",
                "The New Year celebration called Nowruz marks the beginning of spring.",
                "Persian music often features traditional instruments like the tar and setar.",
                "Hospitality is considered one of the most important values in Iranian society.",
                "The art of Persian calligraphy has been practiced for over a thousand years."
            ]
            return random.choice(detailed_responses)
        
        else:
            # Default encouraging responses for short messages
            encouraging_responses = [
                "I understand! Can you tell me more about that?",
                "That's a good start! Please share more details.",
                "I see! Could you explain that a bit more?",
                "Interesting! What else can you tell me about this?",
                "Excuse me, where is the bathroom?",
                "What is your favorite subject in school?",
                "How do you spend your weekends?",
                "What kind of music do you enjoy listening to?"
            ]
            return random.choice(encouraging_responses)
    
    def generate_conversation_prompt(self, level: int, topic: str, context: Dict[str, Any] = None) -> str:
        """Generate a conversation prompt based on level and topic"""
        try:
            if self.conversational_ai:
                return self.conversational_ai.suggest_conversation_topic()
            
            # Fallback conversation starters
            topic_starters = {
                'family': [
                    "Tell me about your family. Who are the most important people in your life?",
                    "What traditions does your family have that are special to you?",
                    "How would you describe your family to someone new?"
                ],
                'work': [
                    "What kind of work do you do, or what would you like to do?",
                    "What's the most interesting part of your job or studies?",
                    "What are your hopes for your professional future?"
                ],
                'hobbies': [
                    "What do you like to do in your free time?",
                    "What activities bring you the most joy?",
                    "What are you passionate about?"
                ],
                'general': [
                    "What would you like to talk about today?",
                    "Tell me something interesting about yourself!",
                    "What's been on your mind lately?"
                ]
            }
            
            starters = topic_starters.get(topic, topic_starters['general'])
            return random.choice(starters)
            
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            return "Let's have a conversation! What would you like to talk about?"
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        try:
            if self.conversational_ai:
                return self.conversational_ai.get_conversation_stats()
            else:
                return {'basic_mode': True, 'advanced_ai': False}
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'error': 'Stats unavailable'}

# For testing
if __name__ == "__main__":
    ai = AIModels()
    
    test_messages = [
        "Hello there!",
        "How are you doing today?", 
        "I'm learning English and it's quite difficult",
        "My family is from Afghanistan and we moved here recently",
        "What should I do to improve my speaking?",
        "I love reading books in English"
    ]
    
    print("AI Models Test:")
    print("=" * 50)
    
    for msg in test_messages:
        response = ai.generate_response(msg, 2, 'general')
        print(f"User: {msg}")
        print(f"AI: {response}")
        print("-" * 30)
