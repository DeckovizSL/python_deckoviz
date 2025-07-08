from fastapi import APIRouter, Depends, HTTPException
from schemas.visual_journal import UserInput, VisualJournalEntry, VisualJournalHistoryEntry
from deckoviz_ai.visual_journal._service import VisualJournalService
from schemas.user import User
from utils.token import get_current_user
from typing import List

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
        result = await service.generate_visual_journal(user_input, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating visual journal: {str(e)}")

@router.get("/timeline", response_model=List[VisualJournalHistoryEntry])
async def get_journal_timeline(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """
    Get the visual journal timeline showing the user's journal history.
    """
    try:
        service = VisualJournalService()
        timeline = await service.get_journal_timeline(current_user.id, limit)
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting timeline: {str(e)}")

@router.get("/{entry_id}", response_model=VisualJournalEntry)
async def get_journal_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific visual journal entry by ID.
    """
    try:
        service = VisualJournalService()
        entry = await service.get_journal_entry_by_id(entry_id, current_user.id)
        if not entry:
            raise HTTPException(status_code=404, detail="Journal entry not found")
        return entry
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting journal entry: {str(e)}")
