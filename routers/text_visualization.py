from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from deckoviz_ai.text_visualization._service import TextVisualizationService
from deckoviz_ai.text_visualization._schemas import TextVisualizationInput, TextVisualizationOutput, TextVisualizationRequestData
from runware import Runware, IImageInference
import os
import tempfile
from typing import Optional
from utils.token import get_current_user
from schemas.user import User

# The prefix is removed here and handled in main.py to avoid a double prefix.
router = APIRouter(tags=["text-visualization"])
service = TextVisualizationService()

@router.post("/generate", response_model=TextVisualizationOutput)
async def generate_text_visualization(
    req: TextVisualizationRequestData = Depends(),
    pdf_file: Optional[UploadFile] = File(None, description="Required if input_type is 'pdf'. The PDF file to upload."),
    current_user: User = Depends(get_current_user)
):
    """
    ### Generate Visualizations from Text or PDF

    This endpoint creates a series of images based on provided text or a PDF document, guided by a visualization prompt. It supports different content splitting strategies based on image density.

    **Input Modes:**

    You must specify `input_type` as either `"text"` or `"pdf"`.

    ---

    **1. Text Input (`input_type: "text"`)**

    *   **`text`**: Required. The raw text to visualize.
    *   **`image_density`**: Must be `"1_image_per_paragraph"`. An image will be generated for each paragraph (separated by double newlines).
    *   *`pdf_file`, `page_start`, `page_end` should not be provided.*

    ---

    **2. PDF Input (`input_type: "pdf"`)**

    *   **`pdf_file`**: Required. The PDF file to upload.
    *   **`image_density`**: Can be one of the following:
        *   `"1_image_per_paragraph"`: Generates one image per paragraph from the PDF text.
        *   `"1_image_per_page"`: Generates one image for each page in the specified range.
        *   `"2_images_per_page"`: Generates two images for each page (splits page text in half).
    *   **`page_start` / `page_end`**: Optional. The page range to process (1-indexed, inclusive). If not provided, the entire document is used.
    *   *`text` should not be provided.*
    """
    pdf_file_path = None
    try:
        if req.input_type == "pdf":
            if not pdf_file:
                raise HTTPException(status_code=400, detail="A 'pdf_file' is required when input_type is 'pdf'.")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(await pdf_file.read())
                pdf_file_path = tmp.name
        elif req.input_type == "text" and not req.text:
            raise HTTPException(status_code=400, detail="The 'text' field is required when input_type is 'text'.")

        data = {
            "input_type": req.input_type,
            "text": req.text,
            "pdf_file_path": pdf_file_path,
            "visualization_prompt": req.visualization_prompt,
            "image_density": req.image_density,
            "page_start": req.page_start,
            "page_end": req.page_end
        }
        
        prompts = service.generate_prompts(TextVisualizationInput(**data))
        
        image_urls = []
        try:
            runware = Runware(api_key=os.getenv("RUNWARE_API_KEY"))
            await runware.connect()
            neg_prompt = "blurry, low resolution, pixelated, distorted faces, missing limbs, bad anatomy, extra fingers, low detail, poorly lit, overexposed, underexposed, noisy, artifacts, watermark, cropped, low contrast, flat colors, dull, amateur"
            for prompt in prompts:
                try:
                    request_image = IImageInference(
                        positivePrompt=prompt,
                        model="civitai:101055@128078",
                        numberResults=1,
                        negativePrompt=neg_prompt,
                        height=req.height,
                        width=req.width,
                    )
                    images = await runware.imageInference(requestImage=request_image)
                    if images and hasattr(images[0], 'imageURL'):
                        image_urls.append(images[0].imageURL)
                    else:
                        image_urls.append("")
                except Exception:
                    image_urls.append("")
        except Exception:
            image_urls = ["" for _ in prompts]
        
        return TextVisualizationOutput(prompts=prompts, image_urls=image_urls)
    
    except Exception as e:
        return TextVisualizationOutput(prompts=[], image_urls=[])
    
    finally:
        if pdf_file_path and os.path.exists(pdf_file_path):
            os.remove(pdf_file_path) 