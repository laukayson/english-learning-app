// Enhanced Voice Manager with Web-based STT Support
// Supports both browser SpeechRecognition and Google Translate STT

class EnhancedVoiceManager extends VoiceManager {
    constructor() {
        super();
        
        // Web STT service status
        this.webSTTAvailable = false;
        this.webSTTInitialized = false;
        this.preferWebSTT = true; // Prefer unlimited web STT over browser API
        
        // STT service modes
        this.STT_MODES = {
            BROWSER: 'browser',
            WEB_SERVICE: 'web_service'
        };
        
        this.currentSTTMode = this.STT_MODES.BROWSER;
    }

    async initialise() {
        await super.initialise();
        
        // Check web STT service availability
        await this.checkWebSTTService();
        
        Utils.log('Enhanced Voice Manager initialized', {
            browserRecognition: this.isSupported.recognition,
            webSTTAvailable: this.webSTTAvailable,
            preferredMode: this.currentSTTMode
        });
    }

    async checkWebSTTService() {
        try {
            const response = await fetch(`${CONFIG.API.BASE_URL}${CONFIG.API.ENDPOINTS.STT_STATUS}`);
            const status = await response.json();
            
            this.webSTTAvailable = status.ready;
            
            if (this.webSTTAvailable && this.preferWebSTT) {
                this.currentSTTMode = this.STT_MODES.WEB_SERVICE;
                Utils.log('Web STT service is available and preferred');
            } else {
                this.currentSTTMode = this.STT_MODES.BROWSER;
                Utils.log('Using browser STT');
            }
            
            return this.webSTTAvailable;
            
        } catch (error) {
            Utils.logError('Failed to check web STT service', error);
            this.webSTTAvailable = false;
            this.currentSTTMode = this.STT_MODES.BROWSER;
            return false;
        }
    }

