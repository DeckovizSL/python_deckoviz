from typing import List, Dict
from langchain.schema import BaseMessage
from langchain.memory import ConversationBufferMemory
import json
from database.connection import AsyncSession
from models.chat import ChatMessage
from datetime import datetime

class PostgresChatMemory:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.buffer_memory = ConversationBufferMemory(return_messages=True)
        self.temp_messages: List[Dict] = []
    
    async def add_message(self, message_type: str, content: str, metadata: Dict = None):
        """Add message to temporary buffer"""
        message_data = {
            "message_type": message_type,
            "content": content,
            "metadata": json.dumps(metadata) if metadata else None,
            "timestamp": datetime.utcnow()
        }
        self.temp_messages.append(message_data)
        
        # Also add to LangChain memory for immediate use
        if message_type == "human":
            self.buffer_memory.chat_memory.add_user_message(content)
        elif message_type == "ai":
            self.buffer_memory.chat_memory.add_ai_message(content)
    
    async def get_messages(self) -> List[BaseMessage]:
        """Get messages for LangChain"""
        return self.buffer_memory.chat_memory.messages
    
    async def save_to_postgres(self):
        """Save all temporary messages to PostgreSQL"""
        async with AsyncSession() as db:
            try:
                for msg_data in self.temp_messages:
                    chat_message = ChatMessage(
                        session_id=self.session_id,
                        **msg_data
                    )
                    db.add(chat_message)
                
                await db.commit()
                self.temp_messages.clear()  # Clear after successful save
                return True
            except Exception as e:
                await db.rollback()
                print(f"Error saving messages: {e}")
                return False
    
    async def load_from_postgres(self):
        """Load existing messages from PostgreSQL"""
        async with AsyncSession() as db:
            result = await db.execute(
                select(ChatMessage).where(ChatMessage.session_id == self.session_id).order_by(ChatMessage.timestamp)
            )
            messages = result.scalars().all()
            
            for msg in messages:
                if msg.message_type == "human":
                    self.buffer_memory.chat_memory.add_user_message(msg.content)
                elif msg.message_type == "ai":
                    self.buffer_memory.chat_memory.add_ai_message(msg.content)
