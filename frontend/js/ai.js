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
        // Return a simple error message when AI is unavailable
        return {
            english: "AI service is currently unavailable. Please try again later.",
            farsi: "سرویس هوش مصنوعی در حال حاضر در دسترس نیست. لطفاً بعداً دوباره امتحان کنید."
        };
    }

    // Generate topic-specific responses (removed - no fallback phrases)
    getTopicBasedResponses(topicId, userText) {
        return [];
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

    // Generate fallback grammar feedback (simplified - no fallback patterns)
    generateFallbackGrammarCheck(text) {
        return {
            has_errors: false,
            corrections: [],
            corrected_text: text,
            score: 0,
            message: "Grammar checking unavailable - AI service required"
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

    // Get fallback image for topics (simplified - basic placeholder only)
    getFallbackImage(topicId) {
        return {
            success: true,
            image_url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="50" font-size="20">No Image</text></svg>',
            alt_text: 'Image generation unavailable',
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

    // Generate fallback exercises (removed - requires AI service)
    generateFallbackExercises(topicId, exerciseType) {
        return [{
            id: `fallback_${topicId}`,
            type: 'message',
            question: 'Exercise generation requires AI service',
            answer: 'Please try again when AI service is available',
            options: [],
            difficulty: 'info'
        }];
    }

    // Generate translation options for multiple choice (removed - requires phrase data)
    generateTranslationOptions(correct, allPhrases) {
        return [correct];
    }

    // Generate word options for fill-in-the-blank (removed - requires AI service)
    generateWordOptions(correct) {
        return [correct];
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
