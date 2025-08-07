/**
 * ConversationManager - Handles conversation interface and chat functionality
 */
class ConversationManager {
    constructor(user, voiceManager) {
        this.user = user;
        this.voiceManager = voiceManager;
        this.currentTopic = null;
        this.messages = [];
        this.isListening = false;
        this.isTutorTyping = false; // Track if tutor is typing
        this.tutorHasGreeted = false; // Track if tutor has sent welcome message
        this.currentSpeakingElement = null; // Track which message is being read
        this.conversationStartTime = null; // Track conversation start time
        this.conversationComplete = false; // Track if conversation is complete
        this.messageCount = 0; // Track number of messages for completion
        
        this.initializeEventListeners();
    }

    removeConflictingListeners() {
        // Remove any existing click listeners on the back button
        const backBtn = document.getElementById('back-to-dashboard');
        if (backBtn) {
            // Clone the button to remove all event listeners
            const newBackBtn = backBtn.cloneNode(true);
            backBtn.parentNode.replaceChild(newBackBtn, backBtn);
        }
    }

    initializeEventListeners() {
        // Remove any existing event listeners from app.js to prevent conflicts
        this.removeConflictingListeners();
        
        // Send button
        const sendBtn = document.getElementById('send-btn');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }

        // Enter key in input
        const userInput = document.getElementById('user-input');
        if (userInput) {
            userInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !this.isTutorTyping && this.tutorHasGreeted) {
                    this.sendMessage();
                }
            });
        }

        // Voice button
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.addEventListener('mousedown', () => this.startVoiceInput());
            voiceBtn.addEventListener('mouseup', () => this.stopVoiceInput());
            voiceBtn.addEventListener('mouseleave', () => this.stopVoiceInput());
        }

        // Voice input button (alternative)
        const voiceInputBtn = document.getElementById('voice-input-btn');
        if (voiceInputBtn) {
            voiceInputBtn.addEventListener('click', () => this.toggleVoiceInput());
        }

        // Back button
        const backBtn = document.getElementById('back-to-dashboard');
        if (backBtn) {
            backBtn.addEventListener('click', () => this.handleBackToDashboard());
        }
    }

    async startConversation(topicId) {
        this.currentTopic = topicId;
        this.conversationStartTime = Date.now();
        this.conversationComplete = false;
        this.tutorHasGreeted = false; // Reset greeting flag
        this.messageCount = 0;
        this.loadTopicData(topicId);
        this.clearMessages();
        
        // Disable input until tutor greets
        this.setInputDisabled(true, "Waiting for tutor to start...");
        
        // Initialize AI context for this topic (silently)
        await this.initializeTopicContext(topicId);
        
        this.showWelcomeMessage();
    }

    async initializeTopicContext(topicId) {
        /**
         * Send context to AI when topic is chosen (without showing AI response to user)
         * This will also open the browser window if in visible mode
         */
        try {
            console.log('🚀 Initializing AI context for topic:', topicId);
            console.log('⏳ Opening browser window (if in visible mode)...');
            
            const response = await fetch(`${CONFIG.BACKEND_URL}/api/chat/init-topic`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    topic: topicId,
                    user_id: this.user ? this.user.id : null,
                    user_level: this.user ? this.user.level : 'beginner'
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Topic context initialized:', data);
                console.log('🌐 Browser window should now be open and ready for conversation');
                return true;
            } else {
                console.warn('⚠️ Failed to initialize topic context, but continuing...');
                return false;
            }
        } catch (error) {
            console.warn('⚠️ Error initializing topic context:', error);
            // Don't fail the conversation start if context initialization fails
            return false;
        }
    }

    loadTopicData(topicId) {
        // Update conversation header with topic information
        const topicTitle = document.getElementById('conversation-topic-title');
        if (topicTitle) {
            const topicName = this.getTopicName(topicId);
            topicTitle.textContent = topicName;
        }
    }

    getTopicName(topicId) {
        // Use the comprehensive topic details from CONFIG
        if (CONFIG.TOPIC_DETAILS[topicId]) {
            const topic = CONFIG.TOPIC_DETAILS[topicId];
            return topic.name; // Remove emoji from title
        }
        return 'AI Conversation';
    }

    clearMessages() {
        const messagesContainer = document.getElementById('messages-container');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
        this.messages = [];
    }

    showWelcomeMessage() {
        const topicName = this.getTopicName(this.currentTopic);
        const welcomeMessage = `Welcome to ${topicName}! Start practicing by typing a message or holding the 🎤 button to speak.`;
        this.addMessage('ai', welcomeMessage);
        
        // Enable input after tutor has greeted
        this.tutorHasGreeted = true;
        this.setInputDisabled(false);
    }

    async sendMessage() {
        // Prevent sending if tutor is typing or hasn't greeted yet
        if (this.isTutorTyping || !this.tutorHasGreeted) {
            return;
        }

        const userInput = document.getElementById('user-input');
        if (!userInput) return;

        const message = userInput.value.trim();
        if (!message) return;

        // Clear input
        userInput.value = '';

        // Add user message to chat
        this.addMessage('user', message);
        this.messageCount++;

        // Show typing indicator and set typing state
        this.showTypingIndicator();
        this.setInputDisabled(true);

        try {
            // Send message to backend
            const response = await this.sendToBackend(message);
            
            // Remove typing indicator
            this.removeTypingIndicator();
            this.setInputDisabled(false);

            // Add AI response
            if (response && response.ai_response) {
                this.addMessage('ai', response.ai_response, response.farsi_translation);
                
                // Check if lesson is complete
                if (response.ai_response.includes('LESSON_COMPLETE')) {
                    this.conversationComplete = true;
                    this.showCompletionMessage();
                }
                
                // Play AI response if voice is enabled
                if (this.voiceManager && response.audio) {
                    this.voiceManager.playAudio(response.audio);
                }
            } else {
                this.addMessage('ai', "I'm sorry, I couldn't process that. Please try again.");
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator();
            this.setInputDisabled(false);
            
            // Provide more specific error messages
            if (error.message.includes('Failed to fetch')) {
                this.addMessage('ai', "❌ Cannot connect to the AI service. Please make sure the backend server is running.");
            } else if (error.message.includes('HTTP error! status: 500')) {
                this.addMessage('ai', "⚠️ Server error occurred. Please try again later.");
            } else {
                this.addMessage('ai', "❌ Connection error. Please check your internet connection and try again.");
            }
        }
    }

    async sendToBackend(message) {
        const conversationDuration = Date.now() - this.conversationStartTime;
        const minutes = Math.floor(conversationDuration / 60000);
        
        const response = await fetch(`${CONFIG.BACKEND_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                user_id: this.user ? this.user.id : null,
                topic: this.currentTopic,
                history: this.messages.slice(-10).map(msg => ({
                    role: msg.sender === 'user' ? 'user' : 'assistant',
                    content: msg.text
                })),
                conversation_context: {
                    message_count: this.messageCount,
                    duration_minutes: minutes,
                    is_complete: this.conversationComplete,
                    instruction: "Please evaluate the learner's progress in this topic conversation. Consider the quality of their responses, variety of vocabulary used, grammar improvements, and overall engagement. When you determine they have had sufficient meaningful practice for this topic (typically after substantial back-and-forth conversation showing learning progress), indicate completion by including 'LESSON_COMPLETE' in your response. Focus on learning quality rather than time duration."
                }
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    addMessage(sender, text, farsiTranslation = null) {
        const messagesContainer = document.getElementById('messages-container');
        if (!messagesContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = text;
        
        // Add action buttons for messages
        const actionsContainer = document.createElement('div');
        actionsContainer.className = 'message-actions';
        
        // Text-to-speech button
        const speakBtn = document.createElement('button');
        speakBtn.className = 'action-btn speak-btn';
        speakBtn.innerHTML = '🔊';
        speakBtn.title = 'Read aloud';
        speakBtn.addEventListener('click', () => this.handleSpeakClick(messageElement, text, sender, speakBtn));
        
        // Translation button
        const translateBtn = document.createElement('button');
        translateBtn.className = 'action-btn translate-btn';
        translateBtn.innerHTML = '🔄';
        translateBtn.title = 'Translate to Farsi';
        translateBtn.addEventListener('click', () => this.showTranslation(messageElement, text, farsiTranslation));
        
        actionsContainer.appendChild(speakBtn);
        actionsContainer.appendChild(translateBtn);
        
        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        messageElement.appendChild(messageContent);
        messageElement.appendChild(actionsContainer);
        messageElement.appendChild(timestamp);
        messagesContainer.appendChild(messageElement);

        // Store message in history
        this.messages.push({
            sender: sender,
            text: text,
            farsiTranslation: farsiTranslation,
            timestamp: Date.now()
        });

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('messages-container');
        if (!messagesContainer) return;

        this.isTutorTyping = true;

        const typingElement = document.createElement('div');
        typingElement.className = 'message ai-message typing-indicator';
        typingElement.id = 'typing-indicator';
        
        const dots = document.createElement('div');
        dots.className = 'typing-dots';
        dots.innerHTML = '<span></span><span></span><span></span>';
        
        typingElement.appendChild(dots);
        messagesContainer.appendChild(typingElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        this.isTutorTyping = false;
    }

    setInputDisabled(disabled, customMessage = null) {
        // Disable/enable text input
        const userInput = document.getElementById('user-input');
        if (userInput) {
            userInput.disabled = disabled;
            if (disabled) {
                userInput.placeholder = customMessage || "Tutor is typing...";
                userInput.style.opacity = "0.6";
            } else {
                userInput.placeholder = "Type your message... / پیام خود را بنویسید...";
                userInput.style.opacity = "1";
            }
        }

        // Disable/enable send button
        const sendBtn = document.getElementById('send-btn');
        if (sendBtn) {
            sendBtn.disabled = disabled;
            sendBtn.style.opacity = disabled ? "0.6" : "1";
            sendBtn.style.cursor = disabled ? "not-allowed" : "pointer";
        }

        // Disable/enable voice buttons
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.disabled = disabled;
            voiceBtn.style.opacity = disabled ? "0.6" : "1";
            voiceBtn.style.cursor = disabled ? "not-allowed" : "pointer";
        }

        const voiceInputBtn = document.getElementById('voice-input-btn');
        if (voiceInputBtn) {
            voiceInputBtn.disabled = disabled;
            voiceInputBtn.style.opacity = disabled ? "0.6" : "1";
            voiceInputBtn.style.cursor = disabled ? "not-allowed" : "pointer";
        }
    }

    async startVoiceInput() {
        // Prevent voice input if tutor is typing or hasn't greeted yet
        if (this.isTutorTyping || !this.tutorHasGreeted) {
            return;
        }

        if (this.isListening) {
            return; // Already listening
        }

        this.isListening = true;

        // Update UI to show recording state
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.classList.add('listening');
            const voiceText = voiceBtn.querySelector('.voice-text');
            if (voiceText) {
                voiceText.textContent = 'Starting SpeechTexter...';
            }
        }

        console.log('🎤 Starting SpeechTexter voice recording...');
        this.addMessage('ai', '🎤 Initializing SpeechTexter recording...');

        try {
            // Call the new start recording endpoint
            const response = await fetch(`${CONFIG.BACKEND_URL}/api/stt/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    language: 'en'
                })
            });

            const data = await response.json();
            
            if (data.success && data.recording) {
                console.log('✅ SpeechTexter recording started successfully');
                // Update UI to show active recording
                if (voiceBtn) {
                    const voiceText = voiceBtn.querySelector('.voice-text');
                    if (voiceText) {
                        voiceText.textContent = '🔴 Recording - Hold to speak';
                    }
                }
                this.addMessage('ai', '🔴 Recording active - Speak now! (Hold button down)');
            } else {
                console.warn('⚠️ Failed to start SpeechTexter recording:', data);
                this.addMessage('ai', `⚠️ ${data.message || 'Failed to start recording. Please try again.'}`);
                this.stopVoiceInput();
            }
        } catch (error) {
            console.error('❌ SpeechTexter start recording error:', error);
            this.addMessage('ai', '❌ Voice recording failed to start. Please check that the backend server is running and try again.');
            this.stopVoiceInput();
        }
    }

    async stopVoiceInput() {
        if (!this.isListening) {
            return; // Not currently listening
        }

        console.log('⏹️ Stopping SpeechTexter voice recording...');

        // Update UI to show processing state
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.classList.remove('listening');
            const voiceText = voiceBtn.querySelector('.voice-text');
            if (voiceText) {
                voiceText.textContent = 'Processing transcription...';
            }
        }

        try {
            // Call the new stop recording endpoint
            const response = await fetch(`${CONFIG.BACKEND_URL}/api/stt/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            
            if (data.success && data.text && data.text.trim()) {
                console.log('✅ SpeechTexter transcription:', data.text);
                
                // Update UI to show success
                if (voiceBtn) {
                    const voiceText = voiceBtn.querySelector('.voice-text');
                    if (voiceText) {
                        voiceText.textContent = '✅ Transcription complete';
                    }
                }
                
                const userInput = document.getElementById('user-input');
                if (userInput) {
                    userInput.value = data.text.trim();
                }
                this.addMessage('ai', `✅ Transcribed: "${data.text}"`);
                
                // Auto-send the message after a brief delay to show the transcription
                setTimeout(() => {
                    this.sendMessage();
                }, 500);
            } else {
                console.warn('⚠️ No speech detected or transcription failed:', data);
                
                // Update UI to show no speech detected
                if (voiceBtn) {
                    const voiceText = voiceBtn.querySelector('.voice-text');
                    if (voiceText) {
                        voiceText.textContent = '❌ No speech detected';
                    }
                }
                
                this.addMessage('ai', `⚠️ ${data.message || 'No speech was detected. Please try speaking louder or check your microphone.'}`);
            }
        } catch (error) {
            console.error('❌ SpeechTexter stop recording error:', error);
            
            // Update UI to show error
            if (voiceBtn) {
                const voiceText = voiceBtn.querySelector('.voice-text');
                if (voiceText) {
                    voiceText.textContent = '❌ Recording error';
                }
            }
            
            this.addMessage('ai', '❌ Failed to stop recording or get transcription. Please try again.');
        }

        // Reset UI after a delay
        setTimeout(() => {
            if (voiceBtn) {
                const voiceText = voiceBtn.querySelector('.voice-text');
                if (voiceText) {
                    voiceText.textContent = '🎤 Hold to speak';
                }
            }
        }, 2000);

        this.isListening = false;
    }
                console.warn('⚠️ Recording stopped but no speech detected');
                this.addMessage('ai', '⚠️ No speech detected. Please try speaking louder or closer to the microphone.');
            } else {
                console.warn('⚠️ Failed to stop SpeechTexter recording:', data);
                this.addMessage('ai', `⚠️ ${data.message || 'Failed to stop recording. Please try again.'}`);
            }
        } catch (error) {
            console.error('❌ SpeechTexter stop recording error:', error);
            this.addMessage('ai', '❌ Failed to stop voice recording. Please try again.');
        } finally {
            // Always reset UI state
            this.isListening = false;
            const voiceBtn = document.getElementById('voice-btn');
            if (voiceBtn) {
                voiceBtn.classList.remove('listening');
                const voiceText = voiceBtn.querySelector('.voice-text');
                if (voiceText) {
                    voiceText.textContent = 'Hold to Speak';
                }
            }
        }
    }

    toggleVoiceInput() {
        // Prevent voice input if tutor is typing or hasn't greeted yet
        if (this.isTutorTyping || !this.tutorHasGreeted) {
            return;
        }

        if (this.isListening) {
            this.stopVoiceInput();
        } else {
            this.startVoiceInput();
        }
    }

    speakText(text, language = 'en-US') {
        if (!this.voiceManager) {
            console.warn('Voice manager not available for text-to-speech');
            return;
        }

        try {
            this.voiceManager.speak(text, language);
        } catch (error) {
            console.error('Text-to-speech error:', error);
        }
    }

    handleSpeakClick(messageElement, text, sender, speakBtn) {
        if (!this.voiceManager) {
            console.warn('Voice manager not available for text-to-speech');
            return;
        }

        // If currently speaking this message, stop it
        if (this.currentSpeakingElement === messageElement && this.voiceManager.isSpeaking()) {
            this.stopSpeaking(messageElement, speakBtn);
            return;
        }

        // Stop any other speaking
        if (this.currentSpeakingElement) {
            this.stopSpeaking(this.currentSpeakingElement);
        }

        // Start speaking this message
        this.startSpeaking(messageElement, text, sender, speakBtn);
    }

    startSpeaking(messageElement, text, sender, speakBtn) {
        const language = sender === 'user' ? 'en-US' : 'en-US';
        
        // Update button to show stop state
        speakBtn.innerHTML = '⏹️';
        speakBtn.title = 'Stop reading';
        speakBtn.classList.add('speaking');
        
        // Track current speaking element
        this.currentSpeakingElement = messageElement;
        
        // Add visual indicator to message
        messageElement.classList.add('being-read');
        
        try {
            this.voiceManager.speak(text, language);
            
            // Set up end handler to reset button
            const originalOnEnd = this.voiceManager.synthesis.onend;
            this.voiceManager.synthesis.addEventListener('end', () => {
                this.stopSpeaking(messageElement, speakBtn);
                if (originalOnEnd) originalOnEnd();
            }, { once: true });
            
        } catch (error) {
            console.error('Text-to-speech error:', error);
            this.stopSpeaking(messageElement, speakBtn);
        }
    }

    stopSpeaking(messageElement, speakBtn = null) {
        if (this.voiceManager) {
            this.voiceManager.stopSpeaking();
        }
        
        // Reset button if provided
        if (speakBtn) {
            speakBtn.innerHTML = '🔊';
            speakBtn.title = 'Read aloud';
            speakBtn.classList.remove('speaking');
        } else {
            // Find and reset the speak button in the message
            const messageSpeakBtn = messageElement.querySelector('.speak-btn');
            if (messageSpeakBtn) {
                messageSpeakBtn.innerHTML = '🔊';
                messageSpeakBtn.title = 'Read aloud';
                messageSpeakBtn.classList.remove('speaking');
            }
        }
        
        // Remove visual indicator
        if (messageElement) {
            messageElement.classList.remove('being-read');
        }
        
        // Clear current speaking element
        this.currentSpeakingElement = null;
    }

    async showTranslation(messageElement, text, existingTranslation = null) {
        // Check if translation already exists
        let translation = existingTranslation;
        
        if (!translation) {
            // Request translation from backend
            try {
                const response = await fetch(`${CONFIG.BACKEND_URL}/api/translate`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: text,
                        target_language: 'fa'
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    translation = data.translation || 'Translation not available';
                } else {
                    translation = 'Translation service unavailable';
                }
            } catch (error) {
                console.error('Translation error:', error);
                translation = 'Translation failed';
            }
        }

        // Check if translation is already shown
        const existingTranslation_elem = messageElement.querySelector('.message-translation');
        if (existingTranslation_elem) {
            existingTranslation_elem.remove();
            return;
        }

        // Add translation to the message
        const translationElement = document.createElement('div');
        translationElement.className = 'message-translation';
        translationElement.innerHTML = `<span class="translation-text">${translation}</span>`;
        
        const messageContent = messageElement.querySelector('.message-content');
        messageContent.appendChild(translationElement);
    }

    showCompletionMessage() {
        const congratsMessage = "🎉 Excellent work! You've demonstrated great progress in this topic. Your lesson is now complete and your XP has been saved. You can safely leave the conversation.";
        this.addMessage('ai', congratsMessage);
    }

    handleBackToDashboard() {
        // Check if conversation is complete
        if (this.conversationComplete) {
            this.goBackToDashboard();
            return;
        }

        // Show confirmation popup for incomplete lesson
        this.showLeaveConfirmation();
    }

    showLeaveConfirmation() {
        const modal = document.createElement('div');
        modal.className = 'completion-warning-modal';
        modal.innerHTML = `
            <div class="modal-overlay">
                <div class="modal-content">
                    <h3>⚠️ Leave Conversation?</h3>
                    <p>Are you sure you want to leave this conversation?</p>
                    <p><strong>All XP gained during this session will be lost.</strong></p>
                    <div class="modal-actions">
                        <button class="btn-continue" onclick="this.closest('.completion-warning-modal').remove()">
                            Continue Learning
                        </button>
                        <button class="btn-leave" onclick="window.conversationManager.confirmLeave()">
                            Leave (Lose XP)
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Set global reference for the button onclick
        window.conversationManager = this;
    }

    confirmLeave() {
        // Remove any confirmation modal
        const modal = document.querySelector('.completion-warning-modal');
        if (modal) {
            modal.remove();
        }
        
        // Leave without awarding XP
        this.goBackToDashboard(false); // false = no XP
    }

    async awardCompletionXP() {
        try {
            const conversationDuration = Date.now() - this.conversationStartTime;
            const minutes = Math.floor(conversationDuration / 60000);
            
            await fetch(`${CONFIG.BACKEND_URL}/api/progress`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.user.id,
                    action: 'complete_conversation',
                    topic: this.currentTopic,
                    duration_minutes: minutes,
                    message_count: this.messageCount
                })
            });
            
            console.log('XP awarded for completed conversation');
        } catch (error) {
            console.error('Failed to award XP:', error);
        }
    }

    goBackToDashboard(awardXP = true) {
        // Stop any ongoing voice input
        this.stopVoiceInput();
        
        // Stop any ongoing speech
        if (this.currentSpeakingElement) {
            this.stopSpeaking(this.currentSpeakingElement);
        }
        
        // End the chat session to cleanup chatbot driver
        this.endChatSession();
        
        // Award XP only if lesson was completed
        if (awardXP && this.conversationComplete && this.user) {
            this.awardCompletionXP();
        }
        
        // Return to main app
        if (window.app) {
            window.app.showDashboard();
        }
    }

    async endChatSession() {
        try {
            await fetch(`${CONFIG.BACKEND_URL}/api/chat/session/end`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.user ? this.user.id : null,
                    session_id: `conversation_${this.currentTopic}_${this.conversationStartTime}`
                })
            });
            console.log('Chat session ended successfully');
        } catch (error) {
            console.error('Failed to end chat session:', error);
        }
    }
}

// Make ConversationManager available globally
window.ConversationManager = ConversationManager;
