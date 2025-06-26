from database.sqlite import Database
import uuid
from utils.settings import get_settings
from datetime import datetime, timezone

settings = get_settings()


class DreamVisualizerChatDatabase:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.async_sqlite_url
        self.database = Database(self.database_url)
        print(f"Initialized dream chat database with URL: {self.database_url}")

    async def connect_db(self):
        if hasattr(self, 'database') and not self.database.is_connected:
            await self.database.connect()
    
    async def disconnect_db(self):
        if hasattr(self, 'database') and self.database.is_connected:
            await self.database.disconnect()
    
    async def fetch_one(self, query: str, values: dict = None):
        await self.connect_db()
        result = await self.database.fetch_one(query=query, values=values)
        await self.disconnect_db()
        return result
    
    async def fetch_all(self, query: str, values: dict = None):
        await self.connect_db()
        result = await self.database.fetch_all(query=query, values=values)
        await self.disconnect_db()
        return result
    
    async def execute(self, query: str, values: dict = None):
        await self.connect_db()
        await self.database.execute(query=query, values=values)
        await self.disconnect_db()

    async def save_chat_message(self, tenant: str, message: str, role: str, session_id: str):
        await self.connect_db()
        query = """
        INSERT INTO dream_chat_messages(id, tenant, message, role, session_id, created_at) 
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
        await self.database.execute(query=query, values=values)
        await self.disconnect_db()

    async def save_session(self, tenant: str, session_id: str):
        await self.connect_db()
        query = """
        INSERT INTO dream_chat_sessions(id, tenant, is_active, created_at) 
        VALUES (:id, :tenant, :is_active, :created_at)
        """
        values = {
            "id": session_id,
            "tenant": tenant,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        await self.database.execute(query=query, values=values)
        await self.disconnect_db()

    async def close_session(self, session_id: str):
        await self.connect_db()
        query = "UPDATE dream_chat_sessions SET is_active = False WHERE id = :id"
        values = {"id": session_id}
        await self.database.execute(query=query, values=values)
        await self.disconnect_db() 