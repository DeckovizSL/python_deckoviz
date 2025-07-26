from fastapi import APIRouter, HTTPException, Depends
from schemas.story_visualizer import StorySegmentInput, StoryVisualizationOutput
from deckoviz_ai.story_visualizer._service import StoryVisualizerService
from utils.token import get_current_user
from schemas.user import User

router = APIRouter()

@router.post("/", response_model=StoryVisualizationOutput)
async def process_story_segment(input_data: StorySegmentInput, current_user: User = Depends(get_current_user)):
    """
    Process a segment of narrated story and return a visualization prompt and image.
    """
    try:
        service = StoryVisualizerService()
        result = await service.process_story_segment(input_data.text, input_data.previous_context)
        return StoryVisualizationOutput(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing story segment: {str(e)}") 