    async initializeWebSTT() {
        if (this.webSTTInitialized) {
            return true;
        }

        try {
            Utils.log('Initializing web STT service...');
            
            const response = await fetch(`${CONFIG.API.BASE_URL}${CONFIG.API.ENDPOINTS.STT_INITIALIZE}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    headless: true
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.webSTTInitialized = true;
                this.webSTTAvailable = true;
                Utils.log('Web STT service initialized successfully');
                return true;
            } else {
                Utils.logError('Failed to initialize web STT service', result);
                return false;
            }
            
        } catch (error) {
            Utils.logError('Error initializing web STT service', error);
            return false;
        }
    }

    async cleanupWebSTT() {
        if (!this.webSTTInitialized) {
            return;
        }

        try {
            await fetch(`${CONFIG.API.BASE_URL}${CONFIG.API.ENDPOINTS.STT_CLEANUP}`, {
                method: 'POST'
            });
            
            this.webSTTInitialized = false;
            Utils.log('Web STT service cleaned up');
            
        } catch (error) {
            Utils.logError('Error cleaning up web STT service', error);
        }
    }

    // Enhanced speech recognition that uses web STT when available
    async startEnhancedListening(language = 'en', timeout = 10) {
        // Determine which STT method to use
        if (this.currentSTTMode === this.STT_MODES.WEB_SERVICE && this.webSTTAvailable) {
            return await this.startWebSTTListening(language, timeout);
        } else {
            return this.startBrowserListening(language);
        }
    }

    async startWebSTTListening(language = 'en', timeout = 10) {
        try {
            // Initialize web STT service if needed
            if (!this.webSTTInitialized) {
                const initSuccess = await this.initializeWebSTT();
                if (!initSuccess) {
                    throw new Error('Failed to initialize web STT service');
                }
            }

            Utils.log('Starting web-based speech recognition...');
            
            if (this.onStart) this.onStart();

            const response = await fetch(`${CONFIG.API.BASE_URL}${CONFIG.API.ENDPOINTS.STT}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({
                    action: 'microphone',
                    language: language,
                    timeout: timeout.toString()
                })
            });

            const result = await response.json();

            if (result.success && result.text) {
                Utils.log('Web STT result:', result);
                
                if (this.onResult) {
                    this.onResult({
                        transcript: result.text,
                        confidence: result.confidence || 0.9,
                        isFinal: true,
                        source: 'web_stt'
                    });
                }
                
                if (this.onEnd) this.onEnd();
                
                return {
                    success: true,
                    transcript: result.text,
                    confidence: result.confidence || 0.9,
                    source: 'web_stt'
                };
                
            } else {
                throw new Error(result.message || 'No speech detected');
            }

        } catch (error) {
            Utils.logError('Web STT error:', error);
            
            if (this.onError) {
                this.onError(error.message || 'Web STT failed');
            }
            
            // Fallback to browser STT if web STT fails
            Utils.log('Falling back to browser STT...');
            return this.startBrowserListening(language);
        }
    }

    startBrowserListening(language = 'en-US') {
        // Use the original browser-based speech recognition
        return this.startListening(language);
    }

    // Enhanced method that shows STT options to user
    async showSTTOptions() {
        const modal = document.createElement('div');
        modal.className = 'stt-options-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>Choose Speech Recognition Method</h3>
                <div class="stt-options">
                    ${this.webSTTAvailable ? `
                        <button class="stt-option web-stt" data-mode="web">
                            <div class="option-icon">🌐</div>
                            <div class="option-title">Web-based STT</div>
                            <div class="option-desc">Unlimited, high accuracy (Google Translate)</div>
                            <div class="option-pros">✅ No limits ✅ High accuracy</div>
                        </button>
                    ` : ''}
                    
                    ${this.isSupported.recognition ? `
                        <button class="stt-option browser-stt" data-mode="browser">
                            <div class="option-icon">🎤</div>
                            <div class="option-title">Browser STT</div>
                            <div class="option-desc">Built-in browser speech recognition</div>
                            <div class="option-pros">✅ Fast ✅ No setup required</div>
                        </button>
                    ` : ''}
                </div>
                <button class="close-modal">Cancel</button>
            </div>
        `;

        document.body.appendChild(modal);

        return new Promise((resolve) => {
            modal.querySelector('.close-modal').onclick = () => {
                document.body.removeChild(modal);
                resolve(null);
            };

            modal.querySelectorAll('.stt-option').forEach(button => {
                button.onclick = () => {
                    const mode = button.dataset.mode;
                    document.body.removeChild(modal);
                    resolve(mode);
                };
            });
        });
    }

    // Get STT service status for display
    getSTTStatus() {
        return {
            browserSupported: this.isSupported.recognition,
            webSTTAvailable: this.webSTTAvailable,
            webSTTInitialized: this.webSTTInitialized,
            currentMode: this.currentSTTMode,
            recommendation: this.webSTTAvailable ? 'web_service' : 'browser'
        };
    }

    // Switch STT mode
    async switchSTTMode(mode) {
        if (mode === this.STT_MODES.WEB_SERVICE && this.webSTTAvailable) {
            this.currentSTTMode = this.STT_MODES.WEB_SERVICE;
            Utils.log('Switched to web STT mode');
        } else if (mode === this.STT_MODES.BROWSER && this.isSupported.recognition) {
            this.currentSTTMode = this.STT_MODES.BROWSER;
            Utils.log('Switched to browser STT mode');
        } else {
            Utils.logError('Cannot switch to unavailable STT mode:', mode);
            return false;
        }
        return true;
    }

    // Override cleanup to include web STT cleanup
    async cleanup() {
        await this.cleanupWebSTT();
        // Call parent cleanup if it exists
        if (super.cleanup) {
            super.cleanup();
        }
    }
}

// Replace the global voice manager with enhanced version
if (typeof window !== 'undefined') {
    window.VoiceManager = EnhancedVoiceManager;
}
