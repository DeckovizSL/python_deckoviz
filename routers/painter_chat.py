from fastapi import APIRouter,Depends, HTTPException
from deckoviz_ai.personal_painter import PersonalPainterConversation, PersonalPainterDatabase, PersonalPainterPrompt
from utils.token import get_current_user
from schemas.chat import RequestMessage, PersonalPainterChatResponse, AIConversationMessage
from schemas.art import GenerateArtRequest
from schemas.user import User
import uuid
from datetime import datetime, timezone
from runware import Runware, IImageInference
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

pp_chat = PersonalPainterConversation()
pp_db = PersonalPainterDatabase()
pp_prompt = PersonalPainterPrompt()

@router.get("/session")
async def create_painter_chat_session(current_user: User = Depends(get_current_user)):
    session_id = str(uuid.uuid4())
    print(f"Creating new session {session_id} for user {current_user.id}")
    
    try:
        await pp_db.save_session(current_user.id, session_id)
        
        # Verify session was created
        query = "SELECT * FROM chat_sessions WHERE id = :session_id AND tenant = :tenant"
        result = await pp_db.fetch_one(query=query, values={"session_id": session_id, "tenant": current_user.id})
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        print(f"Session created successfully: {result}")
        return {"session_id": session_id}
    except Exception as e:
        print(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.post("/{session_id}")  
async def painter_chat(session_id: str, req: RequestMessage, current_user: User = Depends(get_current_user)): 
    print(f"Checking session {session_id} for user {current_user.id}")
    
    # Verify session exists and is active
    query = "SELECT * FROM chat_sessions WHERE id = :session_id AND tenant = :tenant AND is_active = True"
    result = await pp_db.fetch_one(query=query, values={"session_id": session_id, "tenant": current_user.id})
    
    if not result:
        print(f"Session not found or inactive. Query result: {result}")
        raise HTTPException(status_code=404, detail="Session not found or inactive")
    
    print(f"Session found: {result}")
    
    # Load messages for this specific session
    query = """
    SELECT * FROM chat_messages 
    WHERE tenant = :tenant AND session_id = :session_id 
    ORDER BY created_at ASC
    """
    messages = await pp_db.fetch_all(query=query, values={"tenant": current_user.id, "session_id": session_id})
    chat_history = [{"content": msg["message"], "role": msg["role"]} for msg in messages]
    
    if req.message:
        chat_history.append({"content": req.message, "role": "user"})
        # Save message with session_id
        await pp_db.save_chat_message(current_user.id, req.message, "user", session_id)
    
    response = pp_chat.next_chat(chat_history=chat_history)
    # Save response with session_id
    await pp_db.save_chat_message(current_user.id, response.content, "assistant", session_id)
    return {"question": req.message, "message": response.content, "chat_history": chat_history}

@router.delete("/session/{session_id}")
async def delete_painter_chat_session(session_id: str, current_user: User = Depends(get_current_user)):
    print(f"Attempting to delete session {session_id} for user {current_user.id}")
    
    # Verify session exists and belongs to user
    query = "SELECT * FROM chat_sessions WHERE id = :session_id AND tenant = :tenant"
    result = await pp_db.fetch_one(query=query, values={"session_id": session_id, "tenant": current_user.id})
    
    if not result:
        print(f"Session not found for deletion. Query result: {result}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Close the session
    await pp_db.close_session(session_id)
    
    # Optionally, you can also delete the chat messages for this session
    query = "DELETE FROM chat_messages WHERE session_id = :session_id AND tenant = :tenant"
    await pp_db.execute(query=query, values={"session_id": session_id, "tenant": current_user.id})
    
    print(f"Session {session_id} deleted successfully")
    return {"session_id": session_id, "status": "deleted"}

@router.post("/{session_id}/generate-art")
async def generate_art_from_chat(session_id: str, current_user: User = Depends(get_current_user)):
    # Verify session exists and is active
    query = "SELECT * FROM chat_sessions WHERE id = :session_id AND tenant = :tenant AND is_active = True"
    result = await pp_db.fetch_one(query=query, values={"session_id": session_id, "tenant": current_user.id})
    
    if not result:
        raise HTTPException(status_code=404, detail="Session not found or inactive")
    
    # Get chat history for this specific session
    query = """
    SELECT * FROM chat_messages 
    WHERE tenant = :tenant AND session_id = :session_id 
    ORDER BY created_at ASC
    """
    messages = await pp_db.fetch_all(query=query, values={"tenant": current_user.id, "session_id": session_id})
    chat_history = [{"content": msg["message"], "role": msg["role"]} for msg in messages]
    
    # Generate art prompt from chat history
    art_prompt = pp_prompt.next_chat(chat_history=chat_history)
    
    # Initialize Runware
    runware = Runware(api_key=os.getenv("RUNWARE_API_KEY"))
    await runware.connect()
    
    # Default negative prompt
    neg_prompt = "blurry, low resolution, pixelated, distorted faces, missing limbs, bad anatomy, extra fingers, low detail, poorly lit, overexposed, underexposed, noisy, artifacts, watermark, cropped, low contrast, flat colors, dull, amateur"
    
    # Create image generation request
    request_image = IImageInference(
        positivePrompt=art_prompt.prompt,
        model="civitai:101055@128078",
        numberResults=1,
        negativePrompt=neg_prompt,
        height=512,  # Default height
        width=512,   # Default width
    )
    
    # Generate image
    images = await runware.imageInference(requestImage=request_image)
    return images