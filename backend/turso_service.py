# Turso Database Service for Render Deployment
import os
import json
import logging
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import libsql_client
    TURSO_AVAILABLE = True
except ImportError:
    TURSO_AVAILABLE = False

logger = logging.getLogger(__name__)

class TursoService:
    """Database service that works with both Turso (production) and SQLite (development)"""
    
    def __init__(self, database_url: Optional[str] = None, auth_token: Optional[str] = None):
        self.database_url = database_url or os.environ.get('TURSO_DATABASE_URL')
        self.auth_token = auth_token or os.environ.get('TURSO_AUTH_TOKEN')
        self.client = None
        self.is_turso = self.database_url and self.database_url.startswith('libsql://')
        
        # Debug logging for Turso configuration
        logger.info(f"Initializing database service - Turso: {self.is_turso}")
        logger.info(f"Database URL present: {bool(self.database_url)}")
        logger.info(f"Auth token present: {bool(self.auth_token)}")
        if self.database_url:
            logger.info(f"Database URL starts with libsql://: {self.database_url.startswith('libsql://')}")
        
        if self.is_turso and TURSO_AVAILABLE:
            logger.info("Turso client available, attempting connection...")
            self._init_turso()
        else:
            if not TURSO_AVAILABLE:
                logger.warning("Turso client library not available, falling back to SQLite")
            if not self.is_turso:
                logger.info("Not configured for Turso, using SQLite")
            self._init_sqlite()
        
        self._create_tables()
    
    def _init_turso(self):
        """Initialize Turso client"""
        try:
            logger.info("Creating Turso client...")
            
            # Try different client creation approaches
            import asyncio
            
            # Method 1: Try creating sync client if available
            try:
                if hasattr(libsql_client, 'create_client_sync'):
                    self.client = libsql_client.create_client_sync(
                        url=self.database_url,
                        auth_token=self.auth_token
                    )
                    logger.info("✅ Created Turso sync client")
                else:
                    raise AttributeError("sync client not available")
            except (AttributeError, Exception) as sync_error:
                logger.info(f"Sync client failed: {sync_error}, trying regular client...")
                
                # Method 2: Create event loop if none exists
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    # No event loop, create one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    logger.info("Created new event loop for Turso")
                
                # Method 3: Create regular client with event loop
                self.client = libsql_client.create_client(
                    url=self.database_url,
                    auth_token=self.auth_token
                )
                logger.info("✅ Created Turso regular client with event loop")
            
            # Test the connection with a simple query
            try:
                result = self.client.execute("SELECT 1")
                logger.info("✅ Connected to Turso database successfully")
                logger.info(f"Query result: {result}")
                return True
            except Exception as test_error:
                logger.warning(f"Turso connection test failed: {test_error}")
                raise test_error
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to Turso: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            self._fallback_to_sqlite()
            return False
    
    def _init_sqlite(self):
        """Initialize SQLite fallback"""
        # Extract path from database_url if it's a file:// URL
        if self.database_url and self.database_url.startswith('file:'):
            db_path = self.database_url[5:]  # Remove 'file:' prefix
        else:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "db", "language_app.db")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.is_turso = False
        logger.info(f"Using SQLite database: {db_path}")
    
    def _fallback_to_sqlite(self):
        """Fallback to SQLite if Turso fails"""
        logger.warning("Falling back to SQLite database")
        self._init_sqlite()
    
    def get_connection(self):
        """Get database connection"""
        if self.is_turso:
            return self.client
        else:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA cache_size=10000')
            conn.execute('PRAGMA temp_store=MEMORY')
            return conn
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a query and return results"""
        try:
            if self.is_turso:
                result = self.client.execute(query, params)
                return [dict(zip([col.name for col in result.columns], row)) for row in result.rows]
            else:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []
    
    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """Execute an update/insert query"""
        try:
            if self.is_turso:
                self.client.execute(query, params)
                return True
            else:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Database update error: {e}")
            return False
    
    def _create_tables(self):
        """Create required database tables"""
        tables = [
            '''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                level INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP,
                settings TEXT DEFAULT '{}'
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                level INTEGER NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                completion_date TEXT,
                phrases_learned INTEGER DEFAULT 0,
                practice_sessions INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                messages TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                experience_points INTEGER DEFAULT 0,
                total_experience INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS spaced_repetition (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                phrase_id TEXT NOT NULL,
                interval_days INTEGER DEFAULT 1,
                ease_factor REAL DEFAULT 2.5,
                repetitions INTEGER DEFAULT 0,
                next_review TEXT NOT NULL,
                quality INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS daily_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                challenge_date TEXT NOT NULL,
                challenge_type TEXT NOT NULL,
                target_count INTEGER DEFAULT 3,
                current_count INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            '''
        ]
        
        for table in tables:
            if not self.execute_update(table):
                logger.error(f"Failed to create table: {table[:50]}...")
        
        logger.info("Database tables initialized")
    
    # User management methods
    def create_user(self, user_id: str, username: str, password: str, name: str, age: int, level: int) -> bool:
        """Create a new user"""
        query = '''
            INSERT INTO users (id, username, password, name, age, level, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        return self.execute_update(query, (user_id, username, password, name, age, level, datetime.now().isoformat()))
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        query = 'SELECT * FROM users WHERE username = ? LIMIT 1'
        results = self.execute_query(query, (username,))
        return results[0] if results else None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        query = 'SELECT * FROM users WHERE id = ? LIMIT 1'
        results = self.execute_query(query, (user_id,))
        return results[0] if results else None
    
    def update_user_last_active(self, user_id: str) -> bool:
        """Update user's last active timestamp"""
        query = 'UPDATE users SET last_active = ? WHERE id = ?'
        return self.execute_update(query, (datetime.now().isoformat(), user_id))
    
    # Progress tracking methods
    def get_user_progress(self, user_id: str) -> Dict:
        """Get user's learning progress"""
        query = '''
            SELECT level, experience_points, total_experience 
            FROM user_progress 
            WHERE user_id = ? 
            LIMIT 1
        '''
        results = self.execute_query(query, (user_id,))
        
        if results:
            return results[0]
        else:
            # Initialize progress for new user
            self.initialize_user_progress(user_id, 1)
            return {'level': 1, 'experience_points': 0, 'total_experience': 0}
    
    def initialize_user_progress(self, user_id: str, level: int) -> bool:
        """Initialize progress for a new user"""
        query = '''
            INSERT OR REPLACE INTO user_progress (user_id, level, experience_points, total_experience, created_at)
            VALUES (?, ?, 0, 0, ?)
        '''
        return self.execute_update(query, (user_id, level, datetime.now().isoformat()))
    
    def add_experience_points(self, user_id: str, points: int) -> bool:
        """Add experience points to user"""
        query = '''
            UPDATE user_progress 
            SET experience_points = experience_points + ?, 
                total_experience = total_experience + ?
            WHERE user_id = ?
        '''
        return self.execute_update(query, (points, points, user_id))
    
    # Conversation tracking
    def save_conversation(self, user_id: str, topic: str, messages: List[Dict]) -> bool:
        """Save conversation to database"""
        query = '''
            INSERT INTO conversations (user_id, topic, messages, created_at)
            VALUES (?, ?, ?, ?)
        '''
        return self.execute_update(query, (user_id, topic, json.dumps(messages), datetime.now().isoformat()))
    
    def get_user_conversations(self, user_id: str) -> List[Dict]:
        """Get user's conversation history"""
        query = '''
            SELECT topic, messages, created_at 
            FROM conversations 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 10
        '''
        results = self.execute_query(query, (user_id,))
        
        # Parse messages JSON
        for result in results:
            try:
                result['messages'] = json.loads(result['messages'])
            except:
                result['messages'] = []
        
        return results
    
    # Health check
    def health_check(self) -> Dict:
        """Check database health"""
        try:
            query = 'SELECT COUNT(*) as user_count FROM users'
            results = self.execute_query(query)
            
            return {
                'status': 'healthy',
                'database_type': 'turso' if self.is_turso else 'sqlite',
                'user_count': results[0]['user_count'] if results else 0,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'database_type': 'turso' if self.is_turso else 'sqlite',
                'timestamp': datetime.now().isoformat()
            }

# Global database service instance
db_service = None

def get_db_service() -> TursoService:
    """Get the global database service instance"""
    global db_service
    if db_service is None:
        db_service = TursoService()
    return db_service
