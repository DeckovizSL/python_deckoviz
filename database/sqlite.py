from databases import Database
import asyncio
import sqlite3
import os
import time

# Ensure the database directory exists
os.makedirs('data', exist_ok=True)

DATABASE_URL = "sqlite+aiosqlite:///data/chat_history.db"
database = Database(DATABASE_URL)

def create_sqlite_db():
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect('data/chat_history.db')
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'")
            chat_messages_exists = cursor.fetchone() is not None
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'")
            chat_sessions_exists = cursor.fetchone() is not None
            
            # Create or migrate chat_messages table
            if not chat_messages_exists:
                cursor.execute('''
                CREATE TABLE chat_messages (
                    id TEXT PRIMARY KEY,
                    tenant TEXT NOT NULL,
                    message TEXT NOT NULL,
                    role TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
                )
                ''')
            else:
                # Check if session_id column exists
                cursor.execute("PRAGMA table_info(chat_messages)")
                columns = [column[1] for column in cursor.fetchall()]
                if 'session_id' not in columns:
                    try:
                        # Create new table with correct schema
                        cursor.execute('''
                        CREATE TABLE IF NOT EXISTS chat_messages_new (
                            id TEXT PRIMARY KEY,
                            tenant TEXT NOT NULL,
                            message TEXT NOT NULL,
                            role TEXT NOT NULL,
                            session_id TEXT NOT NULL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
                        )
                        ''')
                        # Copy data from old table to new table
                        cursor.execute('''
                        INSERT INTO chat_messages_new (id, tenant, message, role, session_id, created_at)
                        SELECT id, tenant, message, role, 
                               (SELECT id FROM chat_sessions WHERE tenant = chat_messages.tenant ORDER BY created_at DESC LIMIT 1) as session_id,
                               CASE 
                                   WHEN created_at IS NOT NULL THEN created_at 
                                   ELSE CURRENT_TIMESTAMP 
                               END as created_at
                        FROM chat_messages
                        ''')
                        # Drop old table and rename new table
                        cursor.execute('DROP TABLE IF EXISTS chat_messages')
                        cursor.execute('ALTER TABLE chat_messages_new RENAME TO chat_messages')
                    except sqlite3.OperationalError as e:
                        if "already exists" in str(e):
                            # If the new table already exists, just drop the old one and rename
                            cursor.execute('DROP TABLE IF EXISTS chat_messages')
                            cursor.execute('ALTER TABLE chat_messages_new RENAME TO chat_messages')
                        else:
                            raise
            
            # Create or migrate chat_sessions table
            if not chat_sessions_exists:
                cursor.execute('''
                CREATE TABLE chat_sessions (
                    id TEXT PRIMARY KEY,
                    tenant TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                ''')
            else:
                # Check if created_at and updated_at columns exist
                cursor.execute("PRAGMA table_info(chat_sessions)")
                columns = [column[1] for column in cursor.fetchall()]
                if 'created_at' not in columns or 'updated_at' not in columns:
                    try:
                        # Create new table with correct schema
                        cursor.execute('''
                        CREATE TABLE IF NOT EXISTS chat_sessions_new (
                            id TEXT PRIMARY KEY,
                            tenant TEXT NOT NULL,
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                        ''')
                        # Copy data from old table to new table
                        cursor.execute('''
                        INSERT INTO chat_sessions_new (id, tenant, is_active, created_at, updated_at)
                        SELECT id, tenant, is_active, 
                               CURRENT_TIMESTAMP as created_at,
                               CURRENT_TIMESTAMP as updated_at
                        FROM chat_sessions
                        ''')
                        # Drop old table and rename new table
                        cursor.execute('DROP TABLE IF EXISTS chat_sessions')
                        cursor.execute('ALTER TABLE chat_sessions_new RENAME TO chat_sessions')
                    except sqlite3.OperationalError as e:
                        if "already exists" in str(e):
                            # If the new table already exists, just drop the old one and rename
                            cursor.execute('DROP TABLE IF EXISTS chat_sessions')
                            cursor.execute('ALTER TABLE chat_sessions_new RENAME TO chat_sessions')
                        else:
                            raise
            
            conn.commit()
            conn.close()
            print("SQLite database created/migrated successfully.")
            return
            
        except sqlite3.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Database migration attempt {attempt + 1} failed: {str(e)}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"Database migration failed after {max_retries} attempts: {str(e)}")
                raise
        except Exception as e:
            print(f"Unexpected error during database migration: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

# Initialize the database
create_sqlite_db()

 
