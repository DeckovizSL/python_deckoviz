from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from schemas.user import User
from utils.token import get_current_user

from deckoviz_ai.contextual_chat._agent import ContextualChatAgent

router = APIRouter()
chat_agent = ContextualChatAgent()


# -------- Request Schema --------
class ContextualChatRequest(BaseModel):
    message: str


@router.post("/chat", summary="Context-aware conversational chat")
async def contextual_chat(
    req: ContextualChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Context-aware chat that maintains conversation history per user.
    """

    if not req.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        response = chat_agent.get_response(
            user_id=str(current_user.id),
            message=req.message
        )

        return {
            "response": response
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )