// Voice Manager for Language Learning App

class VoiceManager {
    constructor() {
        this.isSupported = {
            recognition: Utils.supportsSpeechRecognition(),
            synthesis: Utils.supportsSpeechSynthesis()
        };
        
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isListening = false;
        this.isVoiceModeActive = false;
        this.currentLanguage = 'en-US';
        
        this.voices = {
            en: null,
            fa: null
        };
        
        this.settings = {
            rate: 0.9,
            pitch: 1.0,
            volume: 1.0
        };
        
        this.onResult = null;
        this.onError = null;
        this.onStart = null;
        this.onEnd = null;
    }

    async initialise() {
        try {
            Utils.log('Initialising Voice Manager...');
            
            if (this.isSupported.recognition) {
                this.setupSpeechRecognition();
            }
            
            if (this.isSupported.synthesis) {
                await this.setupSpeechSynthesis();
            }
            
            Utils.log('Voice Manager initialised', this.isSupported);
            
        } catch (error) {
            Utils.logError('Voice Manager initialisation failed', error);
        }
    }

    setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            Utils.log('Speech recognition not supported');
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = this.currentLanguage;
        this.recognition.maxAlternatives = 1;

        this.recognition.onstart = () => {
            this.isListening = true;
            Utils.log('Speech recognition started');
            if (this.onStart) this.onStart();
        };

        this.recognition.onresult = (event) => {
            const result = event.results[0][0];
            const transcript = result.transcript;
            const confidence = result.confidence;
            
            Utils.log('Speech recognition result:', { transcript, confidence });
            
            if (this.onResult) {
                this.onResult({
                    transcript,
                    confidence,
                    isFinal: event.results[0].isFinal
                });
            }
        };

        this.recognition.onerror = (event) => {
            Utils.logError('Speech recognition error:', event.error);
            this.isListening = false;
            
            if (this.onError) {
                this.onError(event.error);
            }
        };

