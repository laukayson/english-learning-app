# Render-specific configuration
import os
from urllib.parse import urlparse

# Environment detection
ENVIRONMENT = os.environ.get('FLASK_ENV', 'development')
IS_RENDER = os.environ.get('RENDER', False)

# Database Configuration for Turso
TURSO_DATABASE_URL = os.environ.get('TURSO_DATABASE_URL')
TURSO_AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN')

# Fallback to local SQLite for development
if not TURSO_DATABASE_URL:
    TURSO_DATABASE_URL = 'file:data/db/language_app.db'
    TURSO_AUTH_TOKEN = None

# Render-specific settings
RENDER_CONFIG = {
    'disable_selenium': True,  # Selenium not supported on Render free tier
    'use_turso_db': True,
    'port': int(os.environ.get('PORT', 5000)),
    'host': '0.0.0.0',
    'debug': False if IS_RENDER else True
}

# Feature toggles for Render
FEATURES = {
    'selenium_chatbot': False,  # Disabled on Render
    'web_stt': False,  # Disabled on Render  
    'voice_features': False,  # Disabled on Render
    'browser_automation': False,  # Disabled on Render
    'ai_chat': True,  # Keep text-based chat
    'translation': True,  # Keep translation features
    'progress_tracking': True,  # Keep progress tracking
    'user_management': True  # Keep user system
}

# Learning levels and their topics (same as main config)
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

# Topic details with names and translations (same as main config)
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
