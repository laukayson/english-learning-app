# Configuration for Language Learning App Backend

# Learning levels and their topics
LEVEL_TOPICS = {
    "1": [
        "greetings", "family", "about_me", "numbers", "appearance", 
        "clothes", "food", "meals", "weather", "body_parts", 
        "doctor_conversation", "sports", "time_activities", 
        "days_week", "transportation", "friends"
    ],
    "2": [
        "hometown", "family_relatives", "extended_family", "all_about_me",
        "hobbies", "jobs", "restaurant", "groceries", "directions",
        "emergency", "celebrations", "situational", "household_items",
        "medical_vocabulary", "doctor_advanced", "school", "airport_1", "airport_2"
    ],
    "3": [
        "family_hometown_advanced", "likes_dislikes", "seasons_games",
        "appearance_advanced", "outdoors", "kuala_lumpur_transport",
        "food_advanced", "eating_out", "injury_body", "doctor_detailed",
        "emotions_1", "emotions_2", "emotions_3", "friends_advanced",
        "situational_advanced", "time_daily_advanced", "addresses", "dentist"
    ],
    "4": [
        "novels_reading", "complex_conversations", "academic_english",
        "professional_communication", "advanced_grammar"
    ]
}

# Topic details with names and translations
TOPIC_DETAILS = {
    # Level 1
    'greetings': {'name': 'Greetings', 'farsi': 'احوالپرسی', 'emoji': '👋'},
    'family': {'name': 'Family', 'farsi': 'خانواده', 'emoji': '👨‍👩‍👧‍👦'},
    'about_me': {'name': 'About Me', 'farsi': 'درباره من', 'emoji': '🙋‍♂️'},
    'numbers': {'name': 'Numbers', 'farsi': 'اعداد', 'emoji': '🔢'},
    'appearance': {'name': 'Appearance', 'farsi': 'ظاهر', 'emoji': '👤'},
    'clothes': {'name': 'Clothes', 'farsi': 'لباس', 'emoji': '👕'},
    'food': {'name': 'Food', 'farsi': 'غذا', 'emoji': '🍎'},
    'meals': {'name': 'Meals', 'farsi': 'وعده‌های غذایی', 'emoji': '🍽️'},
    'weather': {'name': 'Weather', 'farsi': 'آب و هوا', 'emoji': '🌤️'},
    'body_parts': {'name': 'Body Parts', 'farsi': 'اعضای بدن', 'emoji': '👁️'},
    'doctor_conversation': {'name': 'At the Doctor', 'farsi': 'نزد دکتر', 'emoji': '👩‍⚕️'},
    'sports': {'name': 'Sports', 'farsi': 'ورزش', 'emoji': '⚽'},
    'time_activities': {'name': 'Time & Activities', 'farsi': 'زمان و فعالیت‌ها', 'emoji': '⏰'},
    'days_week': {'name': 'Days of Week', 'farsi': 'روزهای هفته', 'emoji': '📅'},
    'transportation': {'name': 'Transportation', 'farsi': 'حمل و نقل', 'emoji': '🚌'},
    'friends': {'name': 'Friends', 'farsi': 'دوستان', 'emoji': '👫'},
    
    # Level 2
    'hometown': {'name': 'Hometown', 'farsi': 'زادگاه', 'emoji': '🏘️'},
    'family_relatives': {'name': 'Family & Relatives', 'farsi': 'خانواده و بستگان', 'emoji': '👥'},
    'extended_family': {'name': 'Extended Family', 'farsi': 'خانواده گسترده', 'emoji': '👴👵'},
    'all_about_me': {'name': 'All About Me', 'farsi': 'همه چیز درباره من', 'emoji': '📝'},
    'hobbies': {'name': 'Hobbies', 'farsi': 'سرگرمی‌ها', 'emoji': '🎨'},
    'jobs': {'name': 'Jobs', 'farsi': 'مشاغل', 'emoji': '💼'},
    'restaurant': {'name': 'Restaurant', 'farsi': 'رستوران', 'emoji': '🍽️'},
    'groceries': {'name': 'Groceries', 'farsi': 'خرید مواد غذایی', 'emoji': '🛒'},
    'directions': {'name': 'Directions', 'farsi': 'مسیریابی', 'emoji': '🗺️'},
    'emergency': {'name': 'Emergency', 'farsi': 'اورژانس', 'emoji': '🚨'},
    'celebrations': {'name': 'Celebrations', 'farsi': 'جشن‌ها', 'emoji': '🎉'},
    'situational': {'name': 'Situational', 'farsi': 'موقعیتی', 'emoji': '💬'},
    'household_items': {'name': 'Household Items', 'farsi': 'وسایل خانه', 'emoji': '🏠'},
    'medical_vocabulary': {'name': 'Medical Terms', 'farsi': 'اصطلاحات پزشکی', 'emoji': '💊'},
    'doctor_advanced': {'name': 'Doctor (Advanced)', 'farsi': 'دکتر (پیشرفته)', 'emoji': '🩺'},
    'school': {'name': 'School', 'farsi': 'مدرسه', 'emoji': '🏫'},
    'airport_1': {'name': 'Airport Part 1', 'farsi': 'فرودگاه قسمت ۱', 'emoji': '✈️'},
    'airport_2': {'name': 'Airport Part 2', 'farsi': 'فرودگاه قسمت ۲', 'emoji': '🛂'},
    
    # Level 3
    'family_hometown_advanced': {'name': 'Family & Hometown', 'farsi': 'خانواده و زادگاه', 'emoji': '🏡'},
    'likes_dislikes': {'name': 'Likes & Dislikes', 'farsi': 'علایق و بیزاری‌ها', 'emoji': '👍👎'},
    'seasons_games': {'name': 'Seasons & Games', 'farsi': 'فصل‌ها و بازی‌ها', 'emoji': '🌸🎮'},
    'appearance_advanced': {'name': 'Appearance (Advanced)', 'farsi': 'ظاهر (پیشرفته)', 'emoji': '💄'},
    'outdoors': {'name': 'Outdoors', 'farsi': 'فضای باز', 'emoji': '🌳'},
    'kuala_lumpur_transport': {'name': 'KL Transport', 'farsi': 'حمل و نقل کوالالامپور', 'emoji': '🚇'},
    'food_advanced': {'name': 'Food (Advanced)', 'farsi': 'غذا (پیشرفته)', 'emoji': '🍛'},
    'eating_out': {'name': 'Eating Out', 'farsi': 'غذا خوردن بیرون', 'emoji': '🍴'},
    'injury_body': {'name': 'Injuries', 'farsi': 'آسیب‌ها', 'emoji': '🤕'},
    'doctor_detailed': {'name': 'Doctor (Detailed)', 'farsi': 'دکتر (تفصیلی)', 'emoji': '🏥'},
    'emotions_1': {'name': 'Emotions Part 1', 'farsi': 'احساسات قسمت ۱', 'emoji': '😊'},
    'emotions_2': {'name': 'Emotions Part 2', 'farsi': 'احساسات قسمت ۲', 'emoji': '😢'},
    'emotions_3': {'name': 'Emotions Part 3', 'farsi': 'احساسات قسمت ۳', 'emoji': '😡'},
    'friends_advanced': {'name': 'Friendship (Advanced)', 'farsi': 'دوستی (پیشرفته)', 'emoji': '🤝'},
    'situational_advanced': {'name': 'Complex Situations', 'farsi': 'موقعیت‌های پیچیده', 'emoji': '🎭'},
    'time_daily_advanced': {'name': 'Time Management', 'farsi': 'مدیریت زمان', 'emoji': '📊'},
    'addresses': {'name': 'Addresses', 'farsi': 'آدرس‌ها', 'emoji': '📮'},
    'dentist': {'name': 'Dentist', 'farsi': 'دندانپزشک', 'emoji': '🦷'},
    
    # Level 4
    'novels_reading': {'name': 'Reading & Literature', 'farsi': 'خواندن و ادبیات', 'emoji': '📚'},
    'complex_conversations': {'name': 'Complex Conversations', 'farsi': 'گفتگوهای پیچیده', 'emoji': '🗨️'},
    'academic_english': {'name': 'Academic English', 'farsi': 'انگلیسی آکادمیک', 'emoji': '🎓'},
    'professional_communication': {'name': 'Professional Communication', 'farsi': 'ارتباطات حرفه‌ای', 'emoji': '💻'},
    'advanced_grammar': {'name': 'Advanced Grammar', 'farsi': 'گرامر پیشرفته', 'emoji': '📖'}
}