        this.recognition.onend = () => {
            this.isListening = false;
            Utils.log('Speech recognition ended');
            if (this.onEnd) this.onEnd();
        };
    }

    async setupSpeechSynthesis() {
        if (!this.synthesis) {
            Utils.log('Speech synthesis not supported');
            return;
        }

        // Wait for voices to load
        return new Promise((resolve) => {
            const loadVoices = () => {
                const voices = this.synthesis.getVoices();
                
                // Find best English voice
                this.voices.en = voices.find(voice => 
                    voice.lang.startsWith('en') && voice.name.includes('Google')
                ) || voices.find(voice => 
                    voice.lang.startsWith('en')
                ) || voices[0];

                // Find best Farsi/Persian voice (if available)
                this.voices.fa = voices.find(voice => 
                    voice.lang.startsWith('fa') || voice.lang.includes('persian')
                ) || this.voices.en; // Fallback to English

                Utils.log('Voices loaded:', {
                    english: this.voices.en?.name,
                    farsi: this.voices.fa?.name,
                    total: voices.length
                });

                resolve();
            };

            if (this.synthesis.getVoices().length > 0) {
                loadVoices();
            } else {
                this.synthesis.onvoiceschanged = loadVoices;
            }
        });
    }

    startListening(language = 'en-US') {
        if (!this.isSupported.recognition || !this.recognition) {
            Utils.showNotification('Speech recognition not supported in your browser', 'error');
            return false;
        }

        if (this.isListening) {
            this.stopListening();
            return false;
        }

        try {
            this.currentLanguage = language;
            this.recognition.lang = language;
            this.recognition.start();
            return true;
        } catch (error) {
            Utils.logError('Failed to start listening:', error);
            Utils.showNotification('Failed to start voice recognition', 'error');
            return false;
        }
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }

    speak(text, language = 'en', options = {}) {
        if (!this.isSupported.synthesis || !this.synthesis) {
            Utils.logError('Speech synthesis not supported');
            return false;
        }

        if (!text || text.trim() === '') {
            Utils.logError('No text provided for speech synthesis');
            return false;
        }

        try {
            // Cancel any ongoing speech
            this.synthesis.cancel();
            
            // Add a small delay to ensure cancel completes
            setTimeout(() => {
                const utterance = new SpeechSynthesisUtterance(text);
                
                // Set voice based on language
                if (language === 'fa' && this.voices.fa) {
                    utterance.voice = this.voices.fa;
                } else if (this.voices.en) {
                    utterance.voice = this.voices.en;
                }

                // Apply settings
                utterance.rate = options.rate || this.settings.rate;
                utterance.pitch = options.pitch || this.settings.pitch;
                utterance.volume = options.volume || this.settings.volume;

                // Event handlers
                utterance.onstart = () => {
                    Utils.log('Speech synthesis started:', text);
                    if (this.onStart) this.onStart();
                };

                utterance.onend = () => {
                    Utils.log('Speech synthesis ended');
                    // Call the callback after speech truly ends
                    if (this.onEnd) {
                        // Small delay to ensure proper cleanup
                        setTimeout(() => {
                            this.onEnd();
                        }, 100);
                    }
                };

                utterance.onerror = (event) => {
                    Utils.logError('Speech synthesis error:', event.error);
                    if (this.onError) this.onError(event.error);
                };

                // Store the current utterance for tracking
                this.currentUtterance = utterance;
                this.synthesis.speak(utterance);
            }, 100);
            
            return true;

        } catch (error) {
            Utils.logError('Failed to speak:', error);
            if (this.onError) this.onError(error);
            return false;
        }
    }

    stopSpeaking() {
        if (this.isSupported.synthesis && this.synthesis) {
            this.synthesis.cancel();
            // Clear current utterance tracking
            this.currentUtterance = null;
            Utils.log('Speech synthesis stopped');
            return true;
        }
        return false;
    }

    isSpeaking() {
        return this.isSupported.synthesis && this.synthesis && this.synthesis.speaking;
    }

    speakEnglish(text, options = {}) {
        return this.speak(text, 'en', options);
    }

    speakFarsi(text, options = {}) {
        return this.speak(text, 'fa', {
            ...options,
            rate: 0.8 // Slower rate for Farsi
        });
    }

    toggleVoiceMode() {
        this.isVoiceModeActive = !this.isVoiceModeActive;
        
        const voiceToggle = document.getElementById('voice-toggle');
        if (voiceToggle) {
            voiceToggle.textContent = this.isVoiceModeActive ? '🔊' : '🎤';
            voiceToggle.title = this.isVoiceModeActive ? 'Voice Mode On' : 'Voice Mode Off';
        }

        Utils.showNotification(
            this.isVoiceModeActive ? 'Voice mode enabled' : 'Voice mode disabled',
            'info'
        );

        return this.isVoiceModeActive;
    }

    setCallbacks(callbacks) {
        this.onResult = callbacks.onResult || null;
        this.onError = callbacks.onError || null;
        this.onStart = callbacks.onStart || null;
        this.onEnd = callbacks.onEnd || null;
    }

    // Advanced pronunciation checking
    async checkPronunciation(expectedText, recordingDuration = 5000) {
        return new Promise((resolve) => {
            if (!this.isSupported.recognition) {
                resolve({
                    success: false,
                    error: 'Speech recognition not supported'
                });
                return;
            }

            let hasResult = false;
            const originalCallbacks = {
                onResult: this.onResult,
                onError: this.onError,
                onEnd: this.onEnd
            };

            // Set temporary callbacks
            this.setCallbacks({
                onResult: (result) => {
                    if (hasResult) return;
                    hasResult = true;

                    const score = this.calculatePronunciationScore(
                        result.transcript,
                        expectedText,
                        result.confidence
                    );

                    resolve({
                        success: true,
                        transcript: result.transcript,
                        expected: expectedText,
                        score: score.overall,
                        feedback: score.feedback,
                        suggestions: score.suggestions
                    });

                    // Restore original callbacks
                    this.setCallbacks(originalCallbacks);
                },
                onError: (error) => {
                    resolve({
                        success: false,
                        error: error
                    });
                    this.setCallbacks(originalCallbacks);
                },
                onEnd: () => {
                    if (!hasResult) {
                        resolve({
                            success: false,
                            error: 'No speech detected'
                        });
                    }
                    this.setCallbacks(originalCallbacks);
                }
            });

            // Start listening
            if (!this.startListening()) {
                resolve({
                    success: false,
                    error: 'Failed to start listening'
                });
                return;
            }

            // Auto-stop after specified duration
            setTimeout(() => {
                if (this.isListening && !hasResult) {
                    this.stopListening();
                }
            }, recordingDuration);
        });
    }

    calculatePronunciationScore(transcript, expected, confidence) {
        const transcriptLower = transcript.toLowerCase().trim();
        const expectedLower = expected.toLowerCase().trim();

        // Calculate word-level accuracy
        const transcriptWords = transcriptLower.split(/\s+/);
        const expectedWords = expectedLower.split(/\s+/);

        let correctWords = 0;
        let totalWords = expectedWords.length;

        expectedWords.forEach(word => {
            if (transcriptWords.includes(word)) {
                correctWords++;
            }
        });

        const wordAccuracy = totalWords > 0 ? correctWords / totalWords : 0;

        // Calculate string similarity
        const similarity = this.calculateStringSimilarity(transcriptLower, expectedLower);

        // Combine scores
        const overallScore = (wordAccuracy * 0.4 + similarity * 0.4 + confidence * 0.2);

        // Generate feedback
        let feedback, suggestions = [];

        if (overallScore >= 0.9) {
            feedback = 'Excellent pronunciation! 🌟';
        } else if (overallScore >= 0.7) {
            feedback = 'Very good! 👍';
            suggestions.push('Keep practicing to perfect your pronunciation');
        } else if (overallScore >= 0.5) {
            feedback = 'Good effort! 📈';
            suggestions.push('Try speaking more slowly and clearly');
            suggestions.push('Practice the words that were missed');
        } else {
            feedback = 'Keep practicing! 💪';
            suggestions.push('Speak slowly and clearly');
            suggestions.push('Listen to the pronunciation and repeat');
            suggestions.push('Practice individual words first');
        }

        // Add specific suggestions based on differences
        const missingWords = expectedWords.filter(word => !transcriptWords.includes(word));
        if (missingWords.length > 0) {
            suggestions.push(`Focus on pronouncing: ${missingWords.join(', ')}`);
        }

        return {
            overall: Math.round(overallScore * 100),
            wordAccuracy: Math.round(wordAccuracy * 100),
            similarity: Math.round(similarity * 100),
            confidence: Math.round(confidence * 100),
            feedback,
            suggestions
        };
    }

    calculateStringSimilarity(str1, str2) {
        const longer = str1.length > str2.length ? str1 : str2;
        const shorter = str1.length > str2.length ? str2 : str1;
        
        if (longer.length === 0) return 1.0;
        
        const editDistance = this.levenshteinDistance(longer, shorter);
        return (longer.length - editDistance) / longer.length;
    }

    levenshteinDistance(str1, str2) {
        const matrix = [];

        for (let i = 0; i <= str2.length; i++) {
            matrix[i] = [i];
        }

        for (let j = 0; j <= str1.length; j++) {
            matrix[0][j] = j;
        }

        for (let i = 1; i <= str2.length; i++) {
            for (let j = 1; j <= str1.length; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }

        return matrix[str2.length][str1.length];
    }

    // Voice recording for pronunciation practice
    async recordVoice(duration = 5000) {
        return new Promise((resolve) => {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                resolve({
                    success: false,
                    error: 'Media recording not supported'
                });
                return;
            }

            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    const mediaRecorder = new MediaRecorder(stream);
                    const audioChunks = [];

                    mediaRecorder.ondataavailable = (event) => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        stream.getTracks().forEach(track => track.stop());
                        
                        resolve({
                            success: true,
                            audioBlob,
                            audioUrl: URL.createObjectURL(audioBlob)
                        });
                    };

                    mediaRecorder.start();

                    // Auto-stop after duration
                    setTimeout(() => {
                        if (mediaRecorder.state === 'recording') {
                            mediaRecorder.stop();
                        }
                    }, duration);
                })
                .catch(error => {
                    resolve({
                        success: false,
                        error: error.message
                    });
                });
        });
    }

    // Get available voices
    getAvailableVoices() {
        if (!this.isSupported.synthesis) return [];
        
        return this.synthesis.getVoices().map(voice => ({
            name: voice.name,
            lang: voice.lang,
            gender: voice.name.toLowerCase().includes('female') ? 'female' : 'male',
            isDefault: voice.default
        }));
    }

    // Update voice settings
    updateSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
        Utils.log('Voice settings updated:', this.settings);
    }

    // Check if voice features are available
    isVoiceAvailable() {
        return this.isSupported.recognition || this.isSupported.synthesis;
    }

    // Get voice capabilities
    getCapabilities() {
        return {
            recognition: this.isSupported.recognition,
            synthesis: this.isSupported.synthesis,
            recording: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
            voicesAvailable: this.getAvailableVoices().length,
            isVoiceModeActive: this.isVoiceModeActive
        };
    }
    
    // Recording methods for conversation input
    async startRecording(continuous = false) {
        return new Promise((resolve, reject) => {
            if (!this.isSupported.recognition || !this.recognition) {
                reject(new Error('Speech recognition not supported'));
                return;
            }

            if (this.isListening) {
                reject(new Error('Already recording'));
                return;
            }

            // Store the original event handlers
            const originalOnResult = this.onResult;
            const originalOnError = this.onError;
            const originalOnEnd = this.onEnd;

            // Set up temporary handlers for this recording session
            this.onResult = (data) => {
                // Restore original handlers
                this.onResult = originalOnResult;
                this.onError = originalOnError;
                this.onEnd = originalOnEnd;
                
                this.recordingResolved = true;
                resolve({
                    transcript: data.transcript.trim(),
                    confidence: data.confidence
                });
            };

            this.onError = (error) => {
                // Restore original handlers
                this.onResult = originalOnResult;
                this.onError = originalOnError;
                this.onEnd = originalOnEnd;
                
                this.recordingResolved = true;
                reject(new Error(`Speech recognition error: ${error}`));
            };

            this.onEnd = () => {
                // Only handle end if we haven't already resolved
                if (!this.recordingResolved) {
                    // Restore original handlers
                    this.onResult = originalOnResult;
                    this.onError = originalOnError;
                    this.onEnd = originalOnEnd;
                    
                    this.recordingResolved = true;
                    resolve({ transcript: '', confidence: 0 });
                }
            };

            try {
                this.recordingResolved = false;
                this.recognition.continuous = continuous;
                this.recognition.interimResults = continuous;
                this.recognition.start();
            } catch (error) {
                // Restore original handlers on error
                this.onResult = originalOnResult;
                this.onError = originalOnError;
                this.onEnd = originalOnEnd;
                reject(error);
            }
        });
    }
    
    // Test method to check if speech recognition is working
    async testSpeechRecognition() {
        if (!this.isSupported.recognition) {
            Utils.showNotification('Speech recognition is not supported in your browser. Please use Chrome or Edge.', 'error');
            return false;
        }
        
        if (!this.recognition) {
            Utils.showNotification('Speech recognition not initialised properly.', 'error');
            return false;
        }
        
        try {
            const result = await this.startRecording(false);
            return true;
        } catch (error) {
            if (error.message.includes('not-allowed')) {
                Utils.showNotification('Microphone permission denied. Please allow microphone access and try again.', 'error');
            } else if (error.message.includes('no-speech')) {
                Utils.showNotification('No speech detected. Please speak clearly and try again.', 'warning');
            } else {
                Utils.showNotification('Speech recognition test failed: ' + error.message, 'error');
            }
            return false;
        }
    }
    
    async stopRecording() {
        if (this.recognition && this.isListening) {
            this.recordingResolved = true;
            this.recognition.stop();
        }
        return Promise.resolve();
    }
}
