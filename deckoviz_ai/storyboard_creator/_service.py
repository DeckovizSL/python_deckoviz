import os
from sqlalchemy.orm import Session
from . import _schemas as storyboard_schemas
from models import storyboard as storyboard_models
from deckoviz_ai.llm._llm import GeminiLLM
from . import _prompt as storyboard_prompt
from runware import Runware, IImageInference

def create_storyboard(db: Session, storyboard: storyboard_schemas.StoryboardCreate, tenant_id: str):
    db_storyboard = storyboard_models.Storyboard(
        title=storyboard.title,
        description=storyboard.description,
        width=storyboard.width,
        height=storyboard.height,
        tenant=tenant_id
    )
    db.add(db_storyboard)
    db.commit()
    db.refresh(db_storyboard)
    return db_storyboard

def get_storyboard(db: Session, storyboard_id: int, tenant_id: str):
    return db.query(storyboard_models.Storyboard).filter(
        storyboard_models.Storyboard.id == storyboard_id,
        storyboard_models.Storyboard.tenant == tenant_id
    ).first()

def get_storyboards_by_tenant(db: Session, tenant_id: str):
    return db.query(storyboard_models.Storyboard).filter(storyboard_models.Storyboard.tenant == tenant_id).all()

async def add_frame_to_storyboard(db: Session, storyboard_id: int, frame: storyboard_schemas.StoryboardFrameCreate, tenant_id: str):
    # Get the storyboard to access its dimensions
    db_storyboard = get_storyboard(db=db, storyboard_id=storyboard_id, tenant_id=tenant_id)
    if not db_storyboard:
        # This case should ideally be handled by the router, but it's good practice to have it here too.
        return None

    # Generate image using runware
    runware = Runware(api_key=os.getenv("RUNWARE_API_KEY"))
    await runware.connect()
    neg_prompt = "abstract patterns, random shapes, meaningless designs, geometric patterns, swirls, spirals, kaleidoscope, mandala, fractal, blurry, low resolution, pixelated, distorted, deformed, bad anatomy, poorly drawn, amateur, sketchy, rough, unfinished, low detail, flat lighting, overexposed, underexposed, noisy, grainy, artifacts, watermark, signature, text, letters, words, cropped, borders, frame, low contrast, washed out colors, dull, boring, generic, cliché, bad composition, cluttered, messy, chaotic, unclear subject, no focal point, confusing"
    request_image = IImageInference(
        positivePrompt=frame.prompt,
        model="civitai:101055@128078",
        numberResults=1,
        negativePrompt=neg_prompt,
        height=db_storyboard.height,
        width=db_storyboard.width,
    )
    try:
        images = await runware.imageInference(requestImage=request_image)
        image_url = images[0].imageURL if images and hasattr(images[0], 'imageURL') else ""
    except Exception as e:
        print(f"Error generating image with runware: {e}")
        image_url = ""


    db_frame = storyboard_models.StoryboardFrame(
        prompt=frame.prompt,
        image_url=image_url,
        storyboard_id=storyboard_id
    )
    db.add(db_frame)
    db.commit()
    db.refresh(db_frame)
    return db_frame

def suggest_story_frame(short_instruction: str):
    llm = GeminiLLM(model_name="gemini-1.5-flash")
    prompt = storyboard_prompt.STORY_FRAME_SUGGESTION_PROMPT.format(short_instruction=short_instruction)
    
    response = llm._call(prompt)
    
    return {"suggested_prompt": response.strip()} 