# Conversation templates for different scenarios
CONVERSATION_TEMPLATES = {
    'introduction': {
        'teacher_start': "Hello! I'm your English teacher. What's your name?",
        'follow_ups': [
            "Nice to meet you, {name}! How are you feeling today?",
            "Where are you from, {name}?",
            "How long have you been learning English?"
        ]
    },
    'topic_introduction': {
        'start': "Today we're going to talk about {topic}. Are you ready?",
        'encouragement': [
            "Great job!",
            "That's correct!",
            "Very good!",
            "Excellent!",
            "Well done!",
            "Perfect!"
        ],
        'help': [
            "Let me help you with that.",
            "Here's another way to say it:",
            "Try this instead:",
            "Don't worry, let's practice together."
        ]
    },
    'practice_scenarios': {
        'restaurant': [
            "You are at a restaurant. What would you like to order?",
            "The waiter is asking about drinks. What do you say?",
            "How do you ask for the bill?"
        ],
        'doctor': [
            "You need to see a doctor. How do you explain your problem?",
            "The doctor asks about your symptoms. What do you say?",
            "How do you ask about medicine?"
        ],
        'grocery': [
            "You're at the grocery store. How do you ask where something is?",
            "You can't find what you need. What do you ask?",
            "How do you ask about the price?"
        ]
    }
}

