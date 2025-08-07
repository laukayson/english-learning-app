/**
 * AI Integration Manager for English Learning App
 * 
 * This module provides comprehensive AI functionality including:
 * - Conversation generation with contextual responses
 * - Grammar checking and corrections
 * - Educational image generation
 * - Practice exercise creation
 * - Rate limiting and request queue management
 * - Fallback systems for offline functionality
 * 
 * Dependencies: CONFIG, Utils, storage (global Storage instance)
 */

class AIManager {
    constructor() {
        this.isAvailable = false;
        this.modelStatus = {
            conversation: 'unknown',
            translation: 'unknown',
            grammar: 'unknown',
            image: 'unknown'
        };
        this.requestQueue = [];
        this.isProcessingQueue = false;
        this.rateLimitInfo = {
            requests_remaining: 100,
            reset_time: null,
            blocked_until: null
        };
    }

    // Initialise AI services
    async initialise() {
        try {
            Utils.log('Initialising AI services...');
            
            // Check AI service availability
            await this.checkServiceAvailability();
            
            // Load rate limit info
            await this.loadRateLimitInfo();
            
            Utils.log('AI services initialised', this.modelStatus);
            
        } catch (error) {
            Utils.log('AI initialisation error:', error);
            this.isAvailable = false;
        }
    }

