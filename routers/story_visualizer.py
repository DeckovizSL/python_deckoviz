from fastapi import APIRouter, HTTPException
from schemas.story_visualizer import StorySegmentInput, StoryVisualizationOutput
from deckoviz_ai.story_visualizer._service import StoryVisualizerService

router = APIRouter()

@router.post("/", response_model=StoryVisualizationOutput)
async def process_story_segment(input_data: StorySegmentInput):
    """
    Process a segment of narrated story and return a visualization prompt and image.
    """
    try:
        service = StoryVisualizerService()
        result = await service.process_story_segment(input_data.text, input_data.previous_context)
        return StoryVisualizationOutput(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing story segment: {str(e)}") 