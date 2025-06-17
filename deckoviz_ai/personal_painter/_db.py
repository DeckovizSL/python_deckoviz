from database.sqlite import Database
import uuid
from utils.settings import get_settings
from datetime import datetime, timezone

settings = get_settings()


class PersonalPainterDatabase:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.async_sqlite_url
        self.database = Database(self.database_url)
        print(f"Initialized database with URL: {self.database_url}")

    async def connect_db(self):
        """Connect to the database if not already connected"""
        if hasattr(self, 'database') and not self.database.is_connected:
            await self.database.connect()
            print("Database connected successfully.")
    
    async def disconnect_db(self):
        """Disconnect from the database if connected"""
        if hasattr(self, 'database') and self.database.is_connected:
            await self.database.disconnect()
            print("Database disconnected.")
    
    async def fetch_one(self, query: str, values: dict = None):
        """Fetch a single row from the database"""
        await self.connect_db()
        print(f"Executing query: {query} with values: {values}")
        result = await self.database.fetch_one(query=query, values=values)
        print(f"Query result: {result}")
        await self.disconnect_db()
        return result
    
    async def fetch_all(self, query: str, values: dict = None):
        """Fetch all rows from the database"""
        await self.connect_db()
        print(f"Executing query: {query} with values: {values}")
        result = await self.database.fetch_all(query=query, values=values)
        print(f"Query returned {len(result) if result else 0} rows")
        await self.disconnect_db()
        return result
    
    async def execute(self, query: str, values: dict = None):
        """Execute a query on the database"""
        await self.connect_db()
        print(f"Executing query: {query} with values: {values}")
        await self.database.execute(query=query, values=values)
        await self.disconnect_db()
        print("Query executed successfully")

    async def save_chat_message(self, tenant: str, message: str, role: str, session_id: str):
        """Save a chat message with session ID"""
        await self.connect_db()
        
        query = """
        INSERT INTO chat_messages(id, tenant, message, role, session_id, created_at) 
        VALUES (:id, :tenant, :message, :role, :session_id, :created_at)
        """
        values = {
            "id": str(uuid.uuid4()),
            "tenant": tenant,
            "message": message,
            "role": role,
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc)
        }
        print(f"Saving chat message: {values}")
        await self.database.execute(query=query, values=values)
        await self.disconnect_db()
        print(f"Chat message from {tenant} saved for session {session_id}")

    async def save_session(self, tenant: str, session_id: str):
        """Save a new chat session"""
        await self.connect_db()
        
        query = """
        INSERT INTO chat_sessions(id, tenant, is_active, created_at) 
        VALUES (:id, :tenant, :is_active, :created_at)
        """
        values = {
            "id": session_id,
            "tenant": tenant,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        print(f"Saving new session: {values}")
        await self.database.execute(query=query, values=values)
        await self.disconnect_db()
        print(f"Chat session {session_id} created for {tenant}")

    async def close_session(self, session_id: str):
        """Close a chat session"""
        await self.connect_db()
        query = "UPDATE chat_sessions SET is_active = False WHERE id = :id"
        values = {"id": session_id}
        print(f"Closing session: {values}")
        await self.database.execute(query=query, values=values)
        await self.disconnect_db()
        print(f"Chat session {session_id} closed")
        