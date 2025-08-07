// Topics Manager for Language Learning App

class TopicsManager {
    constructor() {
        this.currentTopic = null;
        this.currentPhrases = [];
        this.currentPhraseIndex = 0;
        this.topicProgress = {};
    }

    // Initialise topics for current user level
    initialiseForLevel(level) {
        const levelConfig = CONFIG.LEVELS[level];
        if (!levelConfig) {
            Utils.log('Level not found', level);
            return false;
        }

        this.currentLevel = level;
        this.availableTopics = levelConfig.topics;
        
        Utils.log('Topics initialised for level', { level, topics: this.availableTopics });
        return true;
    }

    // Get all topics for current level
    getAvailableTopics() {
        return this.availableTopics.map(topicId => {
            const topicDetail = CONFIG.TOPIC_DETAILS[topicId];
            const progress = progressTracker.getTopicProgress(topicId);
            
            return {
                id: topicId,
                name: topicDetail?.name || topicId,
                emoji: topicDetail?.emoji || '📚',
                description: topicDetail?.description || '',
                farsi_name: topicDetail?.farsi_name || '',
                difficulty: topicDetail?.difficulty || 'beginner',
                estimated_time: topicDetail?.estimated_time || '10-15 min',
                status: progress?.status || 'not_started',
                phrases_learned: progress?.phrases_learned || 0,
                conversations_completed: progress?.conversations_completed || 0,
                last_practiced: progress?.last_practiced || null,
                completion_percentage: this.calculateTopicCompletion(topicId)
            };
        });
    }

    // Get topic by ID
    getTopic(topicId) {
        const topicDetail = CONFIG.TOPIC_DETAILS[topicId];
        if (!topicDetail) return null;

        const progress = progressTracker.getTopicProgress(topicId);
        
        return {
            id: topicId,
            name: topicDetail.name,
            emoji: topicDetail.emoji,
            description: topicDetail.description,
            farsi_name: topicDetail.farsi_name,
            difficulty: topicDetail.difficulty,
            estimated_time: topicDetail.estimated_time,
            phrases: this.getTopicPhrases(topicId),
            conversations: this.getTopicConversations(topicId),
            status: progress?.status || 'not_started',
            progress: progress || {}
        };
    }

    // Get phrases for a specific topic
    getTopicPhrases(topicId) {
        const topicDetail = CONFIG.TOPIC_DETAILS[topicId];
        if (!topicDetail || !topicDetail.key_phrases) return [];

        return topicDetail.key_phrases.map((phrase, index) => ({
            id: `${topicId}_phrase_${index}`,
            english: phrase.english,
            farsi: phrase.farsi,
            pronunciation: phrase.pronunciation,
            audio_url: phrase.audio_url || null,
            difficulty: phrase.difficulty || 'beginner',
            context: phrase.context || '',
            examples: phrase.examples || []
        }));
    }

    // Get conversation starters for a topic
    getTopicConversations(topicId) {
        const topicDetail = CONFIG.TOPIC_DETAILS[topicId];
        if (!topicDetail || !topicDetail.conversation_starters) return [];

        return topicDetail.conversation_starters.map((starter, index) => ({
            id: `${topicId}_conv_${index}`,
            english: starter.english,
            farsi: starter.farsi,
            context: starter.context || '',
            difficulty: starter.difficulty || 'beginner',
            expected_responses: starter.expected_responses || []
        }));
    }

    // Start practicing a topic
    startTopic(topicId) {
        const topic = this.getTopic(topicId);
        if (!topic) {
            Utils.showNotification('Topic not found', 'error');
            return false;
        }

        this.currentTopic = topic;
        this.currentPhrases = topic.phrases;
        this.currentPhraseIndex = 0;

        // Update progress
        progressTracker.updateConversationProgress(topicId);

        // Show topic introduction
        this.showTopicIntroduction();

        Utils.log('Topic started', topicId);
        return true;
    }

    // Show topic introduction modal
    showTopicIntroduction() {
        const topic = this.currentTopic;
        const modal = document.getElementById('topicIntroModal');
        
        if (modal && topic) {
            document.getElementById('topicIntroEmoji').textContent = topic.emoji;
            document.getElementById('topicIntroName').textContent = topic.name;
            document.getElementById('topicIntroFarsi').textContent = topic.farsi_name;
            document.getElementById('topicIntroDescription').textContent = topic.description;
            document.getElementById('topicIntroTime').textContent = topic.estimated_time;
            document.getElementById('topicIntroPhrases').textContent = topic.phrases.length;

            Utils.showModal('topicIntroModal');
        }
    }

