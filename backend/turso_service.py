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
# Temporarily set to DEBUG to see exact error
logger.setLevel(logging.DEBUG)

class TursoService:
    """Database service that works with both Turso (production) and SQLite (development)"""
    
    def __init__(self, database_url: Optional[str] = None, auth_token: Optional[str] = None):
        self.database_url = database_url or os.environ.get('TURSO_DATABASE_URL')
        self.auth_token = auth_token or os.environ.get('TURSO_AUTH_TOKEN')
        self.client = None
        
        # Check if this is a Turso database (either libsql:// or https:// format)
        self.is_turso = bool(
            self.database_url and (
                self.database_url.startswith('libsql://') or 
                (self.database_url.startswith('https://') and 'turso.io' in self.database_url)
            )
        )
        
        # Debug logging for Turso configuration
        logger.info(f"Initializing database service - Turso: {self.is_turso}")
        logger.info(f"Database URL present: {bool(self.database_url)}")
        logger.info(f"Auth token present: {bool(self.auth_token)}")
        if self.database_url:
            logger.info(f"Database URL format: {self.database_url[:50]}...")
            if self.database_url.startswith('libsql://'):
                logger.info("Database URL format: libsql (Turso WebSocket)")
            elif self.database_url.startswith('https://') and 'turso.io' in self.database_url:
                logger.info("Database URL format: https (Turso HTTP)")
            else:
                logger.info("Database URL format: other/sqlite")
        
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
            logger.info(f"Database URL: {self.database_url[:50]}...")
            logger.info(f"Auth token length: {len(self.auth_token) if self.auth_token else 0}")
            
            # Ensure we have a proper event loop for async operations
            import asyncio
            import threading
            
            # Check if we're in the main thread
            is_main_thread = threading.current_thread() is threading.main_thread()
            logger.info(f"Running in main thread: {is_main_thread}")
            
            try:
                # Try to get the current event loop
                loop = asyncio.get_running_loop()
                logger.info("Found running event loop")
            except RuntimeError:
                try:
                    # No running loop, try to get the event loop for current thread
                    loop = asyncio.get_event_loop()
                    logger.info("Using existing event loop")
                except RuntimeError:
                    # No event loop exists, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    logger.info("Created new event loop for Turso")
            
            # For Flask/sync context, we need to use sync methods if available
            # Method 1: Try sync client first (best for Flask)
            try:
                if hasattr(libsql_client, 'create_client_sync'):
                    logger.info("Attempting sync client creation...")
                    self.client = libsql_client.create_client_sync(
                        url=self.database_url,
                        auth_token=self.auth_token
                    )
                    logger.info("✅ Created Turso sync client")
                else:
                    raise AttributeError("sync client not available")
                    
            except (AttributeError, Exception) as sync_error:
                logger.info(f"Sync client failed: {sync_error}, trying async client...")
                
                # Method 2: If already HTTPS, use async client with proper event loop
                if self.database_url.startswith('https://'):
                    try:
                        logger.info("Using HTTPS URL with async client...")
                        
                        # Ensure the event loop is set for the current thread
                        if not loop.is_running():
                            asyncio.set_event_loop(loop)
                        
                        self.client = libsql_client.create_client(
                            url=self.database_url,
                            auth_token=self.auth_token
                        )
                        logger.info("✅ Created Turso async client with HTTPS URL")
                    except Exception as https_error:
                        logger.warning(f"HTTPS async client failed: {https_error}")
                        raise https_error
                
                # Method 3: Convert libsql:// to HTTPS and try async client
                elif self.database_url.startswith('libsql://'):
                    try:
                        # Convert WebSocket URL to HTTP
                        http_url = self.database_url.replace('libsql://', 'https://')
                        logger.info(f"Converting to HTTPS URL: {http_url[:50]}...")
                        
                        # Ensure the event loop is set for the current thread
                        if not loop.is_running():
                            asyncio.set_event_loop(loop)
                        
                        self.client = libsql_client.create_client(
                            url=http_url,
                            auth_token=self.auth_token
                        )
                        logger.info("✅ Created Turso async client with converted HTTPS URL")
                    except Exception as convert_error:
                        logger.warning(f"HTTPS conversion failed: {convert_error}")
                        raise convert_error
            
            # Test the connection with a simple query
            try:
                logger.info("Testing Turso connection...")
                result = self.client.execute("SELECT 1")
                logger.info("✅ Connected to Turso database successfully")
                logger.info(f"Query result: {result}")
                return True
            except Exception as test_error:
                logger.warning(f"Turso connection test failed: {test_error}")
                logger.warning(f"Error type: {type(test_error).__name__}")
                
                # If it's a WebSocket error, provide specific guidance
                if "WSServerHandshakeError" in str(type(test_error)) or "505" in str(test_error):
                    logger.error("❌ WebSocket handshake failed - Render network restriction confirmed")
                    logger.error("Render free tier blocks WebSocket connections to external services")
                    logger.error("Solution: Use HTTPS format in TURSO_DATABASE_URL instead of libsql://")
                    logger.error("Example: https://your-db.turso.io instead of libsql://your-db.turso.io")
                
                raise test_error
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to Turso: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            
            # For deployment, we'll fall back to SQLite
            logger.warning("🔄 Falling back to SQLite - Event loop configuration issue")
            logger.warning("This is likely due to Flask/async context incompatibility")
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
                try:
                    # Execute query with proper parameter handling
                    logger.debug(f"Executing Turso query: {query[:100]}...")
                    logger.debug(f"With params: {params}")
                    
                    if params:
                        # Convert tuple to list for libsql_client
                        params_list = list(params) if isinstance(params, tuple) else params
                        result = self.client.execute(query, params_list)
                    else:
                        result = self.client.execute(query)
                    
                    logger.debug(f"Turso query executed successfully, result type: {type(result)}")
                    
                    # Handle libsql_client.result.ResultSet from sync client
                    if hasattr(result, 'columns') and hasattr(result, 'rows'):
                        try:
                            # Extract column names - columns should be a tuple of strings
                            columns = []
                            try:
                                if result.columns:
                                    columns = list(result.columns)
                                    logger.debug(f"Extracted columns: {columns}")
                            except (KeyError, AttributeError, TypeError) as col_error:
                                logger.warning(f"Column access error: {col_error}")
                                # Try alternative access methods
                                try:
                                    if hasattr(result, '__getitem__') and 'columns' in result:
                                        columns = list(result['columns'])
                                    elif hasattr(result, 'get'):
                                        columns = list(result.get('columns', []))
                                except Exception as alt_col_error:
                                    logger.warning(f"Alternative column access failed: {alt_col_error}")
                                    columns = []
                            
                            # Extract rows data
                            rows = []
                            try:
                                if result.rows:
                                    rows = list(result.rows)
                                    logger.debug(f"Extracted {len(rows)} rows")
                            except (KeyError, AttributeError, TypeError) as row_error:
                                logger.warning(f"Row access error: {row_error}")
                                # Try alternative access methods
                                try:
                                    if hasattr(result, '__getitem__') and 'rows' in result:
                                        rows = list(result['rows'])
                                    elif hasattr(result, 'get'):
                                        rows = list(result.get('rows', []))
                                except Exception as alt_row_error:
                                    logger.warning(f"Alternative row access failed: {alt_row_error}")
                                    rows = []
                            
                            # Create result dictionaries
                            if columns and rows:
                                final_result = [dict(zip(columns, row)) for row in rows]
                                logger.debug(f"Created {len(final_result)} result dictionaries")
                                return final_result
                            elif rows:
                                # No column names, use numeric indices
                                final_result = [dict(enumerate(row)) for row in rows]
                                logger.debug(f"Created {len(final_result)} numbered result dictionaries")
                                return final_result
                            else:
                                logger.debug("No rows returned")
                                return []
                                
                        except Exception as parse_error:
                            logger.error(f"Error parsing Turso result: {parse_error}")
                            logger.error(f"Parse error type: {type(parse_error)}")
                            logger.error(f"Result type: {type(result)}")
                            logger.error(f"Result attributes: {dir(result)}")
                            logger.error(f"Result repr: {repr(result)}")
                            return []
                    
                    else:
                        logger.warning(f"Turso result missing columns/rows attributes: {type(result)}")
                        logger.warning(f"Available attributes: {dir(result)}")
                        return []
                        
                except Exception as turso_error:
                    logger.error(f"Turso execution error: {turso_error}")
                    logger.error(f"Turso error type: {type(turso_error)}")
                    logger.error(f"Turso error args: {turso_error.args if hasattr(turso_error, 'args') else 'No args'}")
                    
                    # Check if this is a "table doesn't exist" error
                    error_msg = str(turso_error).lower()
                    if 'table' in error_msg and ('not exist' in error_msg or 'no such table' in error_msg):
                        logger.error(f"❌ Table doesn't exist error detected for query: {query[:100]}")
                        logger.error("🔧 Attempting to recreate tables...")
                        self._create_tables()
                        logger.info("✅ Tables recreated, retrying query...")
                        
                        # Retry the query once after recreating tables
                        try:
                            if params:
                                params_list = list(params) if isinstance(params, tuple) else params
                                result = self.client.execute(query, params_list)
                            else:
                                result = self.client.execute(query)
                            logger.info("✅ Query succeeded after table recreation")
                        except Exception as retry_error:
                            logger.error(f"❌ Query still failed after table recreation: {retry_error}")
                            raise retry_error
                    else:
                        raise turso_error
                        
            else:
                # SQLite handling
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    return [dict(row) for row in cursor.fetchall()]
                    
        except Exception as e:
            logger.error(f"Database query error: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args if hasattr(e, 'args') else 'No args'}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            if self.is_turso:
                logger.error(f"Turso client type: {type(self.client)}")
            return []
    
    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """Execute an update/insert query"""
        try:
            if self.is_turso:
                try:
                    logger.debug(f"Executing Turso update: {query[:100]}...")
                    logger.debug(f"With params: {params}")
                    
                    # For updates, we don't need to process the result
                    if params:
                        # Convert tuple to list for libsql_client
                        params_list = list(params) if isinstance(params, tuple) else params
                        result = self.client.execute(query, params_list)
                    else:
                        result = self.client.execute(query)
                    
                    logger.debug(f"Turso update executed successfully, result type: {type(result)}")
                    return True
                    
                except Exception as turso_error:
                    logger.error(f"Turso update execution error: {turso_error}")
                    logger.error(f"Turso update error type: {type(turso_error)}")
                    logger.error(f"Turso update error args: {turso_error.args if hasattr(turso_error, 'args') else 'No args'}")
                    raise turso_error
                    
            else:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Database update error: {e}")
            logger.error(f"Update error type: {type(e)}")
            logger.error(f"Update error args: {e.args if hasattr(e, 'args') else 'No args'}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
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
        """Get user's learning progress - with fallback for problematic table"""
        # Try to get from user_progress table first
        try:
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
                # No existing progress, create default
                self.initialize_user_progress(user_id, 1)
                return {'level': 1, 'experience_points': 0, 'total_experience': 0}
                
        except Exception as progress_error:
            logger.warning(f"user_progress table access failed: {progress_error}")
            # Fallback: store progress in user settings JSON field
            try:
                user = self.get_user_by_id(user_id)
                if user and user.get('settings'):
                    import json
                    settings = json.loads(user['settings'])
                    progress = settings.get('progress', {'level': 1, 'experience_points': 0, 'total_experience': 0})
                    logger.info(f"Using fallback progress from user settings: {progress}")
                    return progress
                else:
                    # Return default progress
                    default_progress = {'level': 1, 'experience_points': 0, 'total_experience': 0}
                    logger.info(f"Using default progress: {default_progress}")
                    return default_progress
            except Exception as fallback_error:
                logger.error(f"Fallback progress retrieval failed: {fallback_error}")
                return {'level': 1, 'experience_points': 0, 'total_experience': 0}
    
    def initialize_user_progress(self, user_id: str, level: int) -> bool:
        """Initialize progress for a new user - with fallback"""
        # Try to use user_progress table first
        try:
            query = '''
                INSERT OR REPLACE INTO user_progress (user_id, level, experience_points, total_experience, created_at)
                VALUES (?, ?, 0, 0, ?)
            '''
            return self.execute_update(query, (user_id, level, datetime.now().isoformat()))
            
        except Exception as progress_error:
            logger.warning(f"user_progress table update failed: {progress_error}")
            # Fallback: store in user settings
            try:
                import json
                user = self.get_user_by_id(user_id)
                if user:
                    settings = json.loads(user.get('settings', '{}'))
                    settings['progress'] = {'level': level, 'experience_points': 0, 'total_experience': 0}
                    settings_json = json.dumps(settings)
                    
                    update_query = 'UPDATE users SET settings = ? WHERE id = ?'
                    result = self.execute_update(update_query, (settings_json, user_id))
                    logger.info(f"Stored progress in user settings as fallback")
                    return result
                else:
                    logger.error(f"Could not find user {user_id} for progress fallback")
                    return False
            except Exception as fallback_error:
                logger.error(f"Fallback progress initialization failed: {fallback_error}")
                return False
    
    def add_experience_points(self, user_id: str, points: int) -> bool:
        """Add experience points to user - with fallback"""
        # Try user_progress table first
        try:
            query = '''
                UPDATE user_progress 
                SET experience_points = experience_points + ?, 
                    total_experience = total_experience + ?
                WHERE user_id = ?
            '''
            return self.execute_update(query, (points, points, user_id))
            
        except Exception as progress_error:
            logger.warning(f"user_progress table experience update failed: {progress_error}")
            # Fallback: update user settings
            try:
                import json
                user = self.get_user_by_id(user_id)
                if user:
                    settings = json.loads(user.get('settings', '{}'))
                    progress = settings.get('progress', {'level': 1, 'experience_points': 0, 'total_experience': 0})
                    
                    progress['experience_points'] += points
                    progress['total_experience'] += points
                    settings['progress'] = progress
                    settings_json = json.dumps(settings)
                    
                    update_query = 'UPDATE users SET settings = ? WHERE id = ?'
                    result = self.execute_update(update_query, (settings_json, user_id))
                    logger.info(f"Updated experience points in user settings as fallback")
                    return result
                else:
                    return False
            except Exception as fallback_error:
                logger.error(f"Fallback experience update failed: {fallback_error}")
                return False
    
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
