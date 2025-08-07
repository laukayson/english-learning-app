// Application Configuration for PythonAnywhere Deployment
const CONFIG = {
    // API Configuration - PythonAnywhere server configuration
    BACKEND_URL: 'https://laukayson.pythonanywhere.com',
    API_BASE_URL: 'https://laukayson.pythonanywhere.com',
    API: {
        BASE_URL: 'https://laukayson.pythonanywhere.com',
        ENDPOINTS: {
            CHAT: '/api/chat',
            TRANSLATE: '/api/translate',
            TTS: '/api/tts',
            STT: '/api/stt',
            PRONUNCIATION: '/api/pronunciation',
            GENERATE_IMAGE: '/api/generate-image',
            PROGRESS: '/api/progress',
            USER: '/api/user'
        },
        TIMEOUT: 45000, // 45 seconds (increased for PythonAnywhere)
        RATE_LIMIT: {
            REQUESTS_PER_MINUTE: 20, // Reduced for PythonAnywhere limits
            REQUESTS_PER_HOUR: 150   // Reduced for PythonAnywhere limits
        }
    },

    // Learning Levels and Topics
    LEVELS: {
        1: {
            name: 'Absolute Beginner',
            farsi: 'مبتدی مطلق',
            topics: [
                'greetings', 'family', 'about_me', 'numbers', 'appearance', 
                'clothes', 'food', 'meals', 'weather', 'body_parts', 
                'doctor_conversation', 'sports', 'time_activities', 
                'days_week', 'transportation', 'friends'
            ]
        },
        2: {
            name: 'Basic',
            farsi: 'پایه',
            topics: [
                'hometown', 'family_relatives', 'extended_family', 'all_about_me',
                'hobbies', 'jobs', 'restaurant', 'groceries', 'directions',
                'emergency', 'celebrations', 'situational', 'household_items',
                'medical_vocabulary', 'doctor_advanced', 'school', 'airport_1', 'airport_2'
            ]
        },
        3: {
            name: 'Intermediate',
            farsi: 'متوسط',
            topics: [
                'family_hometown_advanced', 'likes_dislikes', 'seasons_games',
                'appearance_advanced', 'outdoors', 'kuala_lumpur_transport',
                'food_advanced', 'eating_out', 'injury_body', 'doctor_detailed',
                'emotions_1', 'emotions_2', 'emotions_3', 'friends_advanced',
                'situational_advanced', 'time_daily_advanced', 'addresses', 'dentist'
            ]
        },
        4: {
            name: 'Advanced',
            farsi: 'پیشرفته',
            topics: [
                'novels_reading', 'complex_conversations', 'academic_english',
                'professional_communication', 'advanced_grammar'
            ]
        }
    },

    // Topic Details with emojis and descriptions
    TOPIC_DETAILS: {
        // Level 1
        'greetings': { emoji: '👋', name: 'Greetings', farsi: 'احوالپرسی' },
        'family': { emoji: '👨‍👩‍👧‍👦', name: 'Family', farsi: 'خانواده' },
        'about_me': { emoji: '🙋‍♂️', name: 'About Me', farsi: 'درباره من' },
        'numbers': { emoji: '🔢', name: 'Numbers', farsi: 'اعداد' },
        'appearance': { emoji: '👤', name: 'Appearance', farsi: 'ظاهر' },
        'clothes': { emoji: '👕', name: 'Clothes', farsi: 'لباس' },
        'food': { emoji: '🍎', name: 'Food', farsi: 'غذا' },
        'meals': { emoji: '🍽️', name: 'Meals', farsi: 'وعده‌های غذایی' },
        'weather': { emoji: '🌤️', name: 'Weather', farsi: 'آب و هوا' },
        'body_parts': { emoji: '👁️', name: 'Body Parts', farsi: 'اعضای بدن' },
        'doctor_conversation': { emoji: '👩‍⚕️', name: 'At the Doctor', farsi: 'نزد دکتر' },
        'sports': { emoji: '⚽', name: 'Sports', farsi: 'ورزش' },
        'time_activities': { emoji: '⏰', name: 'Time & Activities', farsi: 'زمان و فعالیت‌ها' },
        'days_week': { emoji: '📅', name: 'Days of Week', farsi: 'روزهای هفته' },
        'transportation': { emoji: '🚌', name: 'Transportation', farsi: 'حمل و نقل' },
        'friends': { emoji: '👫', name: 'Friends', farsi: 'دوستان' },

        // Level 2
        'hometown': { emoji: '🏘️', name: 'Hometown', farsi: 'زادگاه' },
        'family_relatives': { emoji: '👥', name: 'Family & Relatives', farsi: 'خانواده و بستگان' },
        'extended_family': { emoji: '👴👵', name: 'Extended Family', farsi: 'خانواده گسترده' },
        'all_about_me': { emoji: '📝', name: 'All About Me', farsi: 'همه چیز درباره من' },
        'hobbies': { emoji: '🎨', name: 'Hobbies', farsi: 'سرگرمی‌ها' },
        'jobs': { emoji: '💼', name: 'Jobs', farsi: 'مشاغل' },
        'restaurant': { emoji: '🍽️', name: 'Restaurant', farsi: 'رستوران' },
        'groceries': { emoji: '🛒', name: 'Groceries', farsi: 'خرید مواد غذایی' },
        'directions': { emoji: '🗺️', name: 'Directions', farsi: 'مسیریابی' },
        'emergency': { emoji: '🚨', name: 'Emergency', farsi: 'اورژانس' },
        'celebrations': { emoji: '🎉', name: 'Celebrations', farsi: 'جشن‌ها' },
        'situational': { emoji: '💬', name: 'Situational', farsi: 'موقعیتی' },
        'household_items': { emoji: '🏠', name: 'Household Items', farsi: 'وسایل خانه' },
        'medical_vocabulary': { emoji: '💊', name: 'Medical Terms', farsi: 'اصطلاحات پزشکی' },
        'doctor_advanced': { emoji: '🩺', name: 'Doctor (Advanced)', farsi: 'دکتر (پیشرفته)' },
        'school': { emoji: '🏫', name: 'School', farsi: 'مدرسه' },
        'airport_1': { emoji: '✈️', name: 'Airport Part 1', farsi: 'فرودگاه قسمت ۱' },
        'airport_2': { emoji: '🛂', name: 'Airport Part 2', farsi: 'فرودگاه قسمت ۲' },

        // Level 3
        'family_hometown_advanced': { emoji: '🏡', name: 'Family & Hometown', farsi: 'خانواده و زادگاه' },
        'likes_dislikes': { emoji: '👍👎', name: 'Likes & Dislikes', farsi: 'علایق و بیزاری‌ها' },
        'seasons_games': { emoji: '🌸🎮', name: 'Seasons & Games', farsi: 'فصل‌ها و بازی‌ها' },
        'appearance_advanced': { emoji: '💄', name: 'Appearance (Advanced)', farsi: 'ظاهر (پیشرفته)' },
        'outdoors': { emoji: '🌳', name: 'Outdoors', farsi: 'فضای باز' },
        'kuala_lumpur_transport': { emoji: '🚇', name: 'KL Transport', farsi: 'حمل و نقل کوالالامپور' },
        'food_advanced': { emoji: '🍛', name: 'Food (Advanced)', farsi: 'غذا (پیشرفته)' },
        'eating_out': { emoji: '🍴', name: 'Eating Out', farsi: 'غذا خوردن بیرون' },
        'injury_body': { emoji: '🤕', name: 'Injuries', farsi: 'آسیب‌ها' },
        'doctor_detailed': { emoji: '🏥', name: 'Doctor (Detailed)', farsi: 'دکتر (تفصیلی)' },
        'emotions_1': { emoji: '😊', name: 'Emotions Part 1', farsi: 'احساسات قسمت ۱' },
        'emotions_2': { emoji: '😢', name: 'Emotions Part 2', farsi: 'احساسات قسمت ۲' },
        'emotions_3': { emoji: '😡', name: 'Emotions Part 3', farsi: 'احساسات قسمت ۳' },
        'friends_advanced': { emoji: '🤝', name: 'Friendship (Advanced)', farsi: 'دوستی (پیشرفته)' },
        'situational_advanced': { emoji: '🎭', name: 'Complex Situations', farsi: 'موقعیت‌های پیچیده' },
        'time_daily_advanced': { emoji: '📊', name: 'Time Management', farsi: 'مدیریت زمان' },
        'addresses': { emoji: '📮', name: 'Addresses', farsi: 'آدرس‌ها' },
        'dentist': { emoji: '🦷', name: 'Dentist', farsi: 'دندانپزشک' },

        // Level 4
        'novels_reading': { emoji: '📚', name: 'Reading & Literature', farsi: 'خواندن و ادبیات' },
        'complex_conversations': { emoji: '🗨️', name: 'Complex Conversations', farsi: 'گفتگوهای پیچیده' },
        'academic_english': { emoji: '🎓', name: 'Academic English', farsi: 'انگلیسی آکادمیک' },
        'professional_communication': { emoji: '💻', name: 'Professional Communication', farsi: 'ارتباطات حرفه‌ای' },
        'advanced_grammar': { emoji: '📖', name: 'Advanced Grammar', farsi: 'گرامر پیشرفته' }
    },

    // Phrase Packs for Real-world Scenarios
    PHRASE_PACKS: {
        'hospital': {
            name: 'At the Hospital',
            farsi: 'در بیمارستان',
            emoji: '🏥',
            phrases: [
                { en: 'I need to see a doctor', farsi: 'من باید دکتر ببینم' },
                { en: 'Where is the emergency room?', farsi: 'اتاق اورژانس کجاست؟' },
                { en: 'I have insurance', farsi: 'من بیمه دارم' },
                { en: 'It hurts here', farsi: 'اینجا درد می‌کند' }
            ]
        },
        'grocery': {
            name: 'Buying Groceries',
            farsi: 'خرید مواد غذایی',
            emoji: '🛒',
            phrases: [
                { en: 'Where can I find bread?', farsi: 'نان را کجا می‌توانم پیدا کنم؟' },
                { en: 'How much does this cost?', farsi: 'این چقدر قیمت دارد؟' },
                { en: 'Do you have fresh vegetables?', farsi: 'سبزیجات تازه دارید؟' },
                { en: 'Can I pay with card?', farsi: 'می‌توانم با کارت پرداخت کنم؟' }
            ]
        },
        'school': {
            name: "Talking to Your Child's Teacher",
            farsi: 'صحبت با معلم فرزندتان',
            emoji: '👩‍🏫',
            phrases: [
                { en: 'How is my child doing?', farsi: 'فرزندم چطور پیش می‌رود؟' },
                { en: 'Does my child need extra help?', farsi: 'آیا فرزندم به کمک اضافی نیاز دارد؟' },
                { en: 'When are parent-teacher conferences?', farsi: 'جلسات والدین و معلمان کی است؟' },
                { en: 'What homework does my child have?', farsi: 'فرزندم چه تکالیفی دارد؟' }
            ]
        }
    },

    // Voice Configuration
    VOICE: {
        LANGUAGES: {
            EN: 'en-US',
            FARSI: 'fa-IR'
        },
        RATE: 0.9,
        PITCH: 1.0,
        VOLUME: 1.0
    },

    // Gamification Settings
    GAMIFICATION: {
        DAILY_GOAL: 3, // phrases per day
        STREAK_BONUS: 5, // points for maintaining streak
        COMPLETION_POINTS: 10, // points per topic completion
        PRACTICE_POINTS: 2, // points per practice session
        LEVELS: {
            BEGINNER: 0,
            INTERMEDIATE: 100,
            ADVANCED: 300,
            EXPERT: 600
        }
    },

    // Spaced Repetition Settings (SM-2 Algorithm)
    SPACED_REPETITION: {
        INITIAL_INTERVAL: 1, // days
        EASY_FACTOR: 2.5,
        MIN_FACTOR: 1.3,
        FACTOR_CHANGE: 0.1,
        MIN_INTERVAL: 1,
        MAX_INTERVAL: 365
    },

    // Feature Flags - Some features disabled for PythonAnywhere limitations
    FEATURES: {
        VOICE_INPUT: true,
        PRONUNCIATION_CHECK: false, // May have issues on PythonAnywhere
        IMAGE_GENERATION: false, // Disabled due to potential resource limits
        FARSI_AUDIO: true,
        GAMIFICATION: true,
        SPACED_REPETITION: true,
        PROGRESS_TRACKING: true,
        RATE_LIMITING: true
    },

    // UI Settings
    UI: {
        ANIMATION_DURATION: 300,
        TYPING_DELAY: 50,
        AUTO_SCROLL_DELAY: 100,
        MODAL_ANIMATION: 300
    },

    // Storage Keys
    STORAGE_KEYS: {
        USER_PROFILE: 'user_profile',
        PROGRESS: 'user_progress',
        SETTINGS: 'app_settings',
        CONVERSATION_HISTORY: 'conversation_history',
        SPACED_REPETITION_DATA: 'spaced_repetition',
        RATE_LIMIT_DATA: 'rate_limit_data'
    },

    // Error Messages
    ERRORS: {
        NETWORK: 'Network connection error. Please check your internet connection.',
        RATE_LIMIT: 'Too many requests. Please wait a moment before trying again.',
        VOICE_NOT_SUPPORTED: 'Voice features are not supported in your browser.',
        MICROPHONE_ACCESS: 'Microphone access is required for voice features.',
        GENERAL: 'Something went wrong. Please try again.'
    },

    // Development Settings - Production configuration
    DEV: {
        DEBUG: false,
        MOCK_API: false,
        LOG_LEVEL: 'warn' // Reduced logging for production
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