    // Check if AI services are available
    async checkServiceAvailability() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/ai/status`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const statusData = await response.json();
                this.modelStatus = statusData.models || this.modelStatus;
                this.isAvailable = statusData.available || false;
                this.rateLimitInfo = statusData.rate_limit || this.rateLimitInfo;
            } else {
                this.isAvailable = false;
            }

        } catch (error) {
            Utils.log('Service availability check failed:', error);
            this.isAvailable = false;
        }
    }

    // Load rate limit information
    async loadRateLimitInfo() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/ai/rate-limit`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const limitData = await response.json();
                this.rateLimitInfo = limitData;
            }

        } catch (error) {
            Utils.log('Rate limit check failed:', error);
        }
    }

    // Check if AI requests are currently blocked
    isBlocked() {
        if (this.rateLimitInfo.blocked_until) {
            const blockTime = new Date(this.rateLimitInfo.blocked_until);
            return new Date() < blockTime;
        }
        return false;
    }

    // Generate conversation response
    async generateConversationResponse(userMessage, context, conversationHistory = []) {
        if (!this.isAvailable || this.isBlocked()) {
            return this.generateFallbackResponse(userMessage, context);
        }

        try {
            const requestData = {
                user_message: userMessage,
                context: context,
                conversation_history: conversationHistory.slice(-5), // Last 5 messages for context
                user_level: storage.getUserProfile()?.level || 'beginner',
                personality: 'helpful_teacher'
            };

            const response = await this.makeAIRequest('/ai/conversation', requestData);
            
            if (response && response.response) {
                return response.response;
            } else {
                throw new Error('Invalid AI response format');
            }

        } catch (error) {
            Utils.log('Conversation generation error:', error);
            return this.generateFallbackResponse(userMessage, context);
        }
    }

    // Generate fallback response when AI is unavailable
    generateFallbackResponse(userMessage, context) {
        const topic = context?.topic;
        const userText = userMessage.toLowerCase();

        // Context-aware responses based on topic
        if (topic) {
            const topicResponses = this.getTopicBasedResponses(topic.id, userText);
            if (topicResponses.length > 0) {
                return topicResponses[Math.floor(Math.random() * topicResponses.length)];
            }
        }

        // General encouraging responses
        const generalResponses = [
            {
                english: "That's a good try! Let me help you with that.",
                farsi: "تلاش خوبی بود! بگذارید در آن کمکتان کنم."
            },
            {
                english: "I understand what you're trying to say. Let's practise together.",
                farsi: "متوجه می‌شوم که چه می‌خواهید بگویید. بیایید با هم تمرین کنیم."
            },
            {
                english: "Great effort! Keep practising and you'll improve quickly.",
                farsi: "تلاش عالی! به تمرین ادامه دهید و سریع پیشرفت خواهید کرد."
            }
        ];

        return generalResponses[Math.floor(Math.random() * generalResponses.length)];
    }

    // Generate topic-specific responses
    getTopicBasedResponses(topicId, userText) {
        const topicResponses = {
            greetings: [
                {
                    english: "Hello! It's wonderful to practise greetings. How are you feeling today?",
                    farsi: "سلام! تمرین احوالپرسی فوق‌العاده است. امروز چطور احساس می‌کنید؟"
                },
                {
                    english: "Nice to meet you! Let's practise some common greeting phrases.",
                    farsi: "خوشحالم که شما را ملاقات کردم! بیایید چند عبارت متداول احوالپرسی تمرین کنیم."
                }
            ],
            family: [
                {
                    english: "Family is so important! Tell me about your family members.",
                    farsi: "خانواده خیلی مهم است! در مورد اعضای خانواده‌تان بگویید."
                },
                {
                    english: "Let's talk about family relationships. Do you have any siblings?",
                    farsi: "بیایید در مورد روابط خانوادگی صحبت کنیم. آیا خواهر یا برادر دارید؟"
                }
            ],
            food: [
                {
                    english: "Food is a great topic to learn! What's your favorite dish?",
                    farsi: "غذا موضوع عالی برای یادگیری است! غذای مورد علاقه‌تان چیست؟"
                }
            ]
        };

        return topicResponses[topicId] || [];
    }

    // Check grammar and provide corrections
    async checkGrammar(text) {
        if (!this.isAvailable || this.isBlocked()) {
            return this.generateFallbackGrammarCheck(text);
        }

        try {
            const requestData = {
                text: text,
                user_level: storage.getUserProfile()?.level || 'beginner'
            };

            const response = await this.makeAIRequest('/ai/grammar-check', requestData);
            
            if (response && response.corrections) {
                return response;
            } else {
                throw new Error('Invalid grammar check response');
            }

        } catch (error) {
            Utils.log('Grammar check error:', error);
            return this.generateFallbackGrammarCheck(text);
        }
    }

    // Generate fallback grammar feedback
    generateFallbackGrammarCheck(text) {
        // Simple grammar patterns to check
        const patterns = [
            {
                regex: /\bi\s/gi,
                replacement: 'I ',
                message: 'Remember to capitalize "I"'
            },
            {
                regex: /\?\s*[a-z]/g,
                replacement: (match) => match.toUpperCase(),
                message: 'Start new sentences with capital letters'
            }
        ];

        const corrections = [];
        let correctedText = text;

        patterns.forEach(pattern => {
            if (pattern.regex.test(text)) {
                correctedText = correctedText.replace(pattern.regex, pattern.replacement);
                corrections.push({
                    type: 'grammar',
                    message: pattern.message,
                    original: text,
                    corrected: correctedText
                });
            }
        });

        return {
            has_errors: corrections.length > 0,
            corrections: corrections,
            corrected_text: correctedText,
            score: corrections.length === 0 ? 100 : Math.max(50, 100 - (corrections.length * 20))
        };
    }

    // Generate image for topic visualisation
    async generateTopicImage(topicId, prompt) {
        if (!this.isAvailable || this.isBlocked() || this.modelStatus.image !== 'available') {
            return this.getFallbackImage(topicId);
        }

        try {
            const requestData = {
                topic_id: topicId,
                prompt: prompt,
                style: 'educational',
                safe_mode: true
            };

            const response = await this.makeAIRequest('/ai/generate-image', requestData);
            
            if (response && response.image_url) {
                return {
                    success: true,
                    image_url: response.image_url,
                    alt_text: response.alt_text || prompt
                };
            } else {
                throw new Error('Invalid image generation response');
            }

        } catch (error) {
            Utils.log('Image generation error:', error);
            return this.getFallbackImage(topicId);
        }
    }

    // Get fallback image for topics
    getFallbackImage(topicId) {
        const fallbackImages = {
            greetings: {
                url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="50" font-size="40">👋</text></svg>',
                alt_text: 'Greeting hand wave'
            },
            family: {
                url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="50" font-size="40">👨‍👩‍👧‍👦</text></svg>',
                alt_text: 'Family illustration'
            },
            food: {
                url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="50" font-size="40">🍽️</text></svg>',
                alt_text: 'Food and dining'
            }
        };

        const fallback = fallbackImages[topicId] || {
            url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="50" font-size="40">📚</text></svg>',
            alt_text: 'Learning topic'
        };

        return {
            success: true,
            image_url: fallback.url,
            alt_text: fallback.alt_text,
            is_fallback: true
        };
    }

    // Make a rate-limited AI request
    async makeAIRequest(endpoint, data) {
        return new Promise((resolve, reject) => {
            this.requestQueue.push({
                endpoint,
                data,
                resolve,
                reject,
                timestamp: Date.now()
            });

            this.processRequestQueue();
        });
    }

    // Process the request queue with rate limiting
    async processRequestQueue() {
        if (this.isProcessingQueue || this.requestQueue.length === 0) {
            return;
        }

        this.isProcessingQueue = true;

        while (this.requestQueue.length > 0 && !this.isBlocked()) {
            const request = this.requestQueue.shift();
            
            try {
                const response = await fetch(`${CONFIG.API_BASE_URL}${request.endpoint}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(request.data)
                });

                if (response.status === 429) {
                    // Rate limited
                    const retryAfter = response.headers.get('Retry-After');
                    if (retryAfter) {
                        this.rateLimitInfo.blocked_until = new Date(Date.now() + (parseInt(retryAfter) * 1000));
                    }
                    
                    // Put request back in queue
                    this.requestQueue.unshift(request);
                    break;
                }

                if (response.ok) {
                    const responseData = await response.json();
                    
                    // Update rate limit info from headers
                    this.updateRateLimitFromHeaders(response.headers);
                    
                    request.resolve(responseData);
                } else {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

            } catch (error) {
                Utils.log('AI request error:', error);
                request.reject(error);
            }

            // Add delay between requests to avoid hitting rate limits
            await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
        }

        this.isProcessingQueue = false;

        // If there are still requests and we're not blocked, try again later
        if (this.requestQueue.length > 0 && !this.isBlocked()) {
            setTimeout(() => this.processRequestQueue(), 5000);
        }
    }

    // Update rate limit info from response headers
    updateRateLimitFromHeaders(headers) {
        const remaining = headers.get('X-RateLimit-Remaining');
        const resetTime = headers.get('X-RateLimit-Reset');

        if (remaining !== null) {
            this.rateLimitInfo.requests_remaining = parseInt(remaining);
        }

        if (resetTime !== null) {
            this.rateLimitInfo.reset_time = new Date(parseInt(resetTime) * 1000);
        }
    }

    // Get AI service status for display
    getServiceStatus() {
        return {
            available: this.isAvailable,
            blocked: this.isBlocked(),
            models: this.modelStatus,
            rate_limit: this.rateLimitInfo,
            queue_length: this.requestQueue.length
        };
    }

    // Generate practice exercises for a topic
    async generatePracticeExercises(topicId, exerciseType = 'mixed') {
        const topic = CONFIG.TOPIC_DETAILS[topicId];
        if (!topic) return null;

        if (!this.isAvailable || this.isBlocked()) {
            return this.generateFallbackExercises(topicId, exerciseType);
        }

        try {
            const requestData = {
                topic_id: topicId,
                exercise_type: exerciseType, // mixed, vocabulary, grammar, conversation
                user_level: storage.getUserProfile()?.level || 'beginner',
                count: 5
            };

            const response = await this.makeAIRequest('/ai/generate-exercises', requestData);
            
            if (response && response.exercises) {
                return response.exercises;
            } else {
                throw new Error('Invalid exercises response');
            }

        } catch (error) {
            Utils.log('Exercise generation error:', error);
            return this.generateFallbackExercises(topicId, exerciseType);
        }
    }

    // Generate fallback exercises
    generateFallbackExercises(topicId, exerciseType) {
        const topic = CONFIG.TOPIC_DETAILS[topicId];
        if (!topic || !topic.key_phrases) return [];

        const exercises = [];
        const phrases = topic.key_phrases;

        // Generate different types of exercises
        if (exerciseType === 'vocabulary' || exerciseType === 'mixed') {
            // Translation exercises
            phrases.slice(0, 3).forEach((phrase, index) => {
                exercises.push({
                    id: `vocab_${topicId}_${index}`,
                    type: 'translation',
                    question: `Translate to English: ${phrase.farsi}`,
                    answer: phrase.english,
                    options: this.generateTranslationOptions(phrase.english, phrases),
                    difficulty: phrase.difficulty || 'beginner'
                });
            });
        }

        if (exerciseType === 'grammar' || exerciseType === 'mixed') {
            // Fill in the blank exercises
            phrases.slice(0, 2).forEach((phrase, index) => {
                const words = phrase.english.split(' ');
                if (words.length > 2) {
                    const blankIndex = Math.floor(words.length / 2);
                    const question = words.map((word, i) => i === blankIndex ? '_____' : word).join(' ');
                    
                    exercises.push({
                        id: `grammar_${topicId}_${index}`,
                        type: 'fill_blank',
                        question: `Fill in the blank: ${question}`,
                        answer: words[blankIndex],
                        options: this.generateWordOptions(words[blankIndex]),
                        difficulty: phrase.difficulty || 'beginner'
                    });
                }
            });
        }

        return exercises;
    }

    // Generate translation options for multiple choice
    generateTranslationOptions(correct, allPhrases) {
        const options = [correct];
        const otherPhrases = allPhrases.filter(p => p.english !== correct);
        
        while (options.length < 4 && otherPhrases.length > 0) {
            const randomIndex = Math.floor(Math.random() * otherPhrases.length);
            const randomPhrase = otherPhrases.splice(randomIndex, 1)[0];
            options.push(randomPhrase.english);
        }

        // Shuffle options
        return options.sort(() => Math.random() - 0.5);
    }

    // Generate word options for fill-in-the-blank
    generateWordOptions(correct) {
        const commonWords = ['the', 'and', 'is', 'are', 'have', 'do', 'will', 'can'];
        const options = [correct];
        
        while (options.length < 4 && commonWords.length > 0) {
            const randomIndex = Math.floor(Math.random() * commonWords.length);
            const randomWord = commonWords[randomIndex];
            if (!options.includes(randomWord)) {
                options.push(randomWord);
            }
        }

        return options.sort(() => Math.random() - 0.5);
    }

    // Clear request queue (for cleanup)
    clearRequestQueue() {
        this.requestQueue.forEach(request => {
            request.reject(new Error('Request cancelled'));
        });
        this.requestQueue = [];
        this.isProcessingQueue = false;
    }

    // Update service status display in UI (if status element exists)
    updateStatusDisplay() {
        const statusElement = document.getElementById('aiServiceStatus');
        if (!statusElement) return;

        const status = this.getServiceStatus();
        const statusClass = status.available ? (status.blocked ? 'warning' : 'success') : 'error';
        const statusText = status.available ? (status.blocked ? 'Rate Limited' : 'Available') : 'Unavailable';

        statusElement.className = `ai-status ${statusClass}`;
        statusElement.textContent = `AI: ${statusText}`;
        
        if (status.queue_length > 0) {
            statusElement.textContent += ` (${status.queue_length} queued)`;
        }
    }
}
