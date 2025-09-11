"""
Server Implementation for TV-Mobile App Pairing using Redis
This version uses Redis for storing all data except WebSocket objects
"""

import time
import uuid
import logging
import json
from typing import Dict, Any, List, Optional, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from schemas.qr_code import GenerateQRRequest, GenerateQRResponse, PairingRequest, PairingResponse
from utils.qr_code import TVQRCodeGenerator
from utils.token import get_current_user,create_access_token
from utils.qr_redis import QRRedisManager
from databases.configs import get_redis_client
from utils.websocket_manager import manager
from utils.json_helpers import safe_parse_json

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("qr_code_redis_router")

router = APIRouter()

# We need to keep WebSocket connection objects in memory since they can't be serialized
# But we'll use Redis to track all metadata about rooms and connections
# This dict only maps room_ids to WebSocket objects for message routing
active_connections: Dict[str, List[WebSocket]] = {}

# WebSocket to room mapping for quick lookup during disconnection
ws_room_mapping: Dict[str, str] = {}

# Get Redis manager dependency
def get_qr_redis_manager():
    redis_client = get_redis_client()
    return QRRedisManager(redis_client)

# API Endpoints
@router.post("/qr/generate-qr", response_model=GenerateQRResponse)
async def generate_pairing_qr(request: GenerateQRRequest, redis_manager: QRRedisManager = Depends(get_qr_redis_manager)):
    """
    Generate a QR code for TV pairing (encodes only qr_token).
    """
    qr_generator = TVQRCodeGenerator()
    _, base64_qr, pairing_data, qr_token = qr_generator.generate_qr_pairing(
        instruction_text=request.instructions,
        save_file=False
    )
    # Store qr_token mapped to user_id in Redis (short expiry)
    redis_manager.store_qr_token(qr_token, request.user_id)
    expiration_time = int(time.time()) + redis_manager.QR_TOKEN_EXPIRY
    logger.debug(f"Generated QR token {qr_token} for user {request.user_id}")
    return GenerateQRResponse(
        qr_token=qr_token,
        qr_code_base64=base64_qr,
        expiration_time=expiration_time
    )

@router.post("/qr/pair-tv", response_model=PairingResponse)
async def pair_tv(request: PairingRequest, user_id: str = Depends(get_current_user), redis_manager: QRRedisManager = Depends(get_qr_redis_manager)):
    """
    Pair a TV device using qr_token (called by mobile app after scanning QR).
    """
    # Validate qr_token and get mapped user_id
    mapped_user_id = redis_manager.get_user_id_by_qr_token(request.qr_token)
    if not mapped_user_id:
        return PairingResponse(success=False, message="Invalid or expired QR token.")
    if mapped_user_id != user_id:
        return PairingResponse(success=False, message="User mismatch for QR token.")
    # Expire the QR token after successful pairing
    redis_manager.expire_qr_token(request.qr_token)
    # Notify TV via WebSocket (if implemented)
    # ...existing code for notification...
    logger.debug(f"Paired TV for user {user_id} using QR token {request.qr_token}")
    return PairingResponse(success=True, message="TV paired successfully.")

@router.get("/qr/device/{device_id}/room")
async def get_room_for_device(device_id: str, redis_manager: QRRedisManager = Depends(get_qr_redis_manager)):
    """
    Check if a room ID has been assigned to a device.
    This is polled by the TV app after displaying the QR code.

    """
    device_data = redis_manager.get_device_data(device_id)
    
    if not device_data:
        raise HTTPException(status_code=404, detail="Device ID not found")
    
    room_id = device_data.get("room_id")
    user_id = device_data.get("user_id")
    
    if room_id is None:
        # No room assigned yet
        return {"paired": False}
    
    # Update the last access time for this device
    redis_manager.update_device_timestamp(device_id)
    
    # If we have room metadata, include additional information
    room_metadata = redis_manager.get_room_metadata(room_id) or {}
    
    return {
        "paired": True,
        "room_id": room_id,
        "token": create_access_token(user_id),
        "connection_count": redis_manager.get_room_connection_count(room_id),
        "created_at": room_metadata.get("created_at", time.time()),
        "last_activity": room_metadata.get("last_activity", time.time())
    }

