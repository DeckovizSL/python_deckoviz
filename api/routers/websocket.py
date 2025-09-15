# WebSocket router setup: import necessary FastAPI classes and logger
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.core.logger import logger
from api.utils.websocket_manager import manager

# Initialize router and logger
router = APIRouter()


# # Function to notify clients in a room with arbitrary JSON payload
async def notify_new_images(room_id: str, payload: dict):
    """
    Broadcast the given JSON payload to all WebSocket clients in the room.
    """
    await manager.broadcast(room_id, payload)

 