# Phrase packs for real-world scenarios
PHRASE_PACKS = {
    'essential_phrases': [
        {'en': 'Excuse me', 'farsi': 'ببخشید'},
        {'en': 'Thank you', 'farsi': 'متشکرم'},
        {'en': 'Please', 'farsi': 'لطفاً'},
        {'en': 'I\'m sorry', 'farsi': 'متأسفم'},
        {'en': 'Help me', 'farsi': 'کمکم کنید'},
    ],
    'hospital': [
        {'en': 'I need to see a doctor', 'farsi': 'من باید دکتر ببینم'},
        {'en': 'Where is the emergency room?', 'farsi': 'اتاق اورژانس کجاست؟'},
        {'en': 'I have insurance', 'farsi': 'من بیمه دارم'},
        {'en': 'It hurts here', 'farsi': 'اینجا درد می‌کند'},
        {'en': 'I need medicine', 'farsi': 'به دارو نیاز دارم'},
    ],
    'grocery': [
        {'en': 'Where can I find bread?', 'farsi': 'نان را کجا می‌توانم پیدا کنم؟'},
        {'en': 'How much does this cost?', 'farsi': 'این چقدر قیمت دارد؟'},
        {'en': 'Do you have fresh vegetables?', 'farsi': 'سبزیجات تازه دارید؟'},
        {'en': 'Can I pay with card?', 'farsi': 'می‌توانم با کارت پرداخت کنم؟'},
        {'en': 'Where is the checkout?', 'farsi': 'صندوق فروش کجاست؟'},
    ],
    'school': [
        {'en': 'How is my child doing?', 'farsi': 'فرزندم چطور پیش می‌رود؟'},
        {'en': 'Does my child need extra help?', 'farsi': 'آیا فرزندم به کمک اضافی نیاز دارد؟'},
        {'en': 'When are parent-teacher conferences?', 'farsi': 'جلسات والدین و معلمان کی است؟'},
        {'en': 'What homework does my child have?', 'farsi': 'فرزندم چه تکالیفی دارد؟'},
        {'en': 'Is my child participating in class?', 'farsi': 'آیا فرزندم در کلاس شرکت می‌کند؟'},
    ],
    'transportation': [
        {'en': 'Where is the bus stop?', 'farsi': 'ایستگاه اتوبوس کجاست؟'},
        {'en': 'How much is the fare?', 'farsi': 'کرایه چقدر است؟'},
        {'en': 'Which bus goes to the city center?', 'farsi': 'کدام اتوبوس به مرکز شهر می‌رود؟'},
        {'en': 'Is this the right platform?', 'farsi': 'آیا این سکوی درست است؟'},
        {'en': 'When does the next train arrive?', 'farsi': 'قطار بعدی کی می‌رسد؟'},
    ]
}

# Spaced repetition settings (SM-2 algorithm)
SPACED_REPETITION_CONFIG = {
    'initial_interval': 1,
    'minimum_interval': 1,
    'maximum_interval': 365,
    'easy_factor': 2.5,
    'minimum_factor': 1.3,
    'factor_increment': 0.1,
    'factor_decrement': 0.2
}

# Gamification settings
GAMIFICATION_CONFIG = {
    'points': {
        'conversation_message': 2,
        'correct_pronunciation': 5,
        'topic_completion': 25,
        'daily_challenge': 10,
        'streak_bonus': 5
    },
    'badges': {
        'first_conversation': {'name': 'First Steps', 'description': 'Started first conversation'},
        'week_streak': {'name': 'Consistent Learner', 'description': '7 days in a row'},
        'topic_master': {'name': 'Topic Master', 'description': 'Completed all topics in a level'},
        'pronunciation_expert': {'name': 'Clear Speaker', 'description': '50 correct pronunciations'}
    }
}

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    'requests_per_minute': 30,
    'requests_per_hour': 200,
    'requests_per_day': 1000,
    'image_generation_per_hour': 10,
    'ai_chat_per_minute': 10
}

# AI model configuration
AI_CONFIG = {
    'conversation_model': 'microsoft/DialoGPT-small',
    'translation_model': 'Helsinki-NLP/opus-mt-en-fa',
    'grammar_model': 'textattack/distilbert-base-uncased-CoLA',
    'image_model': 'runwayml/stable-diffusion-v1-5',
    'max_tokens': 512,
    'temperature': 0.7
}

# Voice configuration
VOICE_CONFIG = {
    'sample_rate': 16000,
    'channels': 1,
    'chunk_size': 1024,
    'supported_formats': ['wav', 'mp3', 'ogg'],
    'max_duration': 30,  # seconds
    'pronunciation_threshold': 0.7
}

# Image generation configuration
IMAGE_CONFIG = {
    'default_style': 'educational illustration',
    'image_size': '512x512',
    'quality': 'standard',
    'max_images_per_session': 5
}

# Database configuration
DATABASE_CONFIG = {
    'name': 'database.db',
    'backup_interval': 24,  # hours
    'cleanup_old_conversations': 90,  # days
    'max_conversation_length': 50  # messages
}
