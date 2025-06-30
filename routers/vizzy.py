from fastapi import APIRouter, Depends, HTTPException
from schemas.user import User
from utils.token import get_current_user
from deckoviz_ai.vizzy._agent import VizzyAgent, VizzyCommand

# Import existing services and request models
from deckoviz_ai.poster import PosterPrompt, PosterPromptRequest
from deckoviz_ai.moodboard import MoodboardPrompt, MoodboardPromptRequest
from routers.generate_art import generate_art
from schemas.art import GenerateArtRequest
from routers.painter_chat import create_painter_chat_session

router = APIRouter()
vizzy_agent = VizzyAgent()

@router.post("/command", summary="Process a voice command via Vizzy")
async def process_vizzy_command(
    req: VizzyCommand,
    current_user: User = Depends(get_current_user)
):
    """
    Receives a transcribed text command, uses the VizzyAgent to interpret it,
    and then dispatches the command to the appropriate service.
    """
    if not req.text:
        raise HTTPException(status_code=400, detail="Text command cannot be empty.")

    # 1. Get the structured action from the Vizzy LLM agent
    action_data = vizzy_agent.get_action(req.text)

    action_name = action_data.get("action")
    parameters = action_data.get("parameters", {})

    if action_name == "error":
        raise HTTPException(
            status_code=400,
            detail=parameters.get("message", "Command not understood or failed to process.")
        )

    # 2. Dispatch the action to the corresponding service
    try:
        if action_name == "generate_poster":
            # Construct the request for the poster service
            poster_req = PosterPromptRequest(**parameters)
            poster_service = PosterPrompt()
            prompt = poster_service.generate_prompt(poster_req)
            art_req = GenerateArtRequest(
                prompt=prompt,
                height=poster_req.height,
                width=poster_req.width
            )
            return await generate_art(art_req, current_user)

        elif action_name == "generate_moodboard":
            # Construct the request for the moodboard service
            moodboard_req = MoodboardPromptRequest(**parameters)
            moodboard_service = MoodboardPrompt()
            prompt = moodboard_service.generate_prompt(moodboard_req)
            art_req = GenerateArtRequest(
                prompt=prompt,
                height=moodboard_req.height,
                width=moodboard_req.width
            )
            return await generate_art(art_req, current_user)

        elif action_name == "start_personal_painter":
            # Call the function to create a new session
            session_info = await create_painter_chat_session(current_user)
            return {
                "action": "navigate",
                "destination": "personal_painter_chat",
                "session_id": session_info.get("session_id")
            }

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Action '{action_name}' is not recognized or implemented."
            )
    except Exception as e:
        # This will catch errors from the downstream services
        raise HTTPException(status_code=500, detail=f"Error executing action '{action_name}': {str(e)}") 