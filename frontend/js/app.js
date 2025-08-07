// Main Application Controller for Language Learning App

class App {
    constructor() {
        this.currentUser = null;
        this.currentScreen = 'welcome-screen';
        this.conversationManager = null;
        this.voiceManager = null;
        this.progressTracker = null;
        this.isInitialised = false;
        
        this.init();
    }

    async init() {
        try {
            Utils.log('Initialising Language Learning App...');
            
            // Show loading screen
            this.showLoadingScreen();
            
            // Initialise core components
            await this.initialiseComponents();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Check for existing user session
            await this.checkExistingSession();
            
            // Hide loading screen
            this.hideLoadingScreen();
            
            this.isInitialised = true;
            Utils.log('App initialised successfully');
            
        } catch (error) {
            Utils.handleError(error, 'App initialisation');
            this.showErrorMessage('Failed to initialise app. Please refresh the page.');
        }
    }

    showLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            // Clear any inline styles and show with class
            loadingScreen.style.display = '';
            loadingScreen.classList.add('active');
        }
    }

    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.classList.remove('active');
            // Ensure it's hidden by removing any inline styles and forcing display none
            loadingScreen.style.display = 'none';
        }
    }

    async initialiseComponents() {
        // Initialise managers
        this.voiceManager = new VoiceManager();
        this.progressTracker = new ProgressTracker();
        
        // Initialise voice capabilities
        await this.voiceManager.initialise();
        
        Utils.log('Core components initialised');
    }

    setupEventListeners() {
        // Welcome screen events
        const newUserBtn = document.getElementById('new-user-btn');
        const returningUserBtn = document.getElementById('returning-user-btn');
        const langToggle = document.getElementById('lang-toggle');

        if (newUserBtn) {
            newUserBtn.addEventListener('click', () => this.showRegistration());
        }

        if (returningUserBtn) {
            returningUserBtn.addEventListener('click', () => this.showLogin());
        }

        if (langToggle) {
            langToggle.addEventListener('click', () => this.toggleLanguage());
        }

        // Registration form events
        const registrationForm = document.getElementById('registration-form');
        if (registrationForm) {
            registrationForm.addEventListener('submit', (e) => this.handleRegistration(e));
        }

        // Login form events
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Dashboard events
        const conversationPracticeBtn = document.getElementById('conversation-practice');
        const pronunciationPracticeBtn = document.getElementById('pronunciation-practice');
        const visualPracticeBtn = document.getElementById('visual-practice');

        if (conversationPracticeBtn) {
            conversationPracticeBtn.addEventListener('click', () => this.startConversationPractice());
        }

        if (pronunciationPracticeBtn) {
            pronunciationPracticeBtn.addEventListener('click', () => this.startPronunciationPractice());
        }

        if (visualPracticeBtn) {
            visualPracticeBtn.addEventListener('click', () => this.startVisualPractice());
        }

        // Header actions
        const settingsBtn = document.getElementById('settings-btn');
        const logoutBtn = document.getElementById('logout-btn');
        const voiceToggle = document.getElementById('voice-toggle');

        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.showSettings());
        }

        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }

        if (voiceToggle) {
            voiceToggle.addEventListener('click', () => this.toggleVoiceMode());
        }

        // Back buttons (excluding back-to-dashboard which is handled by ConversationManager)
        const backToWelcome = document.getElementById('back-to-welcome');
        const backToWelcomeFromRegister = document.getElementById('back-to-welcome-from-register');

        if (backToWelcome) {
            backToWelcome.addEventListener('click', () => this.showWelcome());
        }

        if (backToWelcomeFromRegister) {
            backToWelcomeFromRegister.addEventListener('click', () => this.showWelcome());
        }

        // Settings modal
        const closeSettings = document.getElementById('close-settings');
        if (closeSettings) {
            closeSettings.addEventListener('click', () => this.hideSettings());
        }

        // Level selector in settings
        const levelSelect = document.getElementById('level-select');
        if (levelSelect) {
            levelSelect.addEventListener('change', (e) => this.updateUserLevel(e.target.value));
        }

        Utils.log('Event listeners set up');
    }

    async checkExistingSession() {
        const userProfile = storage.getUserProfile();
        
        if (userProfile && userProfile.username) {
            // Verify user still exists in database
            try {
                const isValid = await this.verifyUser(userProfile.username);
                if (isValid) {
                    this.currentUser = userProfile;
                    
                    // Track daily login for existing session (page reload)
                    await this.trackDailyLogin(userProfile.user_id || userProfile.id);
                    
                    await this.showDashboard();
                    Utils.log('Existing session found', userProfile);
                } else {
                    storage.clearUserProfile();
                    this.showWelcome();
                }
            } catch (error) {
                console.error('Error verifying user:', error);
                // If verification fails, clear session to be safe
                storage.clearUserProfile();
                this.showWelcome();
            }
        } else {
            this.showWelcome();
        }
    }

    showWelcome() {
        Utils.showScreen('welcome-screen');
        this.currentScreen = 'welcome-screen';
    }

    showRegistration() {
        Utils.showScreen('registration-screen');
        this.currentScreen = 'registration-screen';
    }

    showLogin() {
        Utils.showScreen('login-screen');
        this.currentScreen = 'login-screen';
    }

    async handleRegistration(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const userData = {
            username: formData.get('username'),
            password: formData.get('password'),
            confirmPassword: formData.get('confirm-password'),
            name: formData.get('name'),
            age: parseInt(formData.get('age')),
            level: parseInt(formData.get('level'))
        };

        // Validate data
        if (!userData.username || userData.username.length < 3) {
            this.showErrorMessage('Username must be at least 3 characters long.');
            return;
        }

        if (!userData.password || userData.password.length < 6) {
            this.showErrorMessage('Password must be at least 6 characters long.');
            return;
        }

        if (userData.password !== userData.confirmPassword) {
            this.showErrorMessage('Passwords do not match.');
            return;
        }

        if (!userData.name || !Utils.validateAge(userData.age) || !Utils.validateLevel(userData.level)) {
            this.showErrorMessage('Please fill in all fields correctly.');
            return;
        }

        try {
            // Remove confirm password before sending to API
            delete userData.confirmPassword;
            
            // Register user
            const user = await this.registerUser(userData);
            this.currentUser = user;
            
            // Save to local storage
            storage.saveUserProfile(user);
            
            await this.showDashboard();
            this.showSuccessMessage('Welcome! Your learning journey begins now.');
            
        } catch (error) {
            Utils.handleError(error, 'User registration');
            this.showErrorMessage('Registration failed. Please try again.');
        }
    }

    async handleLogin(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const username = formData.get('username');
        const password = formData.get('password');

        if (!username || !password) {
            this.showErrorMessage('Please enter both username and password.');
            return;
        }

        try {
            // Try to find user (API call)
            const user = await this.loginUser(username, password);
            
            if (user) {
                this.currentUser = user;
                storage.saveUserProfile(user);
                
                // Track daily login for XP
                await this.trackDailyLogin(user.user_id);
                
                await this.showDashboard();
                this.showSuccessMessage(`Welcome back, ${user.name}!`);
            } else {
                this.showErrorMessage('Invalid username or password.');
            }
            
        } catch (error) {
            Utils.handleError(error, 'User login');
            this.showErrorMessage('Login failed. Please try again.');
        }
    }

    async registerUser(userData) {
        try {
            // Map frontend level numbers to backend level strings
            const levelMap = {
                1: 'absolute_beginner',
                2: 'beginner', 
                3: 'intermediate',
                4: 'advanced'
            };

            // Call backend API to register user
            const response = await fetch('/api/user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'create',
                    username: userData.username,
                    password: userData.password,
                    confirmPassword: userData.password, // Same as password since frontend already validated
                    displayName: userData.name, // Map frontend 'name' to backend 'displayName'
                    age: userData.age,
                    learningLevel: levelMap[userData.level] || 'beginner' // Map numeric level to string
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Unknown server error' }));
                throw new Error(errorData.error || `Server error: ${response.status}`);
            }

            const result = await response.json();
            
            // Create user object with API response
            const user = {
                id: result.user_id,
                user_id: result.user_id,
                username: userData.username,
                name: userData.name,  // Display name
                age: userData.age,
                level: userData.level,
                created_at: new Date().toISOString(),
                settings: storage.getSettings()
            };

            Utils.log('User registered successfully', user);
            return user;
            
        } catch (error) {
            Utils.log('Registration failed:', error);
            // Don't fall back to local storage - throw the error to show user what went wrong
            throw error;
        }
    }

    async loginUser(username, password) {
        try {
            // Call backend API to login user
            const response = await fetch('/api/user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    action: 'login',
                    username: username, 
                    password: password 
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Login failed');
            }

            const result = await response.json();
            
            // Create user object with API response
            const user = {
                id: result.user_id,
                user_id: result.user_id,
                username: username,  // Use the username from login form
                name: username,      // Use username as display name for now
                age: 25,            // Default age
                level: 1,           // Default level
                created_at: new Date().toISOString(),
                settings: storage.getSettings()
            };

            Utils.log('User logged in successfully', user);
            return user;
            
        } catch (error) {
            Utils.log('Login failed:', error);
            throw error; // Don't fall back to local storage for authentication
        }
    }

    async logout() {
        try {
            // Call logout API if user is logged in
            if (this.currentUser && this.currentUser.user_id) {
                await fetch('/api/user/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ user_id: this.currentUser.user_id })
                });
            }
        } catch (error) {
            console.error('Logout API error:', error);
        }

        // Clear local data
        this.currentUser = null;
        storage.clearUserProfile();
        
        // Reset managers
        if (this.conversationManager) {
            this.conversationManager = null;
        }
        
        // Show welcome screen
        this.showWelcome();
        this.showSuccessMessage('Logged out successfully.');
    }

    async verifyUser(username) {
        if (!username) {
            return false;
        }

        try {
            const response = await fetch('/api/user/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username: username })
            });

            if (!response.ok) {
                // User doesn't exist anymore
                return false;
            }

            const result = await response.json();
            return result.user_exists;
            
        } catch (error) {
            console.error('User verification error:', error);
            return true; // Assume user exists if verification fails
        }
    }

    async showDashboard() {
        if (!this.currentUser) {
            this.showWelcome();
            return;
        }

        Utils.showScreen('dashboard-screen');
        this.currentScreen = 'dashboard-screen';

        // Update UI with user data
        await this.updateDashboard();
    }

    async updateDashboard() {
        // Update greeting
        const userGreeting = document.getElementById('user-greeting');
        if (userGreeting && this.currentUser) {
            const timeOfDay = Utils.getTimeOfDay();
            const greeting = `Good ${timeOfDay}, ${this.currentUser.name}!`;
            userGreeting.textContent = greeting;
        }

        // Update progress
        await this.updateProgressDisplay();

        // Update topics
        this.updateTopicsDisplay();

        // Update daily challenge
        this.updateDailyChallenge();
    }

    async updateProgressDisplay() {
        const currentUser = storage.getCurrentUser();
        if (!currentUser) return;

        try {
            // Fetch user level info from backend
            const response = await fetch(`/api/user-level-info/${currentUser.user_id || currentUser.id}`);
            if (response.ok) {
                const levelInfo = await response.json();
                this.displayLevelInfo(levelInfo);
            } else {
                console.warn('Failed to fetch level info, using local progress');
                this.displayLocalProgress();
            }
        } catch (error) {
            console.error('Error fetching user level info:', error);
            this.displayLocalProgress();
        }
    }

    displayLevelInfo(levelInfo) {
        // Update level badge
        const levelNumberEl = document.getElementById('user-level');
        if (levelNumberEl) {
            levelNumberEl.textContent = levelInfo.level;
        }

        // Update XP bar and text
        const xpFillEl = document.getElementById('xp-fill');
        const currentXpEl = document.getElementById('current-xp');
        const nextLevelXpEl = document.getElementById('next-level-xp');
        
        if (xpFillEl) {
            const percentage = levelInfo.xp_progress_percent || 0;
            xpFillEl.style.width = `${percentage}%`;
        }
        
        if (currentXpEl) {
            currentXpEl.textContent = levelInfo.current_xp || 0;
        }
        
        if (nextLevelXpEl) {
            nextLevelXpEl.textContent = levelInfo.next_level_xp || 100;
        }

        // Update progress stats
        const totalXpEl = document.getElementById('total-xp');
        const topicsCompletedEl = document.getElementById('topics-completed');
        const daysStreakEl = document.getElementById('days-streak');

        if (totalXpEl) {
            totalXpEl.textContent = levelInfo.total_xp || 0;
        }

        if (topicsCompletedEl) {
            topicsCompletedEl.textContent = levelInfo.topics_completed || 0;
        }

        if (daysStreakEl) {
            daysStreakEl.textContent = levelInfo.current_streak || 0;
        }

        // Update daily progress bar (if it exists)
        const dailyProgressEl = document.getElementById('daily-progress');
        if (dailyProgressEl) {
            const progress = this.progressTracker.getProgress();
            const dailyGoal = storage.getSettings().daily_goal || 3;
            const todayProgress = progress.phrases_learned_today || 0;
            const percentage = Math.min((todayProgress / dailyGoal) * 100, 100);
            dailyProgressEl.style.width = `${percentage}%`;
        }
    }

    displayLocalProgress() {
        // Fallback to local progress if backend is unavailable
        const progress = this.progressTracker.getProgress();
        
        const topicsCompletedEl = document.getElementById('topics-completed');
        const daysStreakEl = document.getElementById('days-streak');

        if (topicsCompletedEl) {
            topicsCompletedEl.textContent = progress.topics_completed.length;
        }

        if (daysStreakEl) {
            daysStreakEl.textContent = progress.current_streak;
        }

        // Set default values for XP display
        const totalXpEl = document.getElementById('total-xp');
        const currentXpEl = document.getElementById('current-xp');
        const nextLevelXpEl = document.getElementById('next-level-xp');
        
        if (totalXpEl) totalXpEl.textContent = '0';
        if (currentXpEl) currentXpEl.textContent = '0';
        if (nextLevelXpEl) nextLevelXpEl.textContent = '100';
    }

    updateTopicsDisplay() {
        const topicsGrid = document.getElementById('topics-grid');
        if (!topicsGrid || !this.currentUser) return;

        const userLevel = this.currentUser.level;
        const topics = CONFIG.LEVELS[userLevel]?.topics || [];
        const completedTopics = this.progressTracker.getProgress().topics_completed;

        topicsGrid.innerHTML = '';

        if (topics.length === 0) {
            topicsGrid.innerHTML = '<p class="no-topics">No topics available for this level.</p>';
            return;
        }

        topics.forEach(topicId => {
            const topicDetails = CONFIG.TOPIC_DETAILS[topicId];
            if (!topicDetails) return;

            const isCompleted = completedTopics.includes(topicId);
            
            const topicBtn = Utils.createElement('button', {
                className: `topic-btn ${isCompleted ? 'completed' : ''}`,
                'data-topic': topicId
            });

            topicBtn.innerHTML = `
                <div class="topic-emoji">${topicDetails.emoji}</div>
                <div class="topic-name">${topicDetails.name}</div>
                ${isCompleted ? '<div class="topic-status">✓</div>' : ''}
            `;

            topicBtn.addEventListener('click', () => this.startTopicConversation(topicId));
            topicsGrid.appendChild(topicBtn);
        });
    }

    updateDailyChallenge() {
        const challengeTextEl = document.getElementById('daily-challenge-text');
        const challengeProgressEl = document.getElementById('challenge-progress');
        
        if (!challengeTextEl || !challengeProgressEl) return;

        const progress = this.progressTracker.getProgress();
        const dailyGoal = storage.getSettings().daily_goal || 3;
        const todayProgress = progress.phrases_learned_today || 0;

        challengeTextEl.textContent = `Learn ${dailyGoal} new phrases today`;
        challengeProgressEl.textContent = `${todayProgress}/${dailyGoal} completed`;
    }

    startConversationPractice() {
        if (!this.currentUser) return;

        // Show topic selection first
        this.showTopicSelection((topic) => {
            this.startTopicConversation(topic);
        });
    }

    startTopicConversation(topicId) {
        Utils.showScreen('conversation-screen');
        this.currentScreen = 'conversation-screen';

        // Initialize conversation manager if needed
        if (!this.conversationManager) {
            this.conversationManager = new ConversationManager(this.currentUser, this.voiceManager);
        }

        this.conversationManager.startConversation(topicId);
    }

    startPronunciationPractice() {
        // Implementation for pronunciation practice
        this.showInfoMessage('Pronunciation practice will be available soon!');
    }

    startVisualPractice() {
        // Implementation for visual learning
        this.showInfoMessage('Visual learning will be available soon!');
    }

    showTopicSelection(callback) {
        // Create and show topic selection modal
        const modal = Utils.createElement('div', { className: 'modal active' });
        const modalContent = Utils.createElement('div', { className: 'modal-content' });
        
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3>Choose a Topic</h3>
                <button class="close-btn">&times;</button>
            </div>
            <div class="modal-body">
                <div class="topic-selection" id="topic-selection"></div>
            </div>
        `;

        modal.appendChild(modalContent);
        document.body.appendChild(modal);

        // Populate topics
        const topicSelection = modal.querySelector('#topic-selection');
        const userLevel = this.currentUser.level;
        const topics = CONFIG.LEVELS[userLevel]?.topics || [];

        topics.forEach(topicId => {
            const topicDetails = CONFIG.TOPIC_DETAILS[topicId];
            if (!topicDetails) return;

            const topicOption = Utils.createElement('div', {
                className: 'topic-option',
                'data-topic': topicId
            });

            topicOption.innerHTML = `
                <div class="topic-emoji">${topicDetails.emoji}</div>
                <div class="topic-name">${topicDetails.name}</div>
                <div class="topic-farsi">${topicDetails.farsi}</div>
            `;

            topicOption.addEventListener('click', () => {
                callback(topicId);
                document.body.removeChild(modal);
            });

            topicSelection.appendChild(topicOption);
        });

        // Close button
        modal.querySelector('.close-btn').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
    }

    async showSettings() {
        const settingsModal = document.getElementById('settings-modal');
        if (settingsModal) {
            settingsModal.classList.add('active');
            await this.populateSettings();
        }
    }

    hideSettings() {
        const settingsModal = document.getElementById('settings-modal');
        if (settingsModal) {
            settingsModal.classList.remove('active');
        }
    }

    async populateSettings() {
        const settings = storage.getSettings();
        
        // Update level selector with current user level from backend
        if (this.currentUser && this.currentUser.user_id) {
            try {
                // Fetch current learning level from backend
                const response = await fetch(`/api/user/${this.currentUser.user_id}`);
                if (response.ok) {
                    const userData = await response.json();
                    
                    // Map backend learning level strings to frontend numbers
                    const levelMap = {
                        'absolute_beginner': 1,
                        'beginner': 2,
                        'intermediate': 3,
                        'advanced': 4
                    };
                    
                    const frontendLevel = levelMap[userData.learning_level] || 2;
                    
                    // Update level selector
                    const levelSelect = document.getElementById('level-select');
                    if (levelSelect) {
                        levelSelect.value = frontendLevel;
                    }
                    
                    // Update local user data if it differs
                    if (this.currentUser.level !== frontendLevel) {
                        this.currentUser.level = frontendLevel;
                        storage.updateUserProfile({ level: frontendLevel });
                    }
                    
                } else {
                    console.warn('Failed to fetch user level from backend, using local data');
                    // Fall back to local level
                    const levelSelect = document.getElementById('level-select');
                    if (levelSelect && this.currentUser) {
                        levelSelect.value = this.currentUser.level;
                    }
                }
            } catch (error) {
                console.error('Error fetching user level:', error);
                // Fall back to local level
                const levelSelect = document.getElementById('level-select');
                if (levelSelect && this.currentUser) {
                    levelSelect.value = this.currentUser.level;
                }
            }
        }

        // Update checkboxes
        const farsiAudio = document.getElementById('farsi-audio');
        const visualAids = document.getElementById('visual-aids');
        const pronunciationCheck = document.getElementById('pronunciation-check');

        if (farsiAudio) farsiAudio.checked = settings.farsi_audio;
        if (visualAids) visualAids.checked = settings.visual_aids;
        if (pronunciationCheck) pronunciationCheck.checked = settings.pronunciation_check;
    }

    async updateUserLevel(newLevel) {
        if (!this.currentUser) return;

        const numericLevel = parseInt(newLevel);
        
        // Map frontend level numbers to backend level strings
        const levelMap = {
            1: 'absolute_beginner',
            2: 'beginner', 
            3: 'intermediate',
            4: 'advanced'
        };

        const learningLevel = levelMap[numericLevel] || 'beginner';

        try {
            // Call backend API to update user learning level
            const response = await fetch(`/api/user/${this.currentUser.user_id}/learning-level`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    learning_level: learningLevel
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Unknown server error' }));
                throw new Error(errorData.error || `Server error: ${response.status}`);
            }

            const result = await response.json();
            
            // Update local user data
            this.currentUser.level = numericLevel;
            storage.updateUserProfile({ level: numericLevel });
            
            // Refresh dashboard to show updated level
            await this.updateDashboard();
            
            this.showSuccessMessage(`Learning level updated to Level ${numericLevel}!`);
            Utils.log('User learning level updated successfully', result);
            
        } catch (error) {
            Utils.handleError(error, 'Update learning level');
            this.showErrorMessage('Failed to update learning level. Please try again.');
            
            // Reset the select to previous value on error
            const levelSelect = document.getElementById('level-select');
            if (levelSelect) {
                levelSelect.value = this.currentUser.level;
            }
        }
    }

    toggleVoiceMode() {
        if (this.voiceManager) {
            this.voiceManager.toggleVoiceMode();
        }
    }

    toggleLanguage() {
        // Implementation for language toggle
        this.showInfoMessage('Language toggle feature coming soon!');
    }

    logout() {
        this.currentUser = null;
        storage.clear();
        this.showWelcome();
        this.showInfoMessage('You have been logged out.');
    }

    // Utility methods for user feedback
    showSuccessMessage(message) {
        Utils.showNotification(message, 'success');
    }

    showErrorMessage(message) {
        Utils.showNotification(message, 'error');
    }

    showInfoMessage(message) {
        Utils.showNotification(message, 'info');
    }

    // Progress tracking methods
    async trackDailyLogin(userId) {
        try {
            if (!userId) {
                return;
            }
            
            const response = await fetch('/api/track-login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_id: userId })
            });
            
            const result = await response.json();
            
            if (result.success && result.first_login_today) {
                this.showSuccessMessage('Daily login bonus earned! +10 XP');
            }
        } catch (error) {
            console.error('Error tracking daily login:', error);
        }
    }

    async trackMessage(userId, topicId = null, messageType = 'text') {
        try {
            const response = await fetch('/api/track-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    user_id: userId, 
                    topic_id: topicId,
                    type: messageType
                })
            });
            
            const result = await response.json();
            if (result.success) {
                // Refresh XP display
                await this.progressTracker.updateProgressDisplay();
            }
        } catch (error) {
            console.error('Error tracking message:', error);
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
