from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from api.utils.device_tokens import decode_jwt, create_jwt
from common.apps.authentication.models import User
from django.utils import timezone
import time, uuid, bcrypt, secrets, logging
from api.utils.qr_redis import QRRedisManager
from api.databases.configs import get_redis_client
from api.utils.websocket_manager import ConnectionManager
from api.utils.json_helpers import safe_parse_json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.utils.device_tokens import decode_jwt
import time, logging

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)

# Managers
redis_client = get_redis_client()
redis_manager = QRRedisManager(redis_client)
manager = ConnectionManager()

# Maps ws.id → room_id
ws_room_mapping = {}

@router.websocket("/device/")
async def websocket_device(websocket: WebSocket):
    """
    Shared WebSocket endpoint for both TV and Mobile.
    - TV connects with only session_id
    - Mobile connects with session_id + access_token
    """
    await websocket.accept()

    session_id = websocket.query_params.get("session_id")
    access_token = websocket.query_params.get("access_token")

    if not session_id:
        await websocket.send_json({"error": "Missing session_id"})
        await websocket.close()
        return

    # Default role = tv (no token)
    role = "tv"
    user_id = None

    if access_token:
        try:
            payload = decode_jwt(access_token)
            role = payload.get("role", "mobile")
            user_id = payload.get("user_id")
        except Exception as e:
            await websocket.send_json({"error": f"Invalid or expired token: {str(e)}"})
            await websocket.close()
            return

    # Ensure room exists in Redis
    if not redis_manager.room_exists(session_id):
        redis_manager.add_room(session_id)

    connection_id = str(id(websocket))
    ws_room_mapping[connection_id] = session_id

    # Update metadata
    metadata = redis_manager.get_room_metadata(session_id) or {}
    metadata.update({
        "last_activity": time.time(),
        f"{role}_connected": True,
        "connection_count": metadata.get("connection_count", 0) + 1
    })
    if user_id:
        metadata["user_id"] = user_id
    redis_manager.store_room_metadata(session_id, metadata)

    # Register connection
    await manager.connect(websocket, session_id, is_accepted=True)

    # Send welcome message
    welcome = {
        "type": "connected",
        "message": f"{role.capitalize()} connected to session {session_id}",
        "role": role,
        "connection_id": connection_id,
        "timestamp": time.time()
    }
    redis_manager.store_room_message(session_id, welcome)
    await manager.broadcast(session_id, welcome)

    # Send history
    history = redis_manager.get_room_messages(session_id, 10)
    if history:
        await websocket.send_json({"type": "history", "messages": history})

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = safe_parse_json(raw_data)

            if not data:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            message = {
                "type": "message",
                "role": role,
                "sender_id": connection_id,
                "data": data,
                "timestamp": time.time()
            }
            redis_manager.store_room_message(session_id, message)

            # Broadcast to everyone else
            await manager.broadcast(session_id, message, exclude=[websocket])

    except WebSocketDisconnect:
        # Cleanup
        await manager.disconnect(websocket, session_id)
        ws_room_mapping.pop(connection_id, None)

        metadata = redis_manager.get_room_metadata(session_id) or {}
        count = max(0, metadata.get("connection_count", 1) - 1)
        metadata.update({
            "last_activity": time.time(),
            f"{role}_disconnected_at": time.time(),
            "connection_count": count
        })
        redis_manager.store_room_metadata(session_id, metadata)

        disconnect = {
            "type": "disconnect",
            "message": f"{role.capitalize()} disconnected",
            "role": role,
            "connection_id": connection_id,
            "session_id": session_id,
            "timestamp": time.time()
        }
        redis_manager.store_room_message(session_id, disconnect)
        await manager.broadcast(session_id, disconnect)

