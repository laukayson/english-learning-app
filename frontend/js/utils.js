// Utility Functions for the Language Learning App

class Utils {
    // Rate limiting functionality
    static rateLimiter = {
        requests: new Map(),
        
        canMakeRequest(key = 'default') {
            const now = Date.now();
            const minute = Math.floor(now / 60000);
            const hour = Math.floor(now / 3600000);
            
            const minuteKey = `${key}_${minute}`;
            const hourKey = `${key}_${hour}`;
            
            const minuteCount = this.requests.get(minuteKey) || 0;
            const hourCount = this.requests.get(hourKey) || 0;
            
            if (minuteCount >= CONFIG.API.RATE_LIMIT.REQUESTS_PER_MINUTE ||
                hourCount >= CONFIG.API.RATE_LIMIT.REQUESTS_PER_HOUR) {
                return false;
            }
            
            this.requests.set(minuteKey, minuteCount + 1);
            this.requests.set(hourKey, hourCount + 1);
            
            // Clean old entries
            this.cleanOldEntries();
            
            return true;
        },
        
        cleanOldEntries() {
            const now = Date.now();
            const currentMinute = Math.floor(now / 60000);
            const currentHour = Math.floor(now / 3600000);
            
            for (const [key] of this.requests) {
                const parts = key.split('_');
                const timestamp = parseInt(parts[parts.length - 1]);
                
                if (key.includes('_') && 
                    ((currentMinute - timestamp > 5) || (currentHour - timestamp > 2))) {
                    this.requests.delete(key);
                }
            }
        }
    };

    // Date and time utilities
    static formatDate(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }).format(date);
    }

    static getTimeOfDay() {
        const hour = new Date().getHours();
        if (hour < 12) return 'morning';
        if (hour < 18) return 'afternoon';
        return 'evening';
    }

    static getDaysSince(date) {
        const now = new Date();
        const targetDate = new Date(date);
        const diffTime = Math.abs(now - targetDate);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }

    // String manipulation utilities
    static capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    static truncate(str, length = 50) {
        return str.length > length ? str.substring(0, length) + '...' : str;
    }

    static slugify(str) {
        return str
            .toLowerCase()
            .replace(/\s+/g, '_')
            .replace(/[^\w\-]+/g, '');
    }

    // Array utilities
    static shuffle(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }

    static getRandomItem(array) {
        return array[Math.floor(Math.random() * array.length)];
    }

    static chunk(array, size) {
        const chunks = [];
        for (let i = 0; i < array.length; i += size) {
            chunks.push(array.slice(i, i + size));
        }
        return chunks;
    }

    // API utilities
    static async fetchWithTimeout(url, options = {}) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), CONFIG.API.TIMEOUT);

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            clearTimeout(timeout);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return response;
        } catch (error) {
            clearTimeout(timeout);
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw error;
        }
    }

    static async makeAPIRequest(endpoint, options = {}) {
        const url = `${CONFIG.API.BASE_URL}${endpoint}`;
        
        // Check rate limiting
        if (!this.rateLimiter.canMakeRequest(endpoint)) {
            throw new Error(CONFIG.ERRORS.RATE_LIMIT);
        }

        try {
            const response = await this.fetchWithTimeout(url, options);
            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // DOM utilities
    static createElement(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else if (key.startsWith('data-')) {
                element.setAttribute(key, value);
            } else {
                element[key] = value;
            }
        });

        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else {
                element.appendChild(child);
            }
        });

        return element;
    }

    static show(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element) || document.querySelector(element);
        }
        if (element) {
            element.style.display = 'block';
            element.classList.add('active');
        }
    }

    static hide(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element) || document.querySelector(element);
        }
        if (element) {
            element.style.display = 'none';
            element.classList.remove('active');
        }
    }

    static toggle(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element) || document.querySelector(element);
        }
        if (element) {
            if (element.style.display === 'none' || !element.classList.contains('active')) {
                this.show(element);
            } else {
                this.hide(element);
            }
        }
    }

    // Animation utilities
    static async fadeIn(element, duration = CONFIG.UI.ANIMATION_DURATION) {
        return new Promise(resolve => {
            element.style.opacity = '0';
            element.style.display = 'block';
            
            const start = performance.now();
            
            function animate(currentTime) {
                const elapsed = currentTime - start;
                const progress = Math.min(elapsed / duration, 1);
                
                element.style.opacity = progress;
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    resolve();
                }
            }
            
            requestAnimationFrame(animate);
        });
    }

    static async fadeOut(element, duration = CONFIG.UI.ANIMATION_DURATION) {
        return new Promise(resolve => {
            const start = performance.now();
            const startOpacity = parseFloat(element.style.opacity) || 1;
            
            function animate(currentTime) {
                const elapsed = currentTime - start;
                const progress = Math.min(elapsed / duration, 1);
                
                element.style.opacity = startOpacity * (1 - progress);
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    element.style.display = 'none';
                    resolve();
                }
            }
            
            requestAnimationFrame(animate);
        });
    }

    // Screen management
    static showScreen(screenId) {
        // Hide all screens
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        
        // Show target screen
        const targetScreen = document.getElementById(screenId);
        if (targetScreen) {
            targetScreen.classList.add('active');
        }
    }

    // Local storage utilities with error handling
    static saveToStorage(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Failed to save to storage:', error);
            return false;
        }
    }

    static loadFromStorage(key, defaultValue = null) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : defaultValue;
        } catch (error) {
            console.error('Failed to load from storage:', error);
            return defaultValue;
        }
    }

    static removeFromStorage(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Failed to remove from storage:', error);
            return false;
        }
    }

    // Validation utilities
    static validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    static validateAge(age) {
        const numAge = parseInt(age);
        return !isNaN(numAge) && numAge >= 5 && numAge <= 100;
    }

    static validateLevel(level) {
        return ['1', '2', '3', '4'].includes(String(level));
    }

    // Text processing utilities
    static removeHtmlTags(str) {
        const div = document.createElement('div');
        div.innerHTML = str;
        return div.textContent || div.innerText || '';
    }

    static highlightText(text, searchTerm) {
        if (!searchTerm) return text;
        const regex = new RegExp(`(${searchTerm})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    // Progress calculation utilities
    static calculateProgress(completed, total) {
        if (total === 0) return 0;
        return Math.round((completed / total) * 100);
    }

    static getProgressColour(percentage) {
        if (percentage < 25) return '#ef4444'; // red
        if (percentage < 50) return '#f59e0b'; // yellow
        if (percentage < 75) return '#3b82f6'; // blue
        return '#10b981'; // green
    }

    // Device detection
    static isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    static isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }

    // Browser capability detection
    static supportsSpeechRecognition() {
        return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    }

    static supportsSpeechSynthesis() {
        return 'speechSynthesis' in window;
    }

    // Error handling utilities
    static handleError(error, context = 'Unknown') {
        console.error(`Error in ${context}:`, error);
        
        let message = CONFIG.ERRORS.GENERAL;
        
        if (error.message.includes('timeout')) {
            message = CONFIG.ERRORS.NETWORK;
        } else if (error.message.includes('rate limit')) {
            message = CONFIG.ERRORS.RATE_LIMIT;
        } else if (error.message.includes('microphone')) {
            message = CONFIG.ERRORS.MICROPHONE_ACCESS;
        }
        
        this.showNotification(message, 'error');
    }

    // Notification system
    static showNotification(message, type = 'info', duration = 5000) {
        const notification = this.createElement('div', {
            className: `notification notification-${type}`,
            innerHTML: message
        });

        document.body.appendChild(notification);

        // Auto remove
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, duration);

        return notification;
    }

    // Debugging utilities
    static log(message, data = null) {
        if (CONFIG.DEV.DEBUG) {
            if (data) {
                console.log(message, data);
            } else {
                console.log(message);
            }
        }
    }

    static logError(message, error = null) {
        if (CONFIG.DEV.DEBUG) {
            if (error) {
                console.error(message, error);
            } else {
                console.error(message);
            }
        }
    }

    // Performance monitoring
    static startTimer(label) {
        if (CONFIG.DEV.DEBUG) {
            console.time(label);
        }
    }

    static endTimer(label) {
        if (CONFIG.DEV.DEBUG) {
            console.timeEnd(label);
        }
    }
}

// Debounce function for input handling
Utils.debounce = function(func, wait, immediate = false) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
};

// Throttle function for event handling
Utils.throttle = function(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
}