    // Get current phrase
    getCurrentPhrase() {
        if (!this.currentPhrases || this.currentPhraseIndex >= this.currentPhrases.length) {
            return null;
        }

        return this.currentPhrases[this.currentPhraseIndex];
    }

    // Move to next phrase
    nextPhrase() {
        if (this.currentPhraseIndex < this.currentPhrases.length - 1) {
            this.currentPhraseIndex++;
            return this.getCurrentPhrase();
        }
        
        // Topic completed
        this.completeTopic();
        return null;
    }

    // Move to previous phrase
    previousPhrase() {
        if (this.currentPhraseIndex > 0) {
            this.currentPhraseIndex--;
            return this.getCurrentPhrase();
        }
        return null;
    }

    // Mark current phrase as learned
    markPhraseAsLearned() {
        const currentPhrase = this.getCurrentPhrase();
        if (!currentPhrase) return;

        // Add to spaced repetition system
        progressTracker.addSpacedRepetitionItem(
            currentPhrase.english,
            currentPhrase.farsi,
            this.currentTopic.id
        );

        // Update progress
        progressTracker.updatePhrasesLearned(1, this.currentTopic.id);

        Utils.log('Phrase marked as learned', currentPhrase);
    }

    // Complete current topic
    completeTopic() {
        if (!this.currentTopic) return;

        progressTracker.completeTopic(this.currentTopic.id);
        
        // Show completion modal
        this.showTopicCompletion();
        
        Utils.log('Topic completed', this.currentTopic.id);
    }

    // Show topic completion modal
    showTopicCompletion() {
        const topic = this.currentTopic;
        const modal = document.getElementById('topicCompleteModal');
        
        if (modal && topic) {
            document.getElementById('completeTopicName').textContent = topic.name;
            document.getElementById('completeTopicEmoji').textContent = topic.emoji;
            document.getElementById('completePhraseCount').textContent = topic.phrases.length;
            
            // Calculate completion time (mock)
            document.getElementById('completeTime').textContent = '12 minutes';
            
            Utils.showModal('topicCompleteModal');
        }
    }

    // Calculate topic completion percentage
    calculateTopicCompletion(topicId) {
        const progress = progressTracker.getTopicProgress(topicId);
        if (!progress) return 0;

        const totalPhrases = this.getTopicPhrases(topicId).length;
        const learnedPhrases = progress.phrases_learned || 0;
        
        if (totalPhrases === 0) return 0;
        return Math.round((learnedPhrases / totalPhrases) * 100);
    }

    // Get recommended topics for user
    getRecommendedTopics() {
        const allTopics = this.getAvailableTopics();
        const recommendations = [];

        // Sort by priority: in_progress > not_started > completed
        const priorities = { 'in_progress': 1, 'not_started': 2, 'completed': 3 };
        
        allTopics.sort((a, b) => {
            const priorityA = priorities[a.status] || 4;
            const priorityB = priorities[b.status] || 4;
            
            if (priorityA !== priorityB) {
                return priorityA - priorityB;
            }
            
            // Secondary sort by last practiced (most recent first for in_progress)
            if (a.status === 'in_progress' && b.status === 'in_progress') {
                const dateA = new Date(a.last_practiced || 0);
                const dateB = new Date(b.last_practiced || 0);
                return dateB - dateA;
            }
            
            return 0;
        });

        return allTopics.slice(0, 6); // Return top 6 recommendations
    }

    // Generate daily practice session
    generateDailyPractice() {
        const dueSpacedItems = progressTracker.getDueSpacedRepetitionItems();
        const inProgressTopics = this.getAvailableTopics().filter(t => t.status === 'in_progress');
        const newTopics = this.getAvailableTopics().filter(t => t.status === 'not_started');

        const practiceSession = {
            spaced_repetition: dueSpacedItems.slice(0, 5), // Max 5 review items
            continue_topics: inProgressTopics.slice(0, 2), // Max 2 topics to continue
            new_topics: newTopics.slice(0, 1), // Max 1 new topic
            estimated_time: this.calculatePracticeTime(dueSpacedItems.length, inProgressTopics.length, newTopics.length)
        };

        return practiceSession;
    }

    // Calculate estimated practice time
    calculatePracticeTime(reviewCount, continueCount, newCount) {
        const reviewTime = reviewCount * 1; // 1 minute per review
        const continueTime = continueCount * 8; // 8 minutes per topic continuation
        const newTime = newCount * 15; // 15 minutes per new topic
        
        return reviewTime + continueTime + newTime;
    }

