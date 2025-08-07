# Database Migration Script: SQLite to Turso
# This script migrates data from local SQLite to Turso database

import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict

try:
    import libsql_client
    TURSO_AVAILABLE = True
except ImportError:
    TURSO_AVAILABLE = False
    print("❌ libsql_client not installed. Run: pip install libsql-client")

from turso_service import TursoService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Migrate data from SQLite to Turso"""
    
    def __init__(self, sqlite_path: str, turso_url: str, turso_token: str):
        self.sqlite_path = sqlite_path
        self.turso_service = TursoService(turso_url, turso_token)
        
    def migrate_all_data(self):
        """Migrate all data from SQLite to Turso"""
        logger.info("🚀 Starting database migration from SQLite to Turso...")
        
        if not os.path.exists(self.sqlite_path):
            logger.error(f"❌ SQLite database not found: {self.sqlite_path}")
            return False
        
        if not TURSO_AVAILABLE:
            logger.error("❌ Turso client not available")
            return False
        
        try:
            # Connect to SQLite
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Migrate users
            self._migrate_users(cursor)
            
            # Migrate progress
            self._migrate_progress(cursor)
            
            # Migrate conversations
            self._migrate_conversations(cursor)
            
            # Migrate user_progress (if exists)
            self._migrate_user_progress(cursor)
            
            # Migrate spaced_repetition (if exists)
            self._migrate_spaced_repetition(cursor)
            
            # Migrate daily_challenges (if exists)
            self._migrate_daily_challenges(cursor)
            
            conn.close()
            
            logger.info("✅ Database migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    def _migrate_users(self, cursor):
        """Migrate users table"""
        logger.info("📱 Migrating users...")
        
        try:
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            
            for user in users:
                user_dict = dict(user)
                success = self.turso_service.execute_update(
                    '''INSERT OR REPLACE INTO users 
                       (id, username, password, name, age, level, created_at, last_active, settings)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        user_dict['id'],
                        user_dict['username'],
                        user_dict['password'],
                        user_dict['name'],
                        user_dict['age'],
                        user_dict['level'],
                        user_dict.get('created_at', datetime.now().isoformat()),
                        user_dict.get('last_active', datetime.now().isoformat()),
                        user_dict.get('settings', '{}')
                    )
                )
                
                if not success:
                    logger.warning(f"⚠️ Failed to migrate user: {user_dict['username']}")
            
            logger.info(f"✅ Migrated {len(users)} users")
            
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                logger.info("⚠️ Users table doesn't exist in source database")
            else:
                raise e
    
    def _migrate_progress(self, cursor):
        """Migrate progress table"""
        logger.info("📊 Migrating progress...")
        
        try:
            cursor.execute("SELECT * FROM progress")
            progress_records = cursor.fetchall()
            
            for record in progress_records:
                record_dict = dict(record)
                success = self.turso_service.execute_update(
                    '''INSERT OR REPLACE INTO progress 
                       (id, user_id, topic, level, completed, completion_date, phrases_learned, practice_sessions)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        record_dict.get('id'),
                        record_dict['user_id'],
                        record_dict['topic'],
                        record_dict['level'],
                        record_dict.get('completed', False),
                        record_dict.get('completion_date'),
                        record_dict.get('phrases_learned', 0),
                        record_dict.get('practice_sessions', 0)
                    )
                )
                
                if not success:
                    logger.warning(f"⚠️ Failed to migrate progress for user: {record_dict['user_id']}")
            
            logger.info(f"✅ Migrated {len(progress_records)} progress records")
            
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                logger.info("⚠️ Progress table doesn't exist in source database")
            else:
                raise e
    
    def _migrate_conversations(self, cursor):
        """Migrate conversations table"""
        logger.info("💬 Migrating conversations...")
        
        try:
            cursor.execute("SELECT * FROM conversations")
            conversations = cursor.fetchall()
            
            for conversation in conversations:
                conv_dict = dict(conversation)
                success = self.turso_service.execute_update(
                    '''INSERT OR REPLACE INTO conversations 
                       (id, user_id, topic, messages, created_at)
                       VALUES (?, ?, ?, ?, ?)''',
                    (
                        conv_dict.get('id'),
                        conv_dict['user_id'],
                        conv_dict['topic'],
                        conv_dict['messages'],
                        conv_dict.get('created_at', datetime.now().isoformat())
                    )
                )
                
                if not success:
                    logger.warning(f"⚠️ Failed to migrate conversation for user: {conv_dict['user_id']}")
            
            logger.info(f"✅ Migrated {len(conversations)} conversations")
            
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                logger.info("⚠️ Conversations table doesn't exist in source database")
            else:
                raise e
    
    def _migrate_user_progress(self, cursor):
        """Migrate user_progress table"""
        logger.info("🎮 Migrating user progress...")
        
        try:
            cursor.execute("SELECT * FROM user_progress")
            user_progress = cursor.fetchall()
            
            for progress in user_progress:
                progress_dict = dict(progress)
                success = self.turso_service.execute_update(
                    '''INSERT OR REPLACE INTO user_progress 
                       (id, user_id, level, experience_points, total_experience, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (
                        progress_dict.get('id'),
                        progress_dict['user_id'],
                        progress_dict.get('level', 1),
                        progress_dict.get('experience_points', 0),
                        progress_dict.get('total_experience', 0),
                        progress_dict.get('created_at', datetime.now().isoformat())
                    )
                )
                
                if not success:
                    logger.warning(f"⚠️ Failed to migrate user progress for: {progress_dict['user_id']}")
            
            logger.info(f"✅ Migrated {len(user_progress)} user progress records")
            
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                logger.info("⚠️ User_progress table doesn't exist in source database")
            else:
                raise e
    
    def _migrate_spaced_repetition(self, cursor):
        """Migrate spaced_repetition table"""
        logger.info("🔄 Migrating spaced repetition...")
        
        try:
            cursor.execute("SELECT * FROM spaced_repetition")
            spaced_repetition = cursor.fetchall()
            
            for record in spaced_repetition:
                record_dict = dict(record)
                success = self.turso_service.execute_update(
                    '''INSERT OR REPLACE INTO spaced_repetition 
                       (id, user_id, phrase_id, interval_days, ease_factor, repetitions, next_review, quality)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        record_dict.get('id'),
                        record_dict['user_id'],
                        record_dict['phrase_id'],
                        record_dict.get('interval_days', 1),
                        record_dict.get('ease_factor', 2.5),
                        record_dict.get('repetitions', 0),
                        record_dict['next_review'],
                        record_dict.get('quality', 0)
                    )
                )
                
                if not success:
                    logger.warning(f"⚠️ Failed to migrate spaced repetition for user: {record_dict['user_id']}")
            
            logger.info(f"✅ Migrated {len(spaced_repetition)} spaced repetition records")
            
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                logger.info("⚠️ Spaced_repetition table doesn't exist in source database")
            else:
                raise e
    
    def _migrate_daily_challenges(self, cursor):
        """Migrate daily_challenges table"""
        logger.info("🎯 Migrating daily challenges...")
        
        try:
            cursor.execute("SELECT * FROM daily_challenges")
            daily_challenges = cursor.fetchall()
            
            for challenge in daily_challenges:
                challenge_dict = dict(challenge)
                success = self.turso_service.execute_update(
                    '''INSERT OR REPLACE INTO daily_challenges 
                       (id, user_id, challenge_date, challenge_type, target_count, current_count, completed)
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (
                        challenge_dict.get('id'),
                        challenge_dict['user_id'],
                        challenge_dict['challenge_date'],
                        challenge_dict['challenge_type'],
                        challenge_dict.get('target_count', 3),
                        challenge_dict.get('current_count', 0),
                        challenge_dict.get('completed', False)
                    )
                )
                
                if not success:
                    logger.warning(f"⚠️ Failed to migrate daily challenge for user: {challenge_dict['user_id']}")
            
            logger.info(f"✅ Migrated {len(daily_challenges)} daily challenge records")
            
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                logger.info("⚠️ Daily_challenges table doesn't exist in source database")
            else:
                raise e
    
    def verify_migration(self):
        """Verify that migration was successful"""
        logger.info("🔍 Verifying migration...")
        
        health = self.turso_service.health_check()
        
        if health['status'] == 'healthy':
            logger.info(f"✅ Migration verified - {health['user_count']} users in Turso database")
            return True
        else:
            logger.error(f"❌ Migration verification failed: {health}")
            return False

def main():
    """Main migration function"""
    print("🔄 SQLite to Turso Migration Tool")
    print("=" * 50)
    
    # Get configuration
    sqlite_path = input("Enter SQLite database path (default: data/db/language_app.db): ").strip()
    if not sqlite_path:
        sqlite_path = os.path.join("data", "db", "language_app.db")
    
    turso_url = input("Enter Turso database URL: ").strip()
    if not turso_url:
        print("❌ Turso database URL is required")
        return
    
    turso_token = input("Enter Turso auth token: ").strip()
    if not turso_token:
        print("❌ Turso auth token is required")
        return
    
    # Start migration
    migrator = DatabaseMigrator(sqlite_path, turso_url, turso_token)
    
    if migrator.migrate_all_data():
        if migrator.verify_migration():
            print("\n🎉 Migration completed successfully!")
            print("Your data has been migrated to Turso.")
            print("\nNext steps:")
            print("1. Update your Render environment variables")
            print("2. Deploy your application to Render")
        else:
            print("\n⚠️ Migration completed but verification failed")
    else:
        print("\n❌ Migration failed")

if __name__ == "__main__":
    main()
