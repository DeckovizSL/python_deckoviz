from fastapi import APIRouter, WebSocket
from api.utils.device_tokens import decode_jwt

router = APIRouter(prefix="/device", tags=["Device WebSocket"])

@router.websocket("/ws/device")
async def device_ws(websocket: WebSocket, token: str):
    try:
        payload = decode_jwt(token)
    except:
        await websocket.close(code=1008)
        return

    user_id = payload.get("user_id")
    role = payload.get("role")

    await websocket.accept()
    await websocket.send_text(f"Connected as {role} with user {user_id}")