    // Search topics by query
    searchTopics(query) {
        if (!query || query.trim() === '') {
            return this.getAvailableTopics();
        }

        const searchTerm = query.toLowerCase().trim();
        const allTopics = this.getAvailableTopics();

        return allTopics.filter(topic => {
            return topic.name.toLowerCase().includes(searchTerm) ||
                   topic.description.toLowerCase().includes(searchTerm) ||
                   topic.farsi_name.toLowerCase().includes(searchTerm) ||
                   topic.id.toLowerCase().includes(searchTerm);
        });
    }

    // Filter topics by criteria
    filterTopics(criteria) {
        const allTopics = this.getAvailableTopics();
        
        return allTopics.filter(topic => {
            // Filter by status
            if (criteria.status && criteria.status !== 'all' && topic.status !== criteria.status) {
                return false;
            }
            
            // Filter by difficulty
            if (criteria.difficulty && criteria.difficulty !== 'all' && topic.difficulty !== criteria.difficulty) {
                return false;
            }
            
            // Filter by completion percentage
            if (criteria.completion_min !== undefined && topic.completion_percentage < criteria.completion_min) {
                return false;
            }
            
            if (criteria.completion_max !== undefined && topic.completion_percentage > criteria.completion_max) {
                return false;
            }
            
            return true;
        });
    }

    // Get topic statistics
    getTopicStatistics() {
        const allTopics = this.getAvailableTopics();
        
        const stats = {
            total: allTopics.length,
            completed: allTopics.filter(t => t.status === 'completed').length,
            in_progress: allTopics.filter(t => t.status === 'in_progress').length,
            not_started: allTopics.filter(t => t.status === 'not_started').length,
            total_phrases: allTopics.reduce((sum, t) => sum + (t.phrases_learned || 0), 0),
            total_conversations: allTopics.reduce((sum, t) => sum + (t.conversations_completed || 0), 0),
            average_completion: Math.round(allTopics.reduce((sum, t) => sum + t.completion_percentage, 0) / allTopics.length)
        };

        stats.completion_rate = allTopics.length > 0 ? Math.round((stats.completed / stats.total) * 100) : 0;
        
        return stats;
    }

    // Update topic display in UI
    updateTopicDisplay() {
        const topicsGrid = document.getElementById('topicsGrid');
        if (!topicsGrid) return;

        const topics = this.getAvailableTopics();
        
        topicsGrid.innerHTML = topics.map(topic => `
            <div class="topic-card ${topic.status}" data-topic-id="${topic.id}">
                <div class="topic-emoji">${topic.emoji}</div>
                <div class="topic-content">
                    <h3 class="topic-name">${topic.name}</h3>
                    <p class="topic-farsi">${topic.farsi_name}</p>
                    <div class="topic-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${topic.completion_percentage}%"></div>
                        </div>
                        <span class="progress-text">${topic.completion_percentage}%</span>
                    </div>
                    <div class="topic-meta">
                        <span class="topic-phrases">${topic.phrases_learned} phrases</span>
                        <span class="topic-status status-${topic.status}">${topic.status.replace('_', ' ')}</span>
                    </div>
                </div>
                <button class="topic-action-btn" onclick="topicsManager.startTopic('${topic.id}')">
                    ${topic.status === 'completed' ? 'Review' : topic.status === 'in_progress' ? 'Continue' : 'Start'}
                </button>
            </div>
        `).join('');

        Utils.log('Topic display updated', { count: topics.length });
    }

    // Update recommended topics display
    updateRecommendedDisplay() {
        const recommendedContainer = document.getElementById('recommendedTopics');
        if (!recommendedContainer) return;

        const recommended = this.getRecommendedTopics();
        
        recommendedContainer.innerHTML = recommended.map(topic => `
            <div class="recommended-topic" data-topic-id="${topic.id}" onclick="topicsManager.startTopic('${topic.id}')">
                <span class="recommended-emoji">${topic.emoji}</span>
                <div class="recommended-content">
                    <span class="recommended-name">${topic.name}</span>
                    <span class="recommended-status">${topic.status.replace('_', ' ')}</span>
                </div>
            </div>
        `).join('');
    }

    // Reset current topic session
    resetCurrentTopic() {
        this.currentTopic = null;
        this.currentPhrases = [];
        this.currentPhraseIndex = 0;
    }
}
