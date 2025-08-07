// Progress Tracker for Language Learning App

class ProgressTracker {
    constructor() {
        this.progress = this.loadProgress();
        this.streakData = this.loadStreakData();
        this.spacedRepetitionData = this.loadSpacedRepetitionData();
    }

    loadProgress() {
        return storage.getProgress();
    }

    saveProgress() {
        return storage.saveProgress(this.progress);
    }

    loadStreakData() {
        const today = new Date().toDateString();
        const streakData = storage.get('streak_data', {
            current_streak: 0,
            longest_streak: 0,
            last_activity_date: null,
            streak_start_date: null
        });

        // Check if streak is broken
        if (streakData.last_activity_date) {
            const lastActivity = new Date(streakData.last_activity_date);
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);

            if (lastActivity.toDateString() !== today && 
                lastActivity.toDateString() !== yesterday.toDateString()) {
                // Streak is broken
                streakData.current_streak = 0;
                streakData.streak_start_date = null;
            }
        }

        return streakData;
    }

    saveStreakData() {
        return storage.set('streak_data', this.streakData);
    }

    loadSpacedRepetitionData() {
        return storage.getSpacedRepetitionData();
    }

    saveSpacedRepetitionData() {
        return storage.saveSpacedRepetitionData(this.spacedRepetitionData);
    }

    // Initialise progress for a new user
    initialiseProgress(user) {
        const userLevel = user.level;
        const topics = CONFIG.LEVELS[userLevel]?.topics || [];

        this.progress = {
            user_id: user.id,
            level: userLevel,
            topics_completed: [],
            topics_in_progress: [],
            total_phrases_learned: 0,
            phrases_learned_today: 0,
            practice_sessions: 0,
            current_streak: 0,
            longest_streak: 0,
            last_activity_date: new Date().toISOString(),
            created_at: new Date().toISOString(),
            level_progress: this.initialiseLevelProgress(topics),
            daily_goals: {
                phrases: 3,
                practice_time: 15 // minutes
            },
            achievements: [],
            total_study_time: 0, // minutes
            conversation_count: 0,
            pronunciation_scores: []
        };

        this.saveProgress();
        Utils.log('Progress initialised for user', user);
    }

    initialiseLevelProgress(topics) {
        const levelProgress = {};
        
        topics.forEach(topicId => {
            levelProgress[topicId] = {
                status: 'not_started', // not_started, in_progress, completed
                phrases_learned: 0,
                conversations_completed: 0,
                last_practiced: null,
                completion_date: null,
                difficulty_rating: null,
                practice_sessions: 0
            };
        });

        return levelProgress;
    }

    // Update progress for various activities
    updateConversationProgress(topicId) {
        if (!this.progress.level_progress[topicId]) {
            this.progress.level_progress[topicId] = {
                status: 'in_progress',
                phrases_learned: 0,
                conversations_completed: 0,
                last_practiced: null,
                completion_date: null,
                practice_sessions: 0
            };
        }

        const topicProgress = this.progress.level_progress[topicId];
        topicProgress.conversations_completed++;
        topicProgress.last_practiced = new Date().toISOString();
        topicProgress.practice_sessions++;

        if (topicProgress.status === 'not_started') {
            topicProgress.status = 'in_progress';
            this.progress.topics_in_progress.push(topicId);
        }

        this.progress.conversation_count++;
        this.updateActivityStreak();
        this.saveProgress();

        Utils.log('Conversation progress updated', { topicId, topicProgress });
    }

    updatePhrasesLearned(count = 1, topicId = null) {
        this.progress.total_phrases_learned += count;
        this.progress.phrases_learned_today += count;

        if (topicId && this.progress.level_progress[topicId]) {
            this.progress.level_progress[topicId].phrases_learned += count;
        }

        this.updateActivityStreak();
        this.checkDailyGoal();
        this.saveProgress();

        Utils.log('Phrases learned updated', { count, topicId, total: this.progress.total_phrases_learned });
    }

    completeTopic(topicId) {
        const topicProgress = this.progress.level_progress[topicId];
        if (!topicProgress) return;

        topicProgress.status = 'completed';
        topicProgress.completion_date = new Date().toISOString();

        // Remove from in_progress and add to completed
        const inProgressIndex = this.progress.topics_in_progress.indexOf(topicId);
        if (inProgressIndex > -1) {
            this.progress.topics_in_progress.splice(inProgressIndex, 1);
        }

        if (!this.progress.topics_completed.includes(topicId)) {
            this.progress.topics_completed.push(topicId);
        }

        // Add achievement
        this.addAchievement('topic_completed', {
            topic: topicId,
            date: new Date().toISOString()
        });

        // Check if level is completed
        this.checkLevelCompletion();

        this.saveProgress();
        Utils.log('Topic completed', topicId);
    }

    updatePronunciationScore(score, phrase) {
        this.progress.pronunciation_scores.push({
            score: score,
            phrase: phrase,
            date: new Date().toISOString()
        });

        // Keep only last 50 scores
        if (this.progress.pronunciation_scores.length > 50) {
            this.progress.pronunciation_scores = this.progress.pronunciation_scores.slice(-50);
        }

        this.saveProgress();
    }

    updateStudyTime(minutes) {
        this.progress.total_study_time += minutes;
        this.updateActivityStreak();
        this.saveProgress();
    }

    updateActivityStreak() {
        const today = new Date().toDateString();
        const lastActivity = this.streakData.last_activity_date;

        if (!lastActivity || new Date(lastActivity).toDateString() !== today) {
            // First activity today
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);

            if (lastActivity && new Date(lastActivity).toDateString() === yesterday.toDateString()) {
                // Continue streak
                this.streakData.current_streak++;
            } else {
                // Start new streak
                this.streakData.current_streak = 1;
                this.streakData.streak_start_date = today;
            }

            this.streakData.last_activity_date = new Date().toISOString();

            // Update longest streak
            if (this.streakData.current_streak > this.streakData.longest_streak) {
                this.streakData.longest_streak = this.streakData.current_streak;
                
                // Add achievement for long streaks
                if (this.streakData.current_streak === 7) {
                    this.addAchievement('week_streak', { streak: 7 });
                } else if (this.streakData.current_streak === 30) {
                    this.addAchievement('month_streak', { streak: 30 });
                }
            }

            this.progress.current_streak = this.streakData.current_streak;
            this.progress.longest_streak = this.streakData.longest_streak;

            this.saveStreakData();
        }
    }

    checkDailyGoal() {
        const dailyGoal = this.progress.daily_goals.phrases;
        
        if (this.progress.phrases_learned_today >= dailyGoal) {
            this.addAchievement('daily_goal_met', {
                goal: dailyGoal,
                achieved: this.progress.phrases_learned_today,
                date: new Date().toISOString()
            });
        }
    }

    checkLevelCompletion() {
        const currentLevel = this.progress.level;
        const levelTopics = CONFIG.LEVELS[currentLevel]?.topics || [];
        const completedTopics = this.progress.topics_completed;

        const levelCompleted = levelTopics.every(topic => completedTopics.includes(topic));
        
        if (levelCompleted) {
            this.addAchievement('level_completed', {
                level: currentLevel,
                date: new Date().toISOString()
            });

            Utils.showNotification(`🎉 Congratulations! You completed Level ${currentLevel}!`, 'success');
        }
    }

    addAchievement(type, data) {
        const achievement = {
            id: Date.now().toString(),
            type: type,
            data: data,
            earned_at: new Date().toISOString()
        };

        this.progress.achievements.push(achievement);
        
        // Show achievement notification
        const achievementConfig = CONFIG.GAMIFICATION_CONFIG.badges[type];
        if (achievementConfig) {
            Utils.showNotification(
                `🏆 Achievement unlocked: ${achievementConfig.name}`, 
                'success'
            );
        }

        this.saveProgress();
        Utils.log('Achievement added', achievement);
    }

    // Spaced repetition system
    addSpacedRepetitionItem(phrase, translation, topicId) {
        const itemId = `${topicId}_${Date.now()}`;
        const now = new Date();
        
        const item = {
            id: itemId,
            phrase: phrase,
            translation: translation,
            topic: topicId,
            interval: CONFIG.SPACED_REPETITION.INITIAL_INTERVAL,
            repetitions: 0,
            ease_factor: CONFIG.SPACED_REPETITION.EASY_FACTOR,
            next_review: new Date(now.getTime() + (CONFIG.SPACED_REPETITION.INITIAL_INTERVAL * 24 * 60 * 60 * 1000)),
            created_at: now.toISOString(),
            last_reviewed: null
        };

        this.spacedRepetitionData.items[itemId] = item;
        this.saveSpacedRepetitionData();

        return itemId;
    }

    updateSpacedRepetitionItem(itemId, quality) {
        const item = this.spacedRepetitionData.items[itemId];
        if (!item) return;

        const now = new Date();
        item.last_reviewed = now.toISOString();
        item.repetitions++;

        // SM-2 Algorithm
        if (quality >= 3) {
            if (item.repetitions === 1) {
                item.interval = 1;
            } else if (item.repetitions === 2) {
                item.interval = 6;
            } else {
                item.interval = Math.round(item.interval * item.ease_factor);
            }
        } else {
            item.repetitions = 0;
            item.interval = 1;
        }

        item.ease_factor = Math.max(
            CONFIG.SPACED_REPETITION.MIN_FACTOR,
            item.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        );

        item.next_review = new Date(now.getTime() + (item.interval * 24 * 60 * 60 * 1000));

        this.saveSpacedRepetitionData();
    }

    getDueSpacedRepetitionItems() {
        const now = new Date();
        const dueItems = [];

        Object.values(this.spacedRepetitionData.items).forEach(item => {
            if (new Date(item.next_review) <= now) {
                dueItems.push(item);
            }
        });

        return dueItems.sort((a, b) => new Date(a.next_review) - new Date(b.next_review));
    }

    // Analytics and statistics
    getProgress() {
        return this.progress;
    }

    async fetchUserLevelInfo(userId) {
        try {
            const response = await fetch(`/api/user-level-info/${userId}`);
            if (response.ok) {
                const levelInfo = await response.json();
                return levelInfo;
            }
        } catch (error) {
            console.error('Error fetching user level info:', error);
        }
        return null;
    }

    async updateProgressDisplay() {
        const currentUser = storage.getCurrentUser();
        if (!currentUser) return;

        const levelInfo = await this.fetchUserLevelInfo(currentUser.id);
        if (levelInfo) {
            this.displayLevelInfo(levelInfo);
        }
    }

    displayLevelInfo(levelInfo) {
        // Update level badge
        const levelBadge = document.querySelector('.level-badge');
        if (levelBadge) {
            levelBadge.textContent = `Level ${levelInfo.level}`;
        }

        // Update XP bar
        const xpFill = document.querySelector('.xp-fill');
        const xpText = document.querySelector('.xp-text');
        if (xpFill && xpText) {
            const percentage = (levelInfo.current_xp / levelInfo.xp_to_next_level) * 100;
            xpFill.style.width = `${percentage}%`;
            xpText.textContent = `${levelInfo.current_xp} / ${levelInfo.xp_to_next_level} XP`;
        }

        // Update total XP display
        const totalXpElement = document.querySelector('.total-xp');
        if (totalXpElement) {
            totalXpElement.textContent = `Total XP: ${levelInfo.total_experience}`;
        }
    }

    getStreakData() {
        return this.streakData;
    }

    getTopicProgress(topicId) {
        return this.progress.level_progress[topicId] || null;
    }

    getLevelProgress() {
        const currentLevel = this.progress.level;
        const levelTopics = CONFIG.LEVELS[currentLevel]?.topics || [];
        const completed = this.progress.topics_completed.filter(topic => levelTopics.includes(topic)).length;
        
        return {
            level: currentLevel,
            completed: completed,
            total: levelTopics.length,
            percentage: levelTopics.length > 0 ? Math.round((completed / levelTopics.length) * 100) : 0
        };
    }

    getStudyStatistics() {
        const now = new Date();
        const weekAgo = new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000));
        const monthAgo = new Date(now.getTime() - (30 * 24 * 60 * 60 * 1000));

        return {
            total_study_time: this.progress.total_study_time,
            total_phrases: this.progress.total_phrases_learned,
            current_streak: this.progress.current_streak,
            longest_streak: this.progress.longest_streak,
            level_progress: this.getLevelProgress(),
            achievements_count: this.progress.achievements.length,
            average_pronunciation_score: this.getAveragePronunciationScore(),
            topics_completed: this.progress.topics_completed.length,
            conversations_completed: this.progress.conversation_count
        };
    }

    getAveragePronunciationScore() {
        const scores = this.progress.pronunciation_scores;
        if (scores.length === 0) return 0;
        
        const sum = scores.reduce((total, item) => total + item.score, 0);
        return Math.round(sum / scores.length);
    }

    // Reset daily progress (called at midnight)
    resetDailyProgress() {
        this.progress.phrases_learned_today = 0;
        this.saveProgress();
        Utils.log('Daily progress reset');
    }

    // Export progress data
    exportProgress() {
        return {
            progress: this.progress,
            streak_data: this.streakData,
            spaced_repetition: this.spacedRepetitionData,
            exported_at: new Date().toISOString()
        };
    }

    // Import progress data
    importProgress(data) {
        if (data.progress) {
            this.progress = data.progress;
            this.saveProgress();
        }
        
        if (data.streak_data) {
            this.streakData = data.streak_data;
            this.saveStreakData();
        }
        
        if (data.spaced_repetition) {
            this.spacedRepetitionData = data.spaced_repetition;
            this.saveSpacedRepetitionData();
        }

        Utils.log('Progress data imported');
    }
}
