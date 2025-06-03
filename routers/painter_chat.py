from fastapi import APIRouter,Depends
from deckoviz_ai.personal_painter import PersonalPainterConversation,PersonalPainterDatabase
from utils.token import get_current_user
from schemas.chat import RequestMessage,PersonalPainterChatResponse,AIConversationMessage
from schemas.user import User
import uuid
from datetime import datetime,timezone

router = APIRouter()

pp_chat = PersonalPainterConversation()
pp_db = PersonalPainterDatabase()

@router.get("/session")
async def painter_chat(current_user: User = Depends(get_current_user)):
    session_id = str(uuid.uuid4())
    await pp_db.save_session(current_user.id,session_id)
    return {"session_id": session_id}

@router.post("/{session_id}")  
async def painter_chat(session_id: str, req: RequestMessage, current_user: User = Depends(get_current_user)): 
    # Initialize chat history
    chat_history = []
    
    # Get or create chat session for this user
    query = "SELECT * FROM chat_sessions WHERE tenant = :tenant ORDER BY created_at DESC LIMIT 1"
    result = await pp_db.fetch_one(query=query, values={"tenant": current_user.id})
    
    if result and result["is_active"]:
        session_id = result["id"]
    else:
        # Create a new chat session
        session_id = str(uuid.uuid4())
        query = """
        INSERT INTO chat_sessions(id, tenant, is_active, created_at)
        VALUES (:id, :tenant, :is_active, :created_at)
        """
        values = {
            "id": session_id,
            "tenant": current_user.id,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        await pp_db.execute(query=query, values=values)
    
    # Load previous messages for this session
    query = "SELECT * FROM chat_messages WHERE tenant = :tenant ORDER BY created_at ASC"
    messages = await pp_db.fetch_all(query=query, values={"tenant": current_user.id})
    chat_history = [{"content": msg["message"], "role": msg["role"], "tenant": msg["tenant"]} for msg in messages]
    if req.message:
        chat_history.append({"content": req.message, "role": "user", "tenant": current_user.id})
        await pp_db.save_chat_message(current_user.id, req.message, "user")
    
    response = pp_chat.next_chat(chat_history=chat_history)
    await pp_db.save_chat_message(current_user.id, response.content, "assistant")
    return {"question": req.message, "message": response.content, "chat_history": chat_history} 


@router.delete("/session/{session_id}")
async def painter_chat(session_id: str, current_user: User = Depends(get_current_user)):
    await pp_db.close_session(session_id)
    return {"session_id": session_id}