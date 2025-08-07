# Progress Tracking Service for Language Learning App

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ProgressTracker:
    # Experience Point System Constants
    XP_REWARDS = {
        'conversation_message': 5,          # Per message sent in conversation
        'conversation_complete': 25,        # Complete a conversation
        'phrase_learned': 10,              # Learn a new phrase
        'topic_started': 15,               # Start a new topic
        'topic_completed': 100,            # Complete a topic
        'daily_login': 10,                 # First login of the day
        'streak_bonus': 20,                # Daily streak bonus (multiplied by streak)
        'voice_message': 8,                # Use voice input
        'correct_pronunciation': 12,        # Good pronunciation score
        'help_other': 5,                   # Use help features (shows engagement)
    }
    
    # Level progression: XP needed for each level (cumulative)
    LEVEL_XP_REQUIREMENTS = [
        0,      # Level 1 (starting level)
        100,    # Level 2 (100 XP total)
        250,    # Level 3 (250 XP total)
        450,    # Level 4 (450 XP total)
        700,    # Level 5 (700 XP total)
        1000,   # Level 6 (1000 XP total)
        1400,   # Level 7 (1400 XP total)
        1900,   # Level 8 (1900 XP total)
        2500,   # Level 9 (2500 XP total)
        3200,   # Level 10 (3200 XP total)
        4000,   # Level 11 (4000 XP total)
        4900,   # Level 12 (4900 XP total)
        5900,   # Level 13 (5900 XP total)
        7000,   # Level 14 (7000 XP total)
        8200,   # Level 15 (8200 XP total)
        9500,   # Level 16 (9500 XP total)
        11000,  # Level 17 (11000 XP total)
        12700,  # Level 18 (12700 XP total)
        14600,  # Level 19 (14600 XP total)
        16700,  # Level 20 (16700 XP total)
    ]
    
    # Generate higher levels dynamically
    @classmethod
    def get_xp_for_level(cls, level: int) -> int:
        """Get XP requirement for a specific level"""
        if level <= 1:
            return 0
        elif level <= len(cls.LEVEL_XP_REQUIREMENTS):
            return cls.LEVEL_XP_REQUIREMENTS[level - 1]
        else:
            # For levels beyond 20, use an exponential formula
            base_xp = cls.LEVEL_XP_REQUIREMENTS[-1]
            additional_levels = level - len(cls.LEVEL_XP_REQUIREMENTS)
            # Each additional level requires 20% more XP than the previous level
            additional_xp = 0
            last_level_requirement = cls.LEVEL_XP_REQUIREMENTS[-1] - cls.LEVEL_XP_REQUIREMENTS[-2]
            
            for i in range(additional_levels):
                last_level_requirement = int(last_level_requirement * 1.2)
                additional_xp += last_level_requirement
            
            return base_xp + additional_xp
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the progress tracking database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # User progress table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_progress (
                        user_id TEXT PRIMARY KEY,
                        level INTEGER NOT NULL,
                        experience_points INTEGER DEFAULT 0,
                        total_experience INTEGER DEFAULT 0,
                        topics_completed TEXT DEFAULT '[]',
                        topics_in_progress TEXT DEFAULT '[]',
                        total_phrases_learned INTEGER DEFAULT 0,
                        phrases_learned_today INTEGER DEFAULT 0,
                        practice_sessions INTEGER DEFAULT 0,
                        current_streak INTEGER DEFAULT 0,
                        longest_streak INTEGER DEFAULT 0,
                        last_activity_date TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        level_progress TEXT DEFAULT '{}',
                        daily_goals TEXT DEFAULT '{"phrases": 3, "practice_time": 15}',
                        achievements TEXT DEFAULT '[]',
                        total_study_time INTEGER DEFAULT 0,
                        conversation_count INTEGER DEFAULT 0
                    )
                ''')
                
                # Add XP columns if they don't exist (for existing databases)
                try:
                    cursor.execute('ALTER TABLE user_progress ADD COLUMN experience_points INTEGER DEFAULT 0')
                except sqlite3.OperationalError:
                    pass  # Column already exists
                
                try:
                    cursor.execute('ALTER TABLE user_progress ADD COLUMN total_experience INTEGER DEFAULT 0')
                except sqlite3.OperationalError:
                    pass  # Column already exists
                
                # Topic progress table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS topic_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        topic_id TEXT NOT NULL,
                        status TEXT DEFAULT 'not_started',
                        phrases_learned INTEGER DEFAULT 0,
                        conversations_completed INTEGER DEFAULT 0,
                        last_practiced TEXT,
                        completion_date TEXT,
                        difficulty_rating INTEGER,
                        practice_sessions INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        UNIQUE(user_id, topic_id)
                    )
                ''')
                
                # Spaced repetition table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS spaced_repetition (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        phrase TEXT NOT NULL,
                        translation TEXT NOT NULL,
                        topic_id TEXT NOT NULL,
                        interval_days INTEGER DEFAULT 1,
                        repetitions INTEGER DEFAULT 0,
                        ease_factor REAL DEFAULT 2.5,
                        next_review TEXT NOT NULL,
                        last_reviewed TEXT,
                        created_at TEXT NOT NULL,
                        quality_history TEXT DEFAULT '[]'
                    )
                ''')
                
                # Learning sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        topic_id TEXT,
                        session_type TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        duration_minutes INTEGER,
                        phrases_practiced INTEGER DEFAULT 0,
                        conversations_completed INTEGER DEFAULT 0,
                        pronunciation_scores TEXT DEFAULT '[]',
                        session_data TEXT DEFAULT '{}',
                        created_at TEXT NOT NULL
                    )
                ''')
                
                # Daily statistics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS daily_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        date TEXT NOT NULL,
                        phrases_learned INTEGER DEFAULT 0,
                        study_time_minutes INTEGER DEFAULT 0,
                        conversations_completed INTEGER DEFAULT 0,
                        practice_sessions INTEGER DEFAULT 0,
                        topics_practiced TEXT DEFAULT '[]',
                        streak_day BOOLEAN DEFAULT FALSE,
                        login_count INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        UNIQUE(user_id, date)
                    )
                ''')
                
                # Add login_count column if it doesn't exist (for existing databases)
                try:
                    cursor.execute('ALTER TABLE daily_stats ADD COLUMN login_count INTEGER DEFAULT 0')
                except sqlite3.OperationalError:
                    pass  # Column already exists
                
                # Pronunciation scores table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS pronunciation_scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        phrase TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        topic_id TEXT,
                        session_id INTEGER,
                        recorded_at TEXT NOT NULL,
                        audio_data TEXT
                    )
                ''')

                conn.commit()
                logger.info("Progress tracking database initialized successfully")

        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise

    def initialize_user_progress(self, user_id: str, level: int) -> bool:
        """Initialize progress tracking for a new user"""
        try:
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO user_progress 
                    (user_id, level, created_at, updated_at, last_activity_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, level, now, now, now))
                
                conn.commit()
                logger.info(f"Progress initialized for user: {user_id}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error initializing user progress: {str(e)}")
            return False

    def add_experience_points(self, user_id: str, action: str, multiplier: int = 1) -> Dict[str, Any]:
        """
        Add experience points for a user action and handle level ups
        
        Args:
            user_id: User identifier
            action: Action type (key from XP_REWARDS)
            multiplier: Multiplier for the XP (for streaks, etc.)
        
        Returns:
            Dict with XP gained, new level info, and whether user leveled up
        """
        try:
            if action not in self.XP_REWARDS:
                logger.warning(f"Unknown XP action: {action}")
                return {'xp_gained': 0, 'level_up': False}
            
            xp_gained = self.XP_REWARDS[action] * multiplier
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current user stats
                cursor.execute('''
                    SELECT level, experience_points, total_experience 
                    FROM user_progress 
                    WHERE user_id = ?
                ''', (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    logger.error(f"User {user_id} not found for XP update")
                    return {'xp_gained': 0, 'level_up': False}
                
                current_level, current_xp, total_xp = result
                new_current_xp = current_xp + xp_gained
                new_total_xp = total_xp + xp_gained
                
                # Check for level up
                new_level = current_level
                level_up = False
                
                while new_level < 100:  # Cap at level 100
                    next_level_requirement = self.get_xp_for_level(new_level + 1)
                    if new_total_xp >= next_level_requirement:
                        new_level += 1
                        level_up = True
                    else:
                        break
                
                # If leveled up, reset current XP relative to new level
                if level_up:
                    current_level_requirement = self.get_xp_for_level(new_level)
                    new_current_xp = new_total_xp - current_level_requirement
                
                # Update database
                cursor.execute('''
                    UPDATE user_progress 
                    SET level = ?, 
                        experience_points = ?, 
                        total_experience = ?,
                        updated_at = ?
                    WHERE user_id = ?
                ''', (new_level, new_current_xp, new_total_xp, datetime.now().isoformat(), user_id))
                
                # Calculate next level XP requirement
                next_level_xp = self.get_xp_for_level(new_level + 1) - self.get_xp_for_level(new_level)
                
                return {
                    'xp_gained': xp_gained,
                    'level_up': level_up,
                    'old_level': current_level,
                    'new_level': new_level,
                    'current_xp': new_current_xp,
                    'next_level_xp': next_level_xp,
                    'total_xp': new_total_xp,
                    'action': action
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error adding XP for user {user_id}: {str(e)}")
            return {'xp_gained': 0, 'level_up': False, 'error': str(e)}

    def get_user_level_info(self, user_id: str) -> Dict[str, Any]:
        """Get detailed level and XP information for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT level, experience_points, total_experience, topics_completed, current_streak
                    FROM user_progress 
                    WHERE user_id = ?
                ''', (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return {
                        'level': 1,
                        'current_xp': 0,
                        'next_level_xp': self.get_xp_for_level(2),
                        'total_xp': 0,
                        'xp_progress_percent': 0,
                        'topics_completed': 0,
                        'current_streak': 0
                    }
                
                level, current_xp, total_xp, topics_completed_str, current_streak = result
                
                # Parse topics completed
                try:
                    topics_completed = len(json.loads(topics_completed_str or '[]'))
                except:
                    topics_completed = 0
                
                # Calculate XP needed for next level
                current_level_total_xp = self.get_xp_for_level(level)
                next_level_total_xp = self.get_xp_for_level(level + 1)
                xp_needed_for_next = next_level_total_xp - current_level_total_xp
                
                # Current XP in this level (should be total_xp - current_level_total_xp)
                current_level_xp = total_xp - current_level_total_xp
                
                # Calculate progress percentage
                xp_progress_percent = (current_level_xp / xp_needed_for_next * 100) if xp_needed_for_next > 0 else 100
                
                return {
                    'level': level,
                    'current_xp': current_level_xp,
                    'next_level_xp': xp_needed_for_next,
                    'total_xp': total_xp,
                    'xp_progress_percent': min(100, max(0, xp_progress_percent)),
                    'topics_completed': topics_completed,
                    'current_streak': current_streak or 0
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error getting level info for user {user_id}: {str(e)}")
            return {
                'level': 1,
                'current_xp': 0,
                'next_level_xp': 100,
                'total_xp': 0,
                'xp_progress_percent': 0
            }

    def update_conversation_progress(self, user_id: str, topic_id: str) -> bool:
        """Update progress when user completes a conversation"""
        try:
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update topic progress
                cursor.execute('''
                    INSERT OR REPLACE INTO topic_progress 
                    (user_id, topic_id, status, conversations_completed, last_practiced, 
                     practice_sessions, created_at, updated_at)
                    VALUES (?, ?, 'in_progress', 
                            COALESCE((SELECT conversations_completed FROM topic_progress 
                                     WHERE user_id = ? AND topic_id = ?), 0) + 1,
                            ?, 
                            COALESCE((SELECT practice_sessions FROM topic_progress 
                                     WHERE user_id = ? AND topic_id = ?), 0) + 1,
                            COALESCE((SELECT created_at FROM topic_progress 
                                     WHERE user_id = ? AND topic_id = ?), ?),
                            ?)
                ''', (user_id, topic_id, user_id, topic_id, now, 
                      user_id, topic_id, user_id, topic_id, now, now))
                
                # Update user progress
                cursor.execute('''
                    UPDATE user_progress 
                    SET conversation_count = conversation_count + 1,
                        last_activity_date = ?,
                        updated_at = ?
                    WHERE user_id = ?
                ''', (now, now, user_id))
                
                # Update daily stats
                today = datetime.now().date().isoformat()
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_stats 
                    (user_id, date, conversations_completed, created_at)
                    VALUES (?, ?, 
                            COALESCE((SELECT conversations_completed FROM daily_stats 
                                     WHERE user_id = ? AND date = ?), 0) + 1,
                            ?)
                ''', (user_id, today, user_id, today, now))
                
                conn.commit()
                
                # Award XP for completing conversation
                self.add_experience_points(user_id, 'conversation_complete')
                
                # Check if topic should be auto-completed
                self.check_and_auto_complete_topic(user_id, topic_id)
                
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error updating conversation progress: {str(e)}")
            return False

    def update_phrases_learned(self, user_id: str, count: int = 1, topic_id: str = None) -> bool:
        """Update phrases learned count"""
        try:
            now = datetime.now().isoformat()
            today = datetime.now().date().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update user progress
                cursor.execute('''
                    UPDATE user_progress 
                    SET total_phrases_learned = total_phrases_learned + ?,
                        phrases_learned_today = phrases_learned_today + ?,
                        last_activity_date = ?,
                        updated_at = ?
                    WHERE user_id = ?
                ''', (count, count, now, now, user_id))
                
                # Update topic progress if topic specified
                if topic_id:
                    cursor.execute('''
                        INSERT OR REPLACE INTO topic_progress 
                        (user_id, topic_id, phrases_learned, created_at, updated_at)
                        VALUES (?, ?, 
                                COALESCE((SELECT phrases_learned FROM topic_progress 
                                         WHERE user_id = ? AND topic_id = ?), 0) + ?,
                                COALESCE((SELECT created_at FROM topic_progress 
                                         WHERE user_id = ? AND topic_id = ?), ?),
                                ?)
                    ''', (user_id, topic_id, user_id, topic_id, count, 
                          user_id, topic_id, now, now))
                
                # Update daily stats
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_stats 
                    (user_id, date, phrases_learned, created_at)
                    VALUES (?, ?, 
                            COALESCE((SELECT phrases_learned FROM daily_stats 
                                     WHERE user_id = ? AND date = ?), 0) + ?,
                            ?)
                ''', (user_id, today, user_id, today, count, now))
                
                conn.commit()
                
                # Award XP for learning phrases
                for _ in range(count):
                    self.add_experience_points(user_id, 'phrase_learned')
                
                # Check if topic should be auto-completed (if topic specified)
                if topic_id:
                    self.check_and_auto_complete_topic(user_id, topic_id)
                
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error updating phrases learned: {str(e)}")
            return False

    def complete_topic(self, user_id: str, topic_id: str) -> bool:
        """Mark a topic as completed"""
        try:
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update topic progress
                cursor.execute('''
                    UPDATE topic_progress 
                    SET status = 'completed',
                        completion_date = ?,
                        updated_at = ?
                    WHERE user_id = ? AND topic_id = ?
                ''', (now, now, user_id, topic_id))
                
                # Update user progress topics_completed
                cursor.execute('''
                    SELECT topics_completed FROM user_progress WHERE user_id = ?
                ''', (user_id,))
                
                result = cursor.fetchone()
                if result:
                    completed_topics = json.loads(result[0] or '[]')
                    if topic_id not in completed_topics:
                        completed_topics.append(topic_id)
                        
                        cursor.execute('''
                            UPDATE user_progress 
                            SET topics_completed = ?, updated_at = ?
                            WHERE user_id = ?
                        ''', (json.dumps(completed_topics), now, user_id))
                        
                        # Award XP for completing topic
                        self.add_experience_points(user_id, 'topic_completed')
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error completing topic: {str(e)}")
            return False

    def check_and_auto_complete_topic(self, user_id: str, topic_id: str) -> bool:
        """Check if a topic should be auto-completed based on activity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current topic progress
                cursor.execute('''
                    SELECT conversations_completed, phrases_learned, practice_sessions, status
                    FROM topic_progress 
                    WHERE user_id = ? AND topic_id = ?
                ''', (user_id, topic_id))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                conversations, phrases, sessions, status = result
                
                # Don't auto-complete if already completed
                if status == 'completed':
                    return False
                
                # Topic completion criteria
                # Complete if user has:
                # - At least 3 conversations in the topic AND
                # - At least 5 practice sessions AND
                # - At least 8 phrases learned
                completion_criteria = {
                    'min_conversations': 3,
                    'min_sessions': 5,
                    'min_phrases': 8
                }
                
                if (conversations >= completion_criteria['min_conversations'] and
                    sessions >= completion_criteria['min_sessions'] and
                    phrases >= completion_criteria['min_phrases']):
                    
                    logger.info(f"Auto-completing topic {topic_id} for user {user_id}")
                    logger.info(f"Criteria met: {conversations} conversations, {sessions} sessions, {phrases} phrases")
                    
                    return self.complete_topic(user_id, topic_id)
                
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Error checking topic completion: {str(e)}")
            return False

    def add_spaced_repetition_item(self, user_id: str, phrase: str, translation: str, 
                                  topic_id: str, item_id: str = None) -> str:
        """Add item to spaced repetition system"""
        try:
            if not item_id:
                item_id = f"{user_id}_{topic_id}_{hash(phrase)}_{datetime.now().timestamp()}"
            
            now = datetime.now().isoformat()
            next_review = (datetime.now() + timedelta(days=1)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO spaced_repetition 
                    (id, user_id, phrase, translation, topic_id, next_review, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (item_id, user_id, phrase, translation, topic_id, next_review, now))
                
                conn.commit()
                return item_id
                
        except sqlite3.Error as e:
            logger.error(f"Error adding spaced repetition item: {str(e)}")
            return None

    def update_spaced_repetition_item(self, item_id: str, quality: int) -> bool:
        """Update spaced repetition item based on quality (SM-2 algorithm)"""
        try:
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current item data
                cursor.execute('''
                    SELECT interval_days, repetitions, ease_factor, quality_history 
                    FROM spaced_repetition WHERE id = ?
                ''', (item_id,))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                interval, repetitions, ease_factor, quality_history = result
                quality_hist = json.loads(quality_history or '[]')
                quality_hist.append(quality)
                
                # SM-2 Algorithm implementation
                if quality >= 3:
                    if repetitions == 0:
                        interval = 1
                    elif repetitions == 1:
                        interval = 6
                    else:
                        interval = int(interval * ease_factor)
                    repetitions += 1
                else:
                    repetitions = 0
                    interval = 1
                
                # Update ease factor
                ease_factor = max(1.3, ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
                
                # Calculate next review date
                next_review = (datetime.now() + timedelta(days=interval)).isoformat()
                
                # Update database
                cursor.execute('''
                    UPDATE spaced_repetition 
                    SET interval_days = ?, repetitions = ?, ease_factor = ?,
                        next_review = ?, last_reviewed = ?, quality_history = ?
                    WHERE id = ?
                ''', (interval, repetitions, ease_factor, next_review, now, 
                          json.dumps(quality_hist), item_id))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error updating spaced repetition item: {str(e)}")
            return False

    def get_due_spaced_repetition_items(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get items due for spaced repetition review"""
        try:
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, phrase, translation, topic_id, interval_days, 
                           repetitions, next_review, last_reviewed
                    FROM spaced_repetition 
                    WHERE user_id = ? AND next_review <= ?
                    ORDER BY next_review ASC
                    LIMIT ?
                ''', (user_id, now, limit))
                
                items = []
                for row in cursor.fetchall():
                    items.append({
                        'id': row[0],
                        'phrase': row[1],
                        'translation': row[2],
                        'topic_id': row[3],
                        'interval_days': row[4],
                        'repetitions': row[5],
                        'next_review': row[6],
                        'last_reviewed': row[7]
                    })
                
                return items
                
        except sqlite3.Error as e:
            logger.error(f"Error getting due spaced repetition items: {str(e)}")
            return []

    def update_study_time(self, user_id: str, minutes: int) -> bool:
        """Update total study time"""
        try:
            now = datetime.now().isoformat()
            today = datetime.now().date().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update user progress
                cursor.execute('''
                    UPDATE user_progress 
                    SET total_study_time = total_study_time + ?,
                        last_activity_date = ?,
                        updated_at = ?
                    WHERE user_id = ?
                ''', (minutes, now, now, user_id))
                
                # Update daily stats
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_stats 
                    (user_id, date, study_time_minutes, created_at)
                    VALUES (?, ?, 
                            COALESCE((SELECT study_time_minutes FROM daily_stats 
                                     WHERE user_id = ? AND date = ?), 0) + ?,
                            ?)
                ''', (user_id, today, user_id, today, minutes, now))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error updating study time: {str(e)}")
            return False

    def add_pronunciation_score(self, user_id: str, phrase: str, score: int, 
                               topic_id: str = None, session_id: int = None) -> bool:
        """Add pronunciation score"""
        try:
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO pronunciation_scores 
                    (user_id, phrase, score, topic_id, session_id, recorded_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, phrase, score, topic_id, session_id, now))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error adding pronunciation score: {str(e)}")
            return False

    def get_user_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive user progress data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get main progress data
                cursor.execute('''
                    SELECT * FROM user_progress WHERE user_id = ?
                ''', (user_id,))
                
                progress_row = cursor.fetchone()
                if not progress_row:
                    return None
                
                # Get column names
                cursor.execute("PRAGMA table_info(user_progress)")
                columns = [column[1] for column in cursor.fetchall()]
                
                progress = dict(zip(columns, progress_row))
                
                # Parse JSON fields
                progress['topics_completed'] = json.loads(progress.get('topics_completed', '[]'))
                progress['topics_in_progress'] = json.loads(progress.get('topics_in_progress', '[]'))
                progress['level_progress'] = json.loads(progress.get('level_progress', '{}'))
                progress['daily_goals'] = json.loads(progress.get('daily_goals', '{"phrases": 3, "practice_time": 15}'))
                progress['achievements'] = json.loads(progress.get('achievements', '[]'))
                
                # Get topic progress details
                cursor.execute('''
                    SELECT topic_id, status, phrases_learned, conversations_completed,
                           last_practiced, completion_date, practice_sessions
                    FROM topic_progress WHERE user_id = ?
                ''', (user_id,))
                
                topic_details = {}
                for row in cursor.fetchall():
                    topic_details[row[0]] = {
                        'status': row[1],
                        'phrases_learned': row[2],
                        'conversations_completed': row[3],
                        'last_practiced': row[4],
                        'completion_date': row[5],
                        'practice_sessions': row[6]
                    }
                
                progress['topic_details'] = topic_details
                
                # Get recent pronunciation scores
                cursor.execute('''
                    SELECT phrase, score, recorded_at 
                    FROM pronunciation_scores 
                    WHERE user_id = ? 
                    ORDER BY recorded_at DESC 
                    LIMIT 10
                ''', (user_id,))
                
                progress['recent_pronunciation_scores'] = [
                    {'phrase': row[0], 'score': row[1], 'recorded_at': row[2]}
                    for row in cursor.fetchall()
                ]
                
                return progress
                
        except sqlite3.Error as e:
            logger.error(f"Error getting user progress: {str(e)}")
            return None

    def get_daily_statistics(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily statistics for the last N days"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days-1)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT date, phrases_learned, study_time_minutes, 
                           conversations_completed, practice_sessions
                    FROM daily_stats 
                    WHERE user_id = ? AND date >= ? AND date <= ?
                    ORDER BY date DESC
                ''', (user_id, start_date.isoformat(), end_date.isoformat()))
                
                stats = []
                for row in cursor.fetchall():
                    stats.append({
                        'date': row[0],
                        'phrases_learned': row[1],
                        'study_time_minutes': row[2],
                        'conversations_completed': row[3],
                        'practice_sessions': row[4]
                    })
                
                return stats
                
        except sqlite3.Error as e:
            logger.error(f"Error getting daily statistics: {str(e)}")
            return []

    def update_activity_streak(self, user_id: str) -> Dict[str, int]:
        """Update activity-based streak (for learning activities, not login)"""
        # This method tracks activity streaks (conversations, phrases learned, etc.)
        # Not used for login streaks - use update_login_streak instead
        try:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if user was active today (learning activities)
                cursor.execute('''
                    SELECT COUNT(*) FROM daily_stats 
                    WHERE user_id = ? AND date = ? AND 
                    (phrases_learned > 0 OR study_time_minutes > 0 OR conversations_completed > 0)
                ''', (user_id, today.isoformat()))
                
                active_today = cursor.fetchone()[0] > 0
                
                # Get current streak info
                cursor.execute('''
                    SELECT current_streak, longest_streak, last_activity_date 
                    FROM user_progress WHERE user_id = ?
                ''', (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return {'current_streak': 0, 'longest_streak': 0}
                
                current_streak, longest_streak, last_activity = result
                
                if active_today:
                    if last_activity:
                        last_date = datetime.fromisoformat(last_activity).date()
                        if last_date == yesterday:
                            # Continue activity streak
                            current_streak += 1
                        elif last_date != today:
                            # Start new activity streak
                            current_streak = 1
                    else:
                        # First activity
                        current_streak = 1
                    
                    # Update longest streak
                    longest_streak = max(longest_streak, current_streak)
                    
                    # Update database
                    cursor.execute('''
                        UPDATE user_progress 
                        SET current_streak = ?, longest_streak = ?, 
                            last_activity_date = ?, updated_at = ?
                        WHERE user_id = ?
                    ''', (current_streak, longest_streak, datetime.now().isoformat(), 
                          datetime.now().isoformat(), user_id))
                    
                    conn.commit()
                
                return {
                    'current_streak': current_streak,
                    'longest_streak': longest_streak
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error updating activity streak: {str(e)}")
            return {'current_streak': 0, 'longest_streak': 0}

    def track_conversation_message(self, user_id: str, topic_id: str = None) -> bool:
        """Track individual conversation message and award XP"""
        try:
            # Award XP for sending a message
            self.add_experience_points(user_id, 'conversation_message')
            return True
        except Exception as e:
            logger.error(f"Error tracking conversation message: {str(e)}")
            return False

    def track_voice_message(self, user_id: str, topic_id: str = None) -> bool:
        """Track voice message usage and award XP"""
        try:
            # Award XP for using voice input
            self.add_experience_points(user_id, 'voice_message')
            return True
        except Exception as e:
            logger.error(f"Error tracking voice message: {str(e)}")
            return False

    def track_daily_login(self, user_id: str) -> bool:
        """Track daily login and award XP if first login today"""
        try:
            today = datetime.now().date().isoformat()
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if user already logged in today
                cursor.execute('''
                    SELECT COUNT(*) FROM daily_stats 
                    WHERE user_id = ? AND date = ? AND login_count > 0
                ''', (user_id, today))
                
                already_logged_in = cursor.fetchone()[0] > 0
                
                if not already_logged_in:
                    # Award XP for first login today
                    self.add_experience_points(user_id, 'daily_login')
                    
                    # Update login count in daily stats
                    cursor.execute('''
                        INSERT OR REPLACE INTO daily_stats 
                        (user_id, date, login_count, created_at)
                        VALUES (?, ?, 1, ?)
                    ''', (user_id, today, now))
                    
                    # Update login streak
                    self.update_login_streak(user_id, cursor)
                    
                    conn.commit()
                    return True
                    
            return False
        except sqlite3.Error as e:
            logger.error(f"Error tracking daily login: {str(e)}")
            return False

    def update_login_streak(self, user_id: str, cursor=None) -> Dict[str, int]:
        """Update daily login streak"""
        should_close_conn = cursor is None
        
        try:
            if cursor is None:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
            
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            # Get current streak info
            cursor.execute('''
                SELECT current_streak, longest_streak, last_activity_date 
                FROM user_progress WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if not result:
                return {'current_streak': 0, 'longest_streak': 0}
            
            current_streak, longest_streak, last_activity = result
            
            # Determine if streak should continue or start new
            if last_activity:
                last_date = datetime.fromisoformat(last_activity).date()
                if last_date == yesterday:
                    # Continue streak
                    current_streak += 1
                elif last_date != today:
                    # Start new streak
                    current_streak = 1
                # If last_date == today, don't change streak (already logged in today)
            else:
                # First time login
                current_streak = 1
            
            # Update longest streak
            longest_streak = max(longest_streak or 0, current_streak)
            
            # Update database
            cursor.execute('''
                UPDATE user_progress 
                SET current_streak = ?, longest_streak = ?, 
                    last_activity_date = ?, updated_at = ?
                WHERE user_id = ?
            ''', (current_streak, longest_streak, datetime.now().isoformat(), 
                  datetime.now().isoformat(), user_id))
            
            if should_close_conn:
                conn.commit()
                conn.close()
            
            logger.info(f"Updated login streak for user {user_id}: {current_streak} days")
            
            return {
                'current_streak': current_streak,
                'longest_streak': longest_streak
            }
            
        except sqlite3.Error as e:
            logger.error(f"Error updating login streak: {str(e)}")
            if should_close_conn and 'conn' in locals():
                conn.close()
            return {'current_streak': 0, 'longest_streak': 0}

    def reset_daily_progress(self, user_id: str) -> bool:
        """Reset daily progress counters (called at midnight)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE user_progress 
                    SET phrases_learned_today = 0, updated_at = ?
                    WHERE user_id = ?
                ''', (datetime.now().isoformat(), user_id))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error resetting daily progress: {str(e)}")
            return False

def create_progress_tracker(db_path: str) -> ProgressTracker:
    """Factory function to create ProgressTracker instance"""
    return ProgressTracker(db_path)
