# Simplified AI Models Service for Render Deployment
# Lightweight conversational AI without heavy dependencies

import logging
from typing import List, Dict, Any, Optional
import json
import random
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class AIModels:
    """Simplified AI models service for Render deployment"""
    
    def __init__(self):
        self.ready = False
        self.conversation_templates = self._load_conversation_templates()
        self.topic_responses = self._load_topic_responses()
        self.initialize()
    
    def initialize(self):
        """Initialize the AI service"""
        try:
            logger.info("Initializing simplified AI models service for Render...")
            self.ready = True
            logger.info("✅ AI models service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AI service: {e}")
            self.ready = False
    
    def is_ready(self) -> bool:
        """Check if AI models are ready"""
        return self.ready
    
    def generate_conversation_response(self, message: str, topic: str, history: List[Dict] = None, user_level: str = 'beginner') -> str:
        """Generate AI response for conversation"""
        try:
            if not self.ready:
                return "I'm sorry, I'm not ready to chat right now. Please try again."
            
            message_lower = message.lower().strip()
            
            # Convert string level to numeric
            level_map = {'beginner': 1, 'elementary': 2, 'intermediate': 3, 'advanced': 4}
            level_num = level_map.get(user_level, 1)
            
            # Context-aware responses
            if self._is_greeting(message_lower):
                return self._get_greeting_response(topic, level_num)
            elif self._is_question(message_lower):
                return self._get_question_response(message_lower, topic, level_num)
            elif self._expresses_difficulty(message_lower):
                return self._get_supportive_response(level_num)
            elif self._is_gratitude(message_lower):
                return self._get_gratitude_response(level_num)
            else:
                return self._get_topic_response(message, topic, level_num)
                
        except Exception as e:
            logger.error(f"Error generating conversation response: {e}")
            return "I'm having trouble understanding. Could you please try again?"
    
    def _load_conversation_templates(self) -> Dict:
        """Load conversation templates"""
        return {
            'greetings': {
                1: [  # Beginner
                    "Hello! Nice to meet you. What is your name?",
                    "Hi there! How are you today?",
                    "Good to see you! Let's practice English together.",
                    "Welcome! Are you ready to learn English?"
                ],
                2: [  # Elementary
                    "Hello! It's great to meet you. What would you like to talk about?",
                    "Hi! I'm excited to help you practice English today.",
                    "Good day! How has your English learning been going?",
                    "Nice to see you! What topics interest you most?"
                ],
                3: [  # Intermediate
                    "Hello! I'm delighted to have this conversation with you. What's on your mind today?",
                    "Greetings! I hope you're having a wonderful day. What would you like to discuss?",
                    "Hi there! I'm here to help you improve your English. What shall we talk about?",
                    "Good to see you again! How has your language learning journey been progressing?"
                ],
                4: [  # Advanced
                    "Hello! I'm pleased to engage in conversation with you today. What topics or themes interest you?",
                    "Greetings! I hope you're doing well. What thought-provoking subjects would you like to explore?",
                    "Good day! I'm eager to have a meaningful discussion with you. What's been on your mind lately?",
                    "Welcome! I'm looking forward to our conversation. What aspects of life or learning intrigue you?"
                ]
            },
            'supportive': {
                1: [
                    "Don't worry! Learning English takes time. You are doing great!",
                    "It's okay to make mistakes. That's how we learn!",
                    "Keep trying! English gets easier with practice.",
                    "You can do it! Every day you get better."
                ],
                2: [
                    "I understand that English can be challenging. You're making good progress!",
                    "Don't be discouraged! Every learner faces difficulties. You're doing well.",
                    "Remember, making mistakes is part of learning. Keep practicing!",
                    "You're improving every day! English takes time but you're on the right path."
                ],
                3: [
                    "I appreciate that learning English presents challenges, but your dedication is admirable.",
                    "It's perfectly normal to encounter difficulties. Your persistence will pay off!",
                    "Please don't feel frustrated. Language learning is a gradual process, and you're making excellent progress.",
                    "Your commitment to improvement is inspiring. Keep up the wonderful work!"
                ],
                4: [
                    "I recognize that mastering English can be intellectually demanding, but your analytical approach is commendable.",
                    "Language acquisition at advanced levels requires nuanced understanding, which you're developing admirably.",
                    "The complexities of English are substantial, yet your sophisticated engagement demonstrates remarkable progress.",
                    "Your pursuit of linguistic excellence reflects both dedication and intellectual curiosity."
                ]
            }
        }
    
    def _load_topic_responses(self) -> Dict:
        """Load topic-specific response templates"""
        return {
            'family': {
                'questions': [
                    "Tell me about your family. How many people are in your family?",
                    "What do you like to do with your family?",
                    "Who is your favorite family member and why?",
                    "What traditions does your family have?"
                ],
                'responses': [
                    "Family is very important! Thank you for sharing that with me.",
                    "That sounds like a wonderful family tradition.",
                    "Your family sounds very caring and supportive.",
                    "It's beautiful how families can be so different yet so loving."
                ]
            },
            'food': {
                'questions': [
                    "What is your favorite food from your country?",
                    "Do you like to cook? What do you make?",
                    "What did you eat for breakfast today?",
                    "What foods would you like to try?"
                ],
                'responses': [
                    "That sounds delicious! I'd love to learn more about that dish.",
                    "Food is such a wonderful way to learn about culture.",
                    "Your country's cuisine sounds very interesting.",
                    "Cooking together is a great way to bond with family and friends."
                ]
            },
            'hobbies': {
                'questions': [
                    "What do you like to do in your free time?",
                    "Do you have any hobbies that you're passionate about?",
                    "What activities make you happy?",
                    "Do you prefer indoor or outdoor activities?"
                ],
                'responses': [
                    "That hobby sounds really interesting! How long have you been doing it?",
                    "It's wonderful that you have activities you enjoy.",
                    "Hobbies are a great way to relax and learn new skills.",
                    "Your interests show that you're a well-rounded person."
                ]
            },
            'school': {
                'questions': [
                    "What subjects do you study in school?",
                    "What is your favorite subject and why?",
                    "Do you have any goals for your education?",
                    "How do you like to study?"
                ],
                'responses': [
                    "Education is so important for building a bright future.",
                    "That subject sounds challenging but rewarding.",
                    "Your dedication to learning is really admirable.",
                    "School can be difficult sometimes, but you're doing great!"
                ]
            },
            'general': {
                'questions': [
                    "How has your day been so far?",
                    "What are you looking forward to this week?",
                    "Is there anything new you've learned recently?",
                    "What makes you feel happy?"
                ],
                'responses': [
                    "Thank you for sharing that with me. Tell me more!",
                    "That's really interesting. What do you think about it?",
                    "I enjoy hearing about your experiences.",
                    "Your perspective on this is very thoughtful."
                ]
            }
        }
    
    def _is_greeting(self, message: str) -> bool:
        """Check if message is a greeting"""
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'how are you']
        return any(greeting in message for greeting in greetings)
    
    def _is_question(self, message: str) -> bool:
        """Check if message contains a question"""
        question_words = ['what', 'where', 'when', 'why', 'how', 'who', 'which', 'can you', 'do you', 'are you']
        return any(word in message for word in question_words) or message.endswith('?')
    
    def _expresses_difficulty(self, message: str) -> bool:
        """Check if message expresses difficulty or frustration"""
        difficulty_words = ['difficult', 'hard', 'challenging', 'confused', 'don\'t understand', 'struggle', 'trouble']
        return any(word in message for word in difficulty_words)
    
    def _is_gratitude(self, message: str) -> bool:
        """Check if message expresses gratitude"""
        gratitude_words = ['thank', 'thanks', 'appreciate', 'grateful']
        return any(word in message for word in gratitude_words)
    
    def _get_greeting_response(self, topic: str, level: int) -> str:
        """Get greeting response based on level"""
        responses = self.conversation_templates['greetings'].get(level, self.conversation_templates['greetings'][1])
        return random.choice(responses)
    
    def _get_question_response(self, message: str, topic: str, level: int) -> str:
        """Generate response to questions"""
        responses = [
            "That's a great question! What do you think about it?",
            "I'd love to hear your thoughts on that first.",
            "What's your opinion on this topic?",
            "That's interesting to think about. How would you answer that?",
            "Let's explore that together. What comes to mind?"
        ]
        
        if level >= 3:
            responses.extend([
                "That's a thought-provoking question. I'm curious about your perspective.",
                "Your inquiry demonstrates sophisticated thinking. What insights do you have?",
                "That's an excellent question that merits careful consideration."
            ])
        
        return random.choice(responses)
    
    def _get_supportive_response(self, level: int) -> str:
        """Get supportive response for difficulties"""
        responses = self.conversation_templates['supportive'].get(level, self.conversation_templates['supportive'][1])
        return random.choice(responses)
    
    def _get_gratitude_response(self, level: int) -> str:
        """Get response to gratitude"""
        responses = {
            1: ["You're welcome! Keep practicing!", "Happy to help!", "No problem! You're doing great!"],
            2: ["You're very welcome! I'm glad I could help.", "My pleasure! Keep up the good work!", "Happy to assist you with your learning!"],
            3: ["You're most welcome! I'm delighted to support your learning journey.", "It's my pleasure to help you improve your English.", "I'm glad I could be of assistance!"],
            4: ["You're exceptionally welcome! I'm honored to contribute to your linguistic development.", "It's genuinely my pleasure to facilitate your language acquisition.", "I'm delighted to support your educational endeavors."]
        }
        level_responses = responses.get(level, responses[1])
        return random.choice(level_responses)
    
    def _get_topic_response(self, message: str, topic: str, level: int) -> str:
        """Get topic-specific response"""
        topic_data = self.topic_responses.get(topic, self.topic_responses['general'])
        
        # Sometimes ask a question, sometimes give a response
        if random.choice([True, False]):
            return random.choice(topic_data['questions'])
        else:
            return random.choice(topic_data['responses'])
    
    def suggest_conversation_topic(self, level: int = 1) -> str:
        """Suggest a conversation topic"""
        topics = {
            1: [
                "Let's talk about your family. Tell me about the people you live with.",
                "What did you eat today? I'd love to hear about your meals.",
                "What do you like to do for fun? Tell me about your hobbies.",
                "How was your day today? What did you do?"
            ],
            2: [
                "I'd like to learn about your hometown. Can you describe where you're from?",
                "What are your favorite activities on the weekend? How do you relax?",
                "Tell me about your studies or work. What do you do during the day?",
                "What are your dreams for the future? What would you like to achieve?"
            ],
            3: [
                "What aspects of your culture are you most proud of? I'd love to learn more.",
                "How has technology changed your daily life? What's your perspective?",
                "What social issues are important to you? Why do they matter?",
                "Describe a challenging experience that helped you grow as a person."
            ],
            4: [
                "What philosophical questions interest you most? How do you approach complex ideas?",
                "How do you think globalization affects local communities and traditions?",
                "What role should education play in addressing societal challenges?",
                "How do you balance personal aspirations with social responsibilities?"
            ]
        }
        
        level_topics = topics.get(level, topics[1])
        return random.choice(level_topics)
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        return {
            'service': 'simplified_ai',
            'platform': 'render',
            'ready': self.ready,
            'features': {
                'conversation': True,
                'topic_responses': True,
                'level_adaptation': True,
                'context_awareness': True
            },
            'limitations': {
                'advanced_ai': False,
                'selenium_features': False,
                'voice_processing': False
            }
        }

# Test the service
if __name__ == "__main__":
    ai = AIModels()
    
    test_messages = [
        ("Hello!", "general", 1),
        ("I'm learning English and it's difficult", "general", 2),
        ("Tell me about your family", "family", 1),
        ("What should I do to improve?", "general", 3),
        ("Thank you for helping me", "general", 2)
    ]
    
    print("Simplified AI Models Test (Render Version)")
    print("=" * 50)
    
    for msg, topic, level in test_messages:
        response = ai.generate_conversation_response(msg, topic, [], f"level_{level}")
        print(f"User (Level {level}): {msg}")
        print(f"AI: {response}")
        print("-" * 30)
