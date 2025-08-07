"""
Advanced Conversational AI for Language Learning
Provides natural conversation flow with context awareness
Now integrates with Selenium-based chatbot for enhanced responses
"""

import random
import re
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
        
        # Conversation templates organized by context (fallback when Selenium is unavailable)
        self.conversation_patterns = {
            'greeting': {
                'patterns': [r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b'],
                'responses': [
                    "Hello! I'm so glad you're here to practice English with me. What would you like to talk about today?",
                    "Hi there! Welcome to our English conversation session. How are you feeling about practicing today?",
                    "Good to see you! I'm excited to help you improve your English. What's on your mind?",
                    "Hello! It's wonderful that you're taking time to practice English. What topic interests you most?"
                ]
            },
            'how_are_you': {
                'patterns': [r'\b(how are you|how do you do|how have you been)\b'],
                'responses': [
                    "I'm doing great, thank you for asking! I'm here and ready to help you practice English. How are you doing today?",
                    "I'm wonderful! I love helping people learn English. How are you feeling about your English learning journey?",
                    "I'm doing well, thanks! I'm always excited when someone wants to practice conversation. How has your day been?",
                    "I'm fantastic! Every conversation helps me understand how to better help learners like you. How are you today?"
                ]
            },
            'name_asking': {
                'patterns': [r'\b(what.*your name|who are you|what should I call you)\b'],
                'responses': [
                    # "I'm your AI English tutor! You can call me Teacher or just AI. I'm here to help you practice conversation in English. What's your name?",
                    # "I'm an AI language teacher designed to help you practice English conversation. You can call me whatever feels comfortable! What should I call you?",
                    # "I'm your conversational English practice partner! I don't have a specific name, but I'm here to help you learn. What would you like me to call you?"
                    "I'd love to get to know you better! What name would you like me to call you during our English practice sessions?"
                ]
            },
            'learning_intent': {
                'patterns': [r'\b(learn|study|practice|improve|help.*english|want.*better)\b'],
                'responses': [
                    # "That's fantastic! Learning English opens so many doors. What specific area would you like to focus on - conversation, vocabulary, or grammar?",
                    # "I love your motivation to learn! English can be challenging but very rewarding. What's your biggest goal with English right now?",
                    # "Excellent attitude! Practice is the key to improving English. What situations do you most want to use English in?",
                    # "That's wonderful to hear! Everyone learns differently. What kind of English practice do you find most helpful?"
                    "That's wonderful that you're interested in learning! What aspect of English would you like to focus on today - speaking, vocabulary, or conversation skills?"
                ]
            },
            'difficulty_expressing': {
                'patterns': [r'\b(difficult|hard|confused|don\'t understand|struggle)\b'],
                'responses': [
                    # "I understand that English can be challenging sometimes. Don't worry - making mistakes is part of learning! What specifically is giving you trouble?",
                    # "It's completely normal to find English difficult. You're doing great by practicing! Can you tell me what part is most confusing?",
                    # "Many English learners feel this way - you're not alone! The important thing is that you're trying. What would help you feel more confident?",
                    # "I appreciate you sharing that with me. English has many tricky parts, but with practice it gets easier. What would you like to work on together?"
                    "Don't worry about difficulty - everyone learns at their own pace! Let's start with something comfortable. What topics do you enjoy talking about in your daily life?"
                ]
            },
            'positive_response': {
                'patterns': [r'\b(good|great|excellent|wonderful|amazing|perfect|love|like)\b'],
                'responses': [
                    # "I'm so happy to hear that! Your positive attitude will really help your English learning. Can you tell me more about what you enjoyed?",
                    # "That's wonderful! When we enjoy something, we learn it much faster. What made this experience positive for you?",
                    # "Excellent! I can hear the enthusiasm in your words. What other topics or activities interest you in English?",
                    # "That's fantastic to hear! Your excitement about learning English is inspiring. What would you like to explore next?"
                    "I'm so glad to hear that! Your positive attitude will really help your English learning. What would you like to talk about today?"
                ]
            },
            'asking_questions': {
                'patterns': [r'\b(what|where|when|who|why|how|can you|could you|would you)\b'],
                'responses': [
                    # "Great question! I love when students are curious. Let me think about the best way to explain this to you.",
                    # "That's an excellent thing to ask about! Questions show you're really thinking about English.",
                    # "I'm glad you asked! That's exactly the kind of thinking that will help you improve your English.",
                    # "What a thoughtful question! This is how we learn - by being curious and asking for clarification."
                    "Great question! I'm here to help you practice English conversation. What topics or situations would you like to practice talking about?"
                ]
            },
            'sharing_personal': {
                'patterns': [r'\b(I|my|me|myself|my family|my work|my school|my country)\b'],
                'responses': [
                    # "Thank you for sharing that with me! It's so interesting to learn about your life. Your personal experiences make great conversation practice.",
                    # "I really appreciate you telling me about yourself! Sharing personal stories is one of the best ways to practice natural English conversation.",
                    # "That's fascinating! When we talk about things that matter to us, it helps us practice English in a meaningful way.",
                    # "I love hearing about your experiences! This kind of personal sharing really helps develop conversational English skills."
                    "Thank you for sharing that with me! I'd love to hear more. Can you tell me a bit more about your interests or experiences?"
                ]
            },
            'fallback': {
                'patterns': [],
                'responses': [
                    # "That's really interesting! I'd love to hear more about your thoughts on this topic.",
                    # "Thank you for sharing that! Your English expression is getting better with each sentence you speak.",
                    # "I can see you're thinking carefully about how to express yourself in English. That's exactly what good learners do!",
                    # "You're doing a great job communicating in English! Can you elaborate on that idea a bit more?",
                    # "I appreciate you taking the time to explain that. What else would you like to discuss about this topic?",
                    # "Your English communication is really developing well! What are your thoughts on this subject?",
                    # "That's a thoughtful way to put it! I'm curious to know what you think about this from your perspective.",
                    # "You're expressing yourself clearly in English! How do you feel about discussing topics like this?"
                    "That's interesting! I'd love to help you practice talking about that. Can you tell me more about your thoughts on this topic?"
                ]
            }
        }
        
        # Topic-specific conversation starters
        self.topic_starters = {
            'family': [
                # "Family is so important! Tell me about your family. Who are the most important people in your life?",
                # "I'd love to hear about your family. What traditions does your family have that are special to you?",
                # "Family relationships can be so interesting! How would you describe your family to someone new?"
                "Family is such a wonderful topic! Tell me about your family - do you have siblings, parents, or other relatives you're close with?"
            ],
            'work': [
                # "Work is such a big part of our lives! What kind of work do you do, or what would you like to do?",
                # "I'm curious about your work experience. What's the most interesting part of your job or studies?",
                # "Career goals can be exciting to discuss! What are your hopes for your professional future?"
                "Work is something we all have experience with! What kind of work do you do, or what type of career are you interested in?"
            ],
            'hobbies': [
                # "Hobbies make life more enjoyable! What do you like to do in your free time?",
                # "I love hearing about people's interests! What activities bring you the most joy?",
                # "Free time activities tell us so much about a person! What are you passionate about?"
                "Hobbies are such a great way to practice English! What activities do you enjoy doing in your free time?"
            ],
            'culture': [
                # "Culture is so fascinating! What aspects of your culture are you most proud of?",
                # "I'm always interested in learning about different cultures. What would you want others to know about your background?",
                # "Cultural exchange is wonderful! What traditions from your culture do you think others would find interesting?"
                "Culture is fascinating! I'd love to learn about your culture or hear about other cultures that interest you. What would you like to share?"
            ],
            'food': [
                # "Food brings people together! What are some of your favorite dishes from your culture?",
                # "I love learning about different cuisines! What food from your country would you recommend to a friend?",
                # "Cooking and eating are such universal experiences! What role does food play in your family or culture?"
                "Food is one of my favorite topics! What's your favorite type of cuisine, or do you enjoy cooking?"
            ]
        }
    
    def _initialize_selenium_chatbot(self):
        """Initialize the original Selenium-based chatbot service"""
        try:
            # Import and initialize your original selenium chatbot
            from selenium_chatbot import SeleniumChatbot
            import uuid
            
            # Generate unique session ID
            self.user_context['session_id'] = str(uuid.uuid4())
            
            # Initialize the original selenium chatbot with proper settings
            self.selenium_client = SeleniumChatbot(
                headless=True,  # Run headless on Render
                timeout=30
            )
            
            # Try to initialize the chatbot
            if self.selenium_client.initialize():
                self.session_active = True
                logger.info(f"✅ Original Selenium chatbot service initialized (session: {self.user_context['session_id']})")
            else:
                logger.warning("Original Selenium chatbot initialization failed")
                self.selenium_client = None
                self.session_active = False
                
        except Exception as e:
            logger.error(f"Failed to initialize original Selenium chatbot service: {str(e)}")
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
    
    def analyze_message_context(self, message: str) -> Dict[str, Any]:
        """Analyze the user's message for context and intent"""
        message_lower = message.lower().strip()
        
        context = {
            'intent': 'general',
            'emotion': 'neutral',
            'complexity': len(message.split()),
            'contains_question': '?' in message,
            'personal_sharing': False
        }
        
        # Detect intent
        for intent_type, pattern_data in self.conversation_patterns.items():
            for pattern in pattern_data['patterns']:
                if re.search(pattern, message_lower):
                    context['intent'] = intent_type
                    break
            if context['intent'] != 'general':
                break
        
        # Detect emotional tone
        positive_words = ['good', 'great', 'love', 'like', 'happy', 'excited', 'wonderful', 'amazing']
        negative_words = ['bad', 'difficult', 'hard', 'sad', 'confused', 'frustrated', 'struggle']
        
        if any(word in message_lower for word in positive_words):
            context['emotion'] = 'positive'
        elif any(word in message_lower for word in negative_words):
            context['emotion'] = 'negative'
        
        # Detect personal sharing
        personal_indicators = ['i ', 'my ', 'me ', 'myself', 'my family', 'my work', 'my country']
        if any(indicator in message_lower for indicator in personal_indicators):
            context['personal_sharing'] = True
        
        return context
    
    def get_response(self, message: str, topic: str = 'general', history: List = None, user_level: str = 'beginner') -> str:
        """
        Main method to get AI response - now uses Selenium chatbot as primary source
        """
        try:
            # Set current topic context
            self.user_context['current_topic'] = topic
            self.user_context['language_level'] = user_level
            
            # Use conversation history if provided
            if history:
                self.conversation_history = history
            
            # Use Selenium chatbot for actual AI responses
            if self.selenium_client and self.use_selenium:
                try:
                    # Use the selenium chatbot implementation
                    response = self.selenium_client.get_response(
                        message=message,
                        topic=topic,
                        history=history,
                        user_level=user_level
                    )
                    if response and response.strip():
                        # Add this interaction to our conversation history
                        self._update_conversation_history(message, response)
                        return response
                except Exception as e:
                    logger.warning(f"Selenium chatbot service failed: {e}")
            
            # Only use fallback if selenium explicitly fails
            logger.info("Using contextual response fallback")
            response = self.generate_contextual_response(message, history)
            
            # Add topic-specific elements if appropriate
            if topic and topic != 'general' and topic in self.topic_starters:
                # Occasionally add topic-specific follow-ups
                if random.random() < 0.3:  # 30% chance
                    topic_followup = random.choice(self.topic_starters[topic])
                    response += f" {topic_followup}"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            # Fallback response
            return "I'm having a moment of trouble thinking of the right response! Could you tell me a bit more about what you'd like to discuss?"
    
    def _update_conversation_history(self, user_message: str, ai_response: str):
        """Update conversation history with the latest exchange"""
        self.conversation_history.append({
            'user_message': user_message,
            'ai_response': ai_response,
            'timestamp': datetime.now(),
            'source': 'render_chatbot'
        })

    def generate_contextual_response(self, user_message: str, conversation_history: List = None) -> str:
        """Generate a contextual response based on the user's message and conversation history"""
        
        # Analyze the current message
        context = self.analyze_message_context(user_message)
        
        # Update conversation history
        self.conversation_history.append({
            'user_message': user_message,
            'context': context,
            'timestamp': datetime.now()
        })
        
        # Get appropriate response based on intent
        intent = context['intent']
        if intent in self.conversation_patterns:
            responses = self.conversation_patterns[intent]['responses']
        else:
            responses = self.conversation_patterns['fallback']['responses']
        
        # Select response based on context
        if context['emotion'] == 'negative':
            # For negative emotions, be more supportive
            supportive_responses = [
                "I understand that can be challenging. Remember, every English learner faces difficulties - it's completely normal! What specific part would you like help with?",
                "Thank you for being honest about that. Learning English takes time, and you're doing better than you think! What would make this easier for you?",
                "I appreciate you sharing how you feel. Many successful English speakers went through the same challenges. How can I best support you right now?"
            ]
            if intent == 'difficulty_expressing':
                return random.choice(responses)
            else:
                return random.choice(supportive_responses)
        
        elif context['personal_sharing']:
            # For personal sharing, be more engaged
            personal_responses = [
                "Thank you for sharing something personal with me! That takes courage, especially in a second language. Your English expression is really developing well!",
                "I'm honored that you're comfortable sharing that with me! Personal stories are the heart of good conversation, and you're telling yours beautifully in English.",
                "What you've shared gives me such insight into who you are! This kind of meaningful conversation is exactly how we develop natural English skills."
            ]
            return random.choice(personal_responses) + " " + random.choice(responses)
        
        elif context['contains_question']:
            # For questions, acknowledge their curiosity
            question_responses = [
                "What an excellent question! I love your curiosity - it's the mark of a great language learner. ",
                "That's such a thoughtful question! Your inquisitive mind will take you far in English learning. ",
                "I'm impressed by your question! This kind of thinking shows real engagement with the language. "
            ]
            return random.choice(question_responses) + random.choice(responses)
        
        # Default response selection
        return random.choice(responses)
    
    def suggest_conversation_topic(self) -> str:
        """Suggest a new conversation topic"""
        topics = list(self.topic_starters.keys())
        topic = random.choice(topics)
        starter = random.choice(self.topic_starters[topic])
        
        return f"Let's try a new topic! {starter}"
    
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
