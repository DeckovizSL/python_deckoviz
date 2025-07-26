from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database.connection import get_db
from deckoviz_ai.storyboard_creator import _service as storyboard_service
from deckoviz_ai.storyboard_creator import _schemas as storyboard_schemas
from utils.token import get_current_user
from schemas.user import User

router = APIRouter(
    prefix="/storyboards",
    tags=["storyboards"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=storyboard_schemas.Storyboard)
def create_storyboard(storyboard: storyboard_schemas.StoryboardCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return storyboard_service.create_storyboard(db=db, storyboard=storyboard, tenant_id=current_user.id)

@router.get("/", response_model=List[storyboard_schemas.Storyboard])
def get_storyboards_for_user(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return storyboard_service.get_storyboards_by_tenant(db=db, tenant_id=current_user.id)

@router.get("/{storyboard_id}", response_model=storyboard_schemas.Storyboard)
def get_storyboard(storyboard_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_storyboard = storyboard_service.get_storyboard(db=db, storyboard_id=storyboard_id, tenant_id=current_user.id)
    if db_storyboard is None:
        raise HTTPException(status_code=404, detail="Storyboard not found")
    return db_storyboard

@router.post("/{storyboard_id}/frames", response_model=storyboard_schemas.StoryboardFrame)
async def add_frame_to_storyboard(storyboard_id: int, frame: storyboard_schemas.StoryboardFrameCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # First, verify the user owns the storyboard
    db_storyboard = storyboard_service.get_storyboard(db=db, storyboard_id=storyboard_id, tenant_id=current_user.id)
    if db_storyboard is None:
        raise HTTPException(status_code=404, detail="Storyboard not found or you do not have permission to access it.")
    return await storyboard_service.add_frame_to_storyboard(db=db, storyboard_id=storyboard_id, frame=frame, tenant_id=current_user.id)

@router.post("/ai-generate-story", response_model=storyboard_schemas.AIStoryFrameSuggestion)
def ai_generate_story(request: storyboard_schemas.AIStoryGenerationRequest, current_user: User = Depends(get_current_user)):
    return storyboard_service.suggest_story_frame(request.short_instruction) 