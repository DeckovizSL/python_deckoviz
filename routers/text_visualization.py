from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from deckoviz_ai.text_visualization._service import TextVisualizationService
from deckoviz_ai.text_visualization._schemas import TextVisualizationInput, TextVisualizationOutput
from runware import Runware, IImageInference
import os
import tempfile
from typing import Optional

router = APIRouter(tags=["text-visualization"])
service = TextVisualizationService()

@router.post("/generate", response_model=TextVisualizationOutput)
async def generate_text_visualization(
    input_type: str = Form(..., description="'text' or 'pdf'"),
    text: Optional[str] = Form(None, description="Text input if input_type is 'text'"),
    pdf_file: Optional[UploadFile] = File(None, description="PDF file if input_type is 'pdf'"),
    visualization_prompt: str = Form(..., description="User's visualization instruction"),
    image_density: str = Form(..., description="'1_image_per_paragraph', '1_image_per_page', or '2_images_per_page'"),
    page_start: Optional[int] = Form(None, description="Start page (1-indexed, inclusive) for PDF"),
    page_end: Optional[int] = Form(None, description="End page (1-indexed, inclusive) for PDF"),
    height: Optional[int] = Form(768, description="Image height"),
    width: Optional[int] = Form(1024, description="Image width")
):
    pdf_file_path = None
    try:
        # Prepare input for service
        if input_type == "pdf":
            if not pdf_file:
                raise HTTPException(status_code=400, detail="PDF file is required for input_type 'pdf'.")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(await pdf_file.read())
                pdf_file_path = tmp.name
        data = {
            "input_type": input_type,
            "text": text,
            "pdf_file_path": pdf_file_path,
            "visualization_prompt": visualization_prompt,
            "image_density": image_density,
            "page_start": page_start,
            "page_end": page_end
        }
        # Generate prompts
        prompts_out = service.generate_prompts(TextVisualizationInput(**data))
        prompts = prompts_out.prompts
        # Generate images using Runware
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
                        height=height,
                        width=width,
                    )
                    images = await runware.imageInference(requestImage=request_image)
                    if images and hasattr(images[0], 'imageURL'):
                        image_urls.append(images[0].imageURL)
                    else:
                        image_urls.append("")
                except Exception:
                    image_urls.append("")
        except Exception:
            # If Runware fails entirely, fill with empty strings
            image_urls = ["" for _ in prompts]
        # Clean up temp file
        if pdf_file_path:
            os.remove(pdf_file_path)
        # Always return both fields
        return TextVisualizationOutput(prompts=prompts, image_urls=image_urls)
    except Exception as e:
        # If even prompt generation fails, return empty lists to satisfy schema
        return TextVisualizationOutput(prompts=[], image_urls=[]) 