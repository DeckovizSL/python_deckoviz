from fastapi import WebSocket
from typing import Dict, Set
from api.core.logger import logger

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, is_accepted: bool = False):
        logger.debug(f"Managing websocket connection for room {room_id}")
        # Only accept the connection if it hasn't been accepted yet
        if not is_accepted:
            await websocket.accept()
        
        # Add to active connections
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                logger.debug(f"Broadcasting message to room {room_id}")
                try:
                    await connection.send_json(message)
                except:
                    await self.disconnect(connection, room_id)

# Create a singleton instance of the connection manager
manager = ConnectionManager()
