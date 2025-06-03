from fastapi import APIRouter,Depends
from deckoviz_ai.personal_painter import PersonalPainterConversation
from utils.settings import get_settings
from utils.token import get_current_user
from schemas.chat import RequestMessage,PersonalPainterChatResponse,AIConversationMessage
from schemas.user import User

router = APIRouter()

settings = get_settings()
pp_chat = PersonalPainterConversation(database_url=settings.sqlite_url)


@router.post("/")  
async def painter_chat(req: RequestMessage , current_user: User = Depends(get_current_user)): 
    await pp_chat.save_chat_message(current_user.id, req.message, "user")
    response = pp_chat.next_chat(chat_history=[{"content": req.message, "role": "user"}])
    await pp_chat.save_chat_message(current_user.id, response.content, "assistant")
    return {"question": req.message, "message": response.content}  