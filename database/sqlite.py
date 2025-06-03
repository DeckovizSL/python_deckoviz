from databases import Database
import asyncio

# Let's create a sqlite database
import sqlite3
import os

# Ensure the database directory exists
os.makedirs('data', exist_ok=True)

DATABASE_URL = "sqlite+aiosqlite:///chat_history.db"
database = Database(DATABASE_URL)

# Create and connect to the SQLite database
def create_sqlite_db():
    conn = sqlite3.connect('data/chat_history.db')
    cursor = conn.cursor()
    
    # Create the chat_messages table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        tenant TEXT NOT NULL,
        message TEXT NOT NULL,
        role TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    print("SQLite database created successfully.")
    
# Initialize the database
create_sqlite_db()

 
