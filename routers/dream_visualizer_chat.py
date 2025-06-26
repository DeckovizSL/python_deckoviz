from fastapi import APIRouter,Depends, HTTPException
from deckoviz_ai.dream_visualizer import DreamVisualizerChatConversation, DreamVisualizerChatDatabase, DreamVisualizerChatPrompt
from utils.token import get_current_user
from schemas.chat import RequestMessage
from schemas.user import User
from schemas.dream_visualizer import DreamVisualizeRequest
import uuid
from runware import Runware, IImageInference
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

dv_chat = DreamVisualizerChatConversation()
dv_db = DreamVisualizerChatDatabase()
dv_prompt = DreamVisualizerChatPrompt()

@router.get("/session", tags=["Dream Visualizer Chat"], summary="Create a new dream chat session")
async def create_dream_chat_session(current_user: User = Depends(get_current_user)):
    session_id = str(uuid.uuid4())
    try:
        await dv_db.save_session(current_user.id, session_id)
        query = "SELECT * FROM dream_chat_sessions WHERE id = :session_id AND tenant = :tenant"
        result = await dv_db.fetch_one(query=query, values={"session_id": session_id, "tenant": current_user.id})
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create dream session")
        return {"session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dream session: {str(e)}")

@router.post("/{session_id}", tags=["Dream Visualizer Chat"], summary="Post a message to a dream chat session")
async def dream_chat(session_id: str, req: RequestMessage, current_user: User = Depends(get_current_user)): 
    query = "SELECT * FROM dream_chat_sessions WHERE id = :session_id AND tenant = :tenant AND is_active = True"
    result = await dv_db.fetch_one(query=query, values={"session_id": session_id, "tenant": current_user.id})
    if not result:
        raise HTTPException(status_code=404, detail="Dream session not found or inactive")
    
    query = "SELECT * FROM dream_chat_messages WHERE tenant = :tenant AND session_id = :session_id ORDER BY created_at ASC"
    messages = await dv_db.fetch_all(query=query, values={"tenant": current_user.id, "session_id": session_id})
    chat_history = [{"content": msg["message"], "role": msg["role"]} for msg in messages]
    
    if req.message:
        chat_history.append({"content": req.message, "role": "user"})
        await dv_db.save_chat_message(current_user.id, req.message, "user", session_id)
    
    response = dv_chat.next_chat(chat_history=chat_history)
    await dv_db.save_chat_message(current_user.id, response.content, "assistant", session_id)
    return {"question": req.message, "message": response.content, "chat_history": chat_history}

@router.delete("/session/{session_id}", tags=["Dream Visualizer Chat"], summary="Delete a dream chat session")
async def delete_dream_chat_session(session_id: str, current_user: User = Depends(get_current_user)):
    query = "SELECT * FROM dream_chat_sessions WHERE id = :session_id AND tenant = :tenant"
    result = await dv_db.fetch_one(query=query, values={"session_id": session_id, "tenant": current_user.id})
    if not result:
        raise HTTPException(status_code=404, detail="Dream session not found")
    
    await dv_db.close_session(session_id)
    
    query = "DELETE FROM dream_chat_messages WHERE session_id = :session_id AND tenant = :tenant"
    await dv_db.execute(query=query, values={"session_id": session_id, "tenant": current_user.id})
    
    return {"session_id": session_id, "status": "deleted"}

@router.post("/{session_id}/visualize", tags=["Dream Visualizer Chat"], summary="Generate an image from a dream chat session")
async def visualize_dream(session_id: str, req: DreamVisualizeRequest, current_user: User = Depends(get_current_user)):
    query = "SELECT * FROM dream_chat_sessions WHERE id = :session_id AND tenant = :tenant AND is_active = True"
    result = await dv_db.fetch_one(query=query, values={"session_id": session_id, "tenant": current_user.id})
    if not result:
        raise HTTPException(status_code=404, detail="Dream session not found or inactive")
    
    query = "SELECT * FROM dream_chat_messages WHERE tenant = :tenant AND session_id = :session_id ORDER BY created_at ASC"
    messages = await dv_db.fetch_all(query=query, values={"tenant": current_user.id, "session_id": session_id})
    chat_history = [{"content": msg["message"], "role": msg["role"]} for msg in messages]
    
    art_prompt = dv_prompt.generate_prompt(chat_history=chat_history)
    
    runware = Runware(api_key=os.getenv("RUNWARE_API_KEY"))
    await runware.connect()
    
    neg_prompt = "blurry, low resolution, pixelated, distorted faces, missing limbs, bad anatomy, extra fingers, low detail, poorly lit, overexposed, underexposed, noisy, artifacts, watermark, cropped, low contrast, flat colors, dull, amateur"
    
    request_image = IImageInference(
        positivePrompt=art_prompt.prompt,
        model="civitai:101055@128078",
        numberResults=1,
        negativePrompt=neg_prompt,
        height=req.height,
        width=req.width,
    )
    
    images = await runware.imageInference(requestImage=request_image)
    return images 