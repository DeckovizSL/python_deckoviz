from database.sqlite import Database
import uuid
from utils.settings import get_settings

settings = get_settings()


class PersonalPainterDatabase:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.async_sqlite_url
        self.database = Database(self.database_url)

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
    
    async def save_chat_message(self, tenant: str, message: str, role: str):
        # Connect to the database if not already connected
        await self.connect_db()
        
        query = "INSERT INTO chat_messages(id, tenant, message, role) VALUES (:id, :tenant, :message, :role)"
        values = {"id": uuid.uuid4(), "tenant": tenant, "message": message, "role": role}
        await self.database.execute(query=query, values=values)
        await self.disconnect_db()
        print(f"Chat message from {tenant} saved asynchronously.")

    async def save_session(self, tenant: str, session_id: str):
        # Connect to the database if not already connected
        await self.connect_db()
        
        query = "INSERT INTO chat_sessions(id, tenant, is_active) VALUES (:id, :tenant, :is_active)"
        values = {"id": session_id, "tenant": tenant, "is_active": True}
        await self.database.execute(query=query, values=values)
        await self.disconnect_db()
        print(f"Chat session from {tenant} saved asynchronously.")

    async def close_session(self,  session_id: str):
        # Connect to the database if not already connected
        await self.connect_db()
        query = "UPDATE chat_sessions SET is_active = False WHERE id = :id"
        values = {"id": session_id}
        await self.database.execute(query=query, values=values)
        await self.disconnect_db()
        print(f"Chat session from {session_id} closed asynchronously.")
        