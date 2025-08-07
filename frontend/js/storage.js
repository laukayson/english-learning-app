// Local Storage Management for Language Learning App

class Storage {
    constructor() {
        this.isAvailable = this.checkStorageAvailability();
        this.prefix = 'english_learning_';
    }

    checkStorageAvailability() {
        try {
            const test = '__storage_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (e) {
            console.warn('Local storage not available');
            return false;
        }
    }

    // Basic storage operations
    set(key, value) {
        if (!this.isAvailable) return false;
        
        try {
            const prefixedKey = this.prefix + key;
            const data = {
                value: value,
                timestamp: Date.now(),
                version: '1.0'
            };
            localStorage.setItem(prefixedKey, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Storage set error:', error);
            return false;
        }
    }

    get(key, defaultValue = null) {
        if (!this.isAvailable) return defaultValue;
        
        try {
            const prefixedKey = this.prefix + key;
            const storedData = localStorage.getItem(prefixedKey);
            
            if (!storedData) return defaultValue;
            
            const data = JSON.parse(storedData);
            return data.value;
        } catch (error) {
            console.error('Storage get error:', error);
            return defaultValue;
        }
    }

    remove(key) {
        if (!this.isAvailable) return false;
        
        try {
            const prefixedKey = this.prefix + key;
            localStorage.removeItem(prefixedKey);
            return true;
        } catch (error) {
            console.error('Storage remove error:', error);
            return false;
        }
    }

    clear() {
        if (!this.isAvailable) return false;
        
        try {
            const keys = Object.keys(localStorage);
            keys.forEach(key => {
                if (key.startsWith(this.prefix)) {
                    localStorage.removeItem(key);
                }
            });
            return true;
        } catch (error) {
            console.error('Storage clear error:', error);
            return false;
        }
    }

    // User profile management
    saveUserProfile(profile) {
        const success = this.set(CONFIG.STORAGE_KEYS.USER_PROFILE, profile);
        if (success) {
            Utils.log('User profile saved', profile);
        }
        return success;
    }

    getUserProfile() {
        return this.get(CONFIG.STORAGE_KEYS.USER_PROFILE);
    }

    clearUserProfile() {
        const success = this.remove(CONFIG.STORAGE_KEYS.USER_PROFILE);
        if (success) {
            Utils.log('User profile cleared');
        }
        return success;
    }

    // Alias for getUserProfile (for compatibility)
    getCurrentUser() {
        return this.getUserProfile();
    }

    updateUserProfile(updates) {
        const currentProfile = this.getUserProfile();
        if (currentProfile) {
            const updatedProfile = { ...currentProfile, ...updates };
            return this.saveUserProfile(updatedProfile);
        }
        return false;
    }

    // Progress tracking
    saveProgress(progress) {
        const success = this.set(CONFIG.STORAGE_KEYS.PROGRESS, progress);
        if (success) {
            Utils.log('Progress saved', progress);
        }
        return success;
    }

    getProgress() {
        return this.get(CONFIG.STORAGE_KEYS.PROGRESS, {
            topics_completed: [],
            total_phrases_learned: 0,
            practice_sessions: 0,
            current_streak: 0,
            last_activity_date: null,
            level_progress: {
                1: { completed: 0, total: 0 },
                2: { completed: 0, total: 0 },
                3: { completed: 0, total: 0 },
                4: { completed: 0, total: 0 }
            }
        });
    }

    updateProgress(updates) {
        const currentProgress = this.getProgress();
        const updatedProgress = { ...currentProgress, ...updates };
        
        // Update last activity date
        updatedProgress.last_activity_date = new Date().toISOString();
        
        return this.saveProgress(updatedProgress);
    }

    // Settings management
    saveSettings(settings) {
        const success = this.set(CONFIG.STORAGE_KEYS.SETTINGS, settings);
        if (success) {
            Utils.log('Settings saved', settings);
        }
        return success;
    }

    getSettings() {
        return this.get(CONFIG.STORAGE_KEYS.SETTINGS, {
            farsi_audio: true,
            visual_aids: true,
            pronunciation_check: true,
            voice_input: true,
            difficulty_level: 1,
            daily_goal: 3,
            notifications: true,
            sound_effects: true,
            auto_play_farsi: false
        });
    }

    updateSettings(updates) {
        const currentSettings = this.getSettings();
        const updatedSettings = { ...currentSettings, ...updates };
        return this.saveSettings(updatedSettings);
    }

    // Conversation history
    saveConversation(conversationId, conversation) {
        const history = this.getConversationHistory();
        history[conversationId] = {
            ...conversation,
            saved_at: new Date().toISOString()
        };
        
        // Keep only last 10 conversations
        const conversations = Object.entries(history);
        if (conversations.length > 10) {
            conversations.sort((a, b) => new Date(b[1].saved_at) - new Date(a[1].saved_at));
            const recentConversations = conversations.slice(0, 10);
            const trimmedHistory = Object.fromEntries(recentConversations);
            return this.set(CONFIG.STORAGE_KEYS.CONVERSATION_HISTORY, trimmedHistory);
        }
        
        return this.set(CONFIG.STORAGE_KEYS.CONVERSATION_HISTORY, history);
    }

    getConversationHistory() {
        return this.get(CONFIG.STORAGE_KEYS.CONVERSATION_HISTORY, {});
    }

    getConversation(conversationId) {
        const history = this.getConversationHistory();
        return history[conversationId] || null;
    }

    deleteConversation(conversationId) {
        const history = this.getConversationHistory();
        delete history[conversationId];
        return this.set(CONFIG.STORAGE_KEYS.CONVERSATION_HISTORY, history);
    }

    // Spaced repetition data
    saveSpacedRepetitionData(data) {
        return this.set(CONFIG.STORAGE_KEYS.SPACED_REPETITION_DATA, data);
    }

    getSpacedRepetitionData() {
        return this.get(CONFIG.STORAGE_KEYS.SPACED_REPETITION_DATA, {
            items: {},
            due_today: [],
            completed_today: []
        });
    }

    updateSpacedRepetitionItem(itemId, itemData) {
        const data = this.getSpacedRepetitionData();
        data.items[itemId] = itemData;
        return this.saveSpacedRepetitionData(data);
    }

    // Rate limiting data (client-side tracking)
    saveRateLimitData(data) {
        return this.set(CONFIG.STORAGE_KEYS.RATE_LIMIT_DATA, data);
    }

    getRateLimitData() {
        return this.get(CONFIG.STORAGE_KEYS.RATE_LIMIT_DATA, {
            last_reset: Date.now(),
            request_count: 0,
            requests_today: 0
        });
    }

    updateRateLimitData() {
        const data = this.getRateLimitData();
        const now = Date.now();
        const today = new Date().toDateString();
        const lastResetDate = new Date(data.last_reset).toDateString();
        
        // Reset daily count if it's a new day
        if (today !== lastResetDate) {
            data.requests_today = 0;
            data.last_reset = now;
        }
        
        data.request_count++;
        data.requests_today++;
        
        return this.saveRateLimitData(data);
    }

    // Offline data management
    saveOfflineData(key, data) {
        const offlineData = this.get('offline_data', {});
        offlineData[key] = {
            data: data,
            timestamp: Date.now(),
            synced: false
        };
        return this.set('offline_data', offlineData);
    }

    getOfflineData(key) {
        const offlineData = this.get('offline_data', {});
        return offlineData[key] || null;
    }

    getAllOfflineData() {
        return this.get('offline_data', {});
    }

    markOfflineDataSynced(key) {
        const offlineData = this.get('offline_data', {});
        if (offlineData[key]) {
            offlineData[key].synced = true;
            return this.set('offline_data', offlineData);
        }
        return false;
    }

    clearSyncedOfflineData() {
        const offlineData = this.get('offline_data', {});
        const unsyncedData = {};
        
        Object.entries(offlineData).forEach(([key, value]) => {
            if (!value.synced) {
                unsyncedData[key] = value;
            }
        });
        
        return this.set('offline_data', unsyncedData);
    }

    // Data export/import
    exportAllData() {
        if (!this.isAvailable) return null;
        
        try {
            const allData = {};
            const keys = Object.keys(localStorage);
            
            keys.forEach(key => {
                if (key.startsWith(this.prefix)) {
                    const cleanKey = key.replace(this.prefix, '');
                    allData[cleanKey] = this.get(cleanKey);
                }
            });
            
            return {
                version: '1.0',
                exported_at: new Date().toISOString(),
                data: allData
            };
        } catch (error) {
            console.error('Export error:', error);
            return null;
        }
    }

    importData(exportedData) {
        if (!exportedData || !exportedData.data) return false;
        
        try {
            Object.entries(exportedData.data).forEach(([key, value]) => {
                this.set(key, value);
            });
            
            Utils.log('Data imported successfully');
            return true;
        } catch (error) {
            console.error('Import error:', error);
            return false;
        }
    }

    // Storage statistics
    getStorageStats() {
        if (!this.isAvailable) {
            return {
                available: false,
                used: 0,
                total: 0,
                items: 0
            };
        }
        
        try {
            let totalSize = 0;
            let itemCount = 0;
            
            const keys = Object.keys(localStorage);
            keys.forEach(key => {
                if (key.startsWith(this.prefix)) {
                    const value = localStorage.getItem(key);
                    totalSize += new Blob([value]).size;
                    itemCount++;
                }
            });
            
            // Estimate total available space (5MB typical limit)
            const estimatedTotal = 5 * 1024 * 1024; // 5MB in bytes
            
            return {
                available: true,
                used: totalSize,
                total: estimatedTotal,
                used_percentage: (totalSize / estimatedTotal) * 100,
                items: itemCount,
                formatted_used: this.formatBytes(totalSize),
                formatted_total: this.formatBytes(estimatedTotal)
            };
        } catch (error) {
            console.error('Storage stats error:', error);
            return {
                available: true,
                used: 0,
                total: 0,
                items: 0,
                error: error.message
            };
        }
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Cleanup old data
    cleanup() {
        try {
            const cutoffDate = Date.now() - (30 * 24 * 60 * 60 * 1000); // 30 days ago
            
            // Clean old conversation history
            const history = this.getConversationHistory();
            const cleanedHistory = {};
            
            Object.entries(history).forEach(([id, conversation]) => {
                const savedAt = new Date(conversation.saved_at).getTime();
                if (savedAt > cutoffDate) {
                    cleanedHistory[id] = conversation;
                }
            });
            
            this.set(CONFIG.STORAGE_KEYS.CONVERSATION_HISTORY, cleanedHistory);
            
            // Clean old offline data
            this.clearSyncedOfflineData();
            
            Utils.log('Storage cleanup completed');
            return true;
        } catch (error) {
            console.error('Cleanup error:', error);
            return false;
        }
    }
}

// Create global storage instance
const storage = new Storage();