# WebSocket endpoints 
@router.websocket("/ws/tv/")  # Support trailing slash
async def websocket_tv_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for TV app connections.
    The TV app connects here after receiving a room ID.
    """
    # Get Redis client directly for WebSocket endpoint
    redis_client = get_redis_client()
    redis_manager = QRRedisManager(redis_client)
    
    # Accept WebSocket connection
    await websocket.accept()
    
    # Get room ID from query parameter
    room_id = websocket.query_params.get("room")
    device_id = websocket.query_params.get("device_id")  # Optional, can help with tracking
    
    if not room_id:
        await websocket.send_json({"error": "No room ID provided"})
        await websocket.close()
        return
    
    # Create a unique connection ID for this WebSocket connection
    connection_id = str(id(websocket))
    
    # Check if room exists in Redis
    if not redis_manager.room_exists(room_id):
        # Try to find the room by checking all devices
        found_device_id = redis_manager.get_device_by_room(room_id)
        
        if not found_device_id:
            await websocket.send_json({"error": "Invalid room ID"})
            await websocket.close()
            return
            
        # If we found a device with this room, update the device ID if needed
        if device_id and device_id != found_device_id:
            logger.debug(f"Device ID mismatch: {device_id} vs {found_device_id}")
    
    # Use the ConnectionManager to handle this connection properly
    # Pass is_accepted=True since we manually accepted the connection above
    await manager.connect(websocket, room_id, is_accepted=True)
    
    # Store connection ID for lookup during disconnection
    ws_room_mapping[connection_id] = room_id
    
    # Add and track connections in Redis
    connection_count = redis_manager.increment_room_connections(room_id)
    
    # Store or update room metadata
    room_metadata = redis_manager.get_room_metadata(room_id) or {}
    room_metadata.update({
        "last_tv_connection": time.time(),
        "connection_count": connection_count,
        "has_tv": True,
        "last_activity": time.time()
    })
    
    if device_id:
        room_metadata["tv_device_id"] = device_id
        
    redis_manager.store_room_metadata(room_id, room_metadata)
    
    # Get recent room messages to send to the new connection
    recent_messages = redis_manager.get_room_messages(room_id, 10)
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "connected",
            "message": f"Connected to room {room_id}",
            "timestamp": time.time(),
            "connection_count": connection_count,
            "connection_type": "tv",
            "connection_id": connection_id
        }
        
        # Store the welcome message in Redis
        redis_manager.store_room_message(room_id, welcome_message)
        
        # Pass is_accepted=True since we manually accepted the connection above
        await manager.connect(websocket, room_id, is_accepted=True)
        
        # Send welcome message to this client
        await manager.broadcast(room_id, welcome_message)
        
        # Send recent message history
        if recent_messages:
            await manager.broadcast(room_id, {
                "type": "history",
                "messages": recent_messages,
                "count": len(recent_messages)
            })
        
        # Handle messages
        while True:
            # Get raw message text first
            raw_data = await websocket.receive_text()
            
            # Try to parse the JSON with our helper that handles common format issues
            data = safe_parse_json(raw_data)
            
            if data is None:
                # Log the error if parsing failed even with our helper
                logger.error(f"Invalid JSON from TV client in room {room_id}")
                logger.error(f"Raw data received: {raw_data}")
                
                # Send error message back to client
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format. Please check for syntax errors."
                })
                # Skip processing this message
                continue
                
            # Log the successfully parsed message
            logger.debug(f"Received message in room {room_id} from TV: {data}")
            
            # Create message with metadata
            message = {
                "type": "message",
                "data": data,
                "timestamp": time.time(),
                "sender_type": "tv",
                "sender_id": connection_id,
                "device_id": device_id
            }
            
            # Store message in Redis for history
            redis_manager.store_room_message(room_id, message)
            
            # Update room last activity timestamp
            room_metadata = redis_manager.get_room_metadata(room_id) or {}
            room_metadata["last_activity"] = time.time()
            redis_manager.store_room_metadata(room_id, room_metadata)
            
            # Broadcast to all clients in the room
            for client in manager.active_connections.get(room_id, []):
                if client != websocket:  # Don't send back to sender
                    await manager.broadcast(room_id, message)
                    
    except WebSocketDisconnect:
        # Clean up connection
        # Get connection ID for this WebSocket
        connection_id = str(id(websocket))
        
        # Get room ID from our mapping
        room_id = ws_room_mapping.get(connection_id, room_id)
        
        # Remove from active connections
        await manager.disconnect(websocket, room_id)
        
        # Remove from WebSocket to room mapping
        if connection_id in ws_room_mapping:
            del ws_room_mapping[connection_id]
        
        # Decrement connection count in Redis
        count = redis_manager.decrement_room_connections(room_id)
        
        # Update room metadata
        room_metadata = redis_manager.get_room_metadata(room_id) or {}
        room_metadata.update({
            "last_activity": time.time(),
            "connection_count": count,
            "tv_disconnected_at": time.time()
        })
        redis_manager.store_room_metadata(room_id, room_metadata)
        
        # Log disconnection
        logger.debug(f"TV client disconnected from room {room_id}. {count} connections remaining")
        
        # Notify other clients about disconnection
        disconnect_message = {
            "type": "disconnect",
            "message": "TV disconnected",
            "timestamp": time.time(),
            "connection_type": "tv",
            "connection_id": connection_id,
            "room_id": room_id
        }
        redis_manager.store_room_message(room_id, disconnect_message)
        
        # Broadcast disconnection to remaining clients
        await manager.broadcast(room_id, disconnect_message)

@router.websocket("/ws/mobile/")  # Support trailing slash
async def websocket_mobile_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for mobile app connections.
    Mobile app connects here after successful pairing.
    """
    # Get Redis client directly for WebSocket endpoint
    redis_client = get_redis_client()
    redis_manager = QRRedisManager(redis_client)
    
    await websocket.accept()
    
    # Get auth token from query parameter (simplified auth)
    token = websocket.query_params.get("token")
    if not token:
        await websocket.send_json({"error": "No authentication token provided"})
        await websocket.close()
        return
    
    # Create a unique connection ID for this WebSocket
    connection_id = str(id(websocket))
    
    # Get room ID from query parameter
    room_id = websocket.query_params.get("room")
    if not room_id:
        logger.debug("No room ID provided")
        await manager.broadcast(room_id, {"error": "No room ID provided"})
        await manager.disconnect(websocket, room_id)
        return
        
    # Verify the room exists in Redis
    if not redis_manager.room_exists(room_id):
        logger.debug("Room does not exist")
        await manager.broadcast(room_id, {"error": "Room does not exist"})
        await manager.disconnect(websocket, room_id)
        return
        
    # Add room if it doesn't exist yet
    redis_manager.add_room(room_id)

    # Initialize room metadata
    room_metadata = {
        "created_at": time.time(),
        "creator_token": token,
        "last_activity": time.time()
    }
    redis_manager.store_room_metadata(room_id, room_metadata)
    
    # Use the ConnectionManager to handle this connection properly
    # Pass is_accepted=True since we manually accepted the connection above
    await manager.connect(websocket, room_id, is_accepted=True)
    
    # Add WebSocket to room mapping for quick lookup during disconnection
    ws_room_mapping[connection_id] = room_id
    
    # Add and track connections in Redis
    connection_count = redis_manager.increment_room_connections(room_id)
    
    # Store or update room metadata
    room_metadata = redis_manager.get_room_metadata(room_id) or {}
    room_metadata.update({
        "last_mobile_connection": time.time(),
        "connection_count": connection_count,
        "has_mobile": True,
        "last_activity": time.time(),
        "mobile_token": token
    })
    redis_manager.store_room_metadata(room_id, room_metadata)
    
    # Get recent room messages to send to the new connection
    recent_messages = redis_manager.get_room_messages(room_id, 10)
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "connected",
            "message": f"Connected to room {room_id}",
            "timestamp": time.time(),
            "connection_count": connection_count,
            "connection_type": "mobile",
            "connection_id": connection_id
        }
        
        # Store the welcome message in Redis
        redis_manager.store_room_message(room_id, welcome_message)
        
        # Send welcome message to this client
        await manager.broadcast(room_id, welcome_message)
        
        # Send recent message history
        if recent_messages:
            await manager.broadcast(room_id, {
                "type": "history",
                "messages": recent_messages,
                "count": len(recent_messages)
            })
        
        # Handle messages
        while True:
            # Get raw message text first
            raw_data = await websocket.receive_text()
            
            # Try to parse the JSON with our helper that handles common format issues
            data = safe_parse_json(raw_data)
            
            if data is None:
                # Log the error if parsing failed even with our helper
                logger.error(f"Invalid JSON from mobile client in room {room_id}")
                logger.error(f"Raw data received: {raw_data}")
                
                # Send error message back to client
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format. Please check for syntax errors."
                })
                # Skip processing this message
                continue
                
            # Log the successfully parsed message
            logger.debug(f"Received message in room {room_id} from mobile: {data}")
            
            # Create message with metadata
            message = {
                "type": "message",
                "data": data,
                "timestamp": time.time(),
                "sender_type": "mobile",
                "sender_id": connection_id
            }
            
            # Store message in Redis for history
            redis_manager.store_room_message(room_id, message)
            
            # Update room last activity timestamp
            room_metadata = redis_manager.get_room_metadata(room_id) or {}
            room_metadata["last_activity"] = time.time()
            redis_manager.store_room_metadata(room_id, room_metadata)
            
            # Broadcast to all clients in the room
            for client in manager.active_connections.get(room_id, []):
                if client != websocket:  # Don't send back to sender
                    await client.send_json(message)
                    
    except WebSocketDisconnect:
        # Clean up connection
        # Get connection ID for this WebSocket
        connection_id = str(id(websocket))
        
        # Get room ID from our mapping
        room_id = ws_room_mapping.get(connection_id, room_id)
        
        # Remove from active connections
        await manager.disconnect(websocket, room_id)
        
        # Remove from WebSocket to room mapping
        if connection_id in ws_room_mapping:
            del ws_room_mapping[connection_id]
        
        # Decrement connection count in Redis
        count = redis_manager.decrement_room_connections(room_id)
        
        # Update room metadata
        room_metadata = redis_manager.get_room_metadata(room_id) or {}
        room_metadata.update({
            "last_activity": time.time(),
            "connection_count": count,
            "mobile_disconnected_at": time.time()
        })
        redis_manager.store_room_metadata(room_id, room_metadata)
        
        # Log disconnection
        logger.debug(f"Mobile client disconnected from room {room_id}. {count} connections remaining")
        
        # Notify other clients about disconnection
        disconnect_message = {
            "type": "disconnect",
            "message": "Mobile client disconnected",
            "timestamp": time.time(),
            "connection_type": "mobile",
            "connection_id": connection_id,
            "room_id": room_id
        }
        redis_manager.store_room_message(room_id, disconnect_message)
        
        # Broadcast disconnection to remaining clients
        await manager.broadcast(room_id, disconnect_message)

 