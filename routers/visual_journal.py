from fastapi import APIRouter, Depends, HTTPException
from schemas.visual_journal import UserInput, VisualJournalEntry
from deckoviz_ai.visual_journal._service import VisualJournalService
from schemas.user import User
from utils.token import get_current_user

router = APIRouter()

@router.post("/", response_model=VisualJournalEntry)
async def generate_visual_journal_entry(
    user_input: UserInput,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a visual journal entry based on the user's text input.
    Creates artistic, symbolic visuals representing the user's day, emotions, and reflections.
    """
    try:
        service = VisualJournalService()
        result = await service.generate_visual_journal(user_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating visual journal: {str(e)}")
