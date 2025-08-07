// Configuration for Render deployment
const RENDER_CONFIG = {
    // API Base URL - will be set automatically by Render
    API_BASE_URL: window.location.origin,
    
    // Features available on Render
    FEATURES: {
        voice_recognition: false,  // Disabled on Render
        text_to_speech: false,     // Disabled on Render
        browser_automation: false, // Disabled on Render
        ai_chat: true,            // Available
        translation: true,         // Available
        progress_tracking: true,   // Available
        user_management: true      // Available
    },
    
    // Platform identification
    PLATFORM: 'render',
    DATABASE: 'turso',
    
    // UI adjustments for Render
    UI_ADJUSTMENTS: {
        hide_voice_buttons: true,
        show_text_only_notice: true,
        disable_microphone_access: true
    },
    
    // Error messages for disabled features
    DISABLED_FEATURE_MESSAGES: {
        voice_recognition: 'Voice recognition is not available in this version. Please use text input.',
        text_to_speech: 'Text-to-speech is not available in this version.',
        microphone: 'Microphone features are disabled in this deployment.'
    }
};

// Feature detection and UI updates
document.addEventListener('DOMContentLoaded', function() {
    // Hide voice-related UI elements
    if (RENDER_CONFIG.UI_ADJUSTMENTS.hide_voice_buttons) {
        const voiceButtons = document.querySelectorAll('.voice-button, .mic-button, .stt-button');
        voiceButtons.forEach(button => {
            button.style.display = 'none';
        });
        
        // Add text-only notice
        if (RENDER_CONFIG.UI_ADJUSTMENTS.show_text_only_notice) {
            const notice = document.createElement('div');
            notice.className = 'platform-notice';
            notice.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    <strong>Text-Only Version:</strong> This deployment supports text-based chat only. 
                    Voice features are not available.
                </div>
            `;
            notice.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 1000;
                max-width: 300px;
                padding: 10px;
                background: #d1ecf1;
                border: 1px solid #bee5eb;
                border-radius: 5px;
                color: #0c5460;
                font-size: 12px;
            `;
            
            document.body.appendChild(notice);
            
            // Auto-hide after 10 seconds
            setTimeout(() => {
                notice.style.display = 'none';
            }, 10000);
        }
    }
});

// Override API endpoints for disabled features
const originalFetch = window.fetch;
window.fetch = function(url, options) {
    // Intercept voice-related API calls
    if (url.includes('/api/stt') || url.includes('/api/tts')) {
        return Promise.reject({
            error: 'Voice features disabled',
            message: RENDER_CONFIG.DISABLED_FEATURE_MESSAGES.voice_recognition
        });
    }
    
    // Call original fetch for other requests
    return originalFetch.apply(this, arguments);
};

// Export for use in other scripts
window.RENDER_CONFIG = RENDER_CONFIG;
