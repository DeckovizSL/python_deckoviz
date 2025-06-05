from fastapi import APIRouter,Depends, HTTPException,UploadFile,File
from schemas.user import User
from utils.token import get_current_user
import os 
from deckoviz_ai.metadata_generator import MetadataGenerator
from schemas.image import MetadataGenerateRequest
from dotenv import load_dotenv
import tempfile

load_dotenv()

router = APIRouter()

metadata_generator = MetadataGenerator()

@router.post("/generate")
async def generate_metadata(image: UploadFile=File(...),current_user: User = Depends(get_current_user)):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(image.file.read())
            temp_file_path = temp_file.name

        response = metadata_generator.generate(temp_file_path)
        os.unlink(temp_file_path)
        return {"metadata":response}
    except Exception as e:
        return HTTPException(status_code=400,detail=str(e))

@router.post("/generate-from-url")
async def generate_metadata(req: MetadataGenerateRequest,current_user: User = Depends(get_current_user)):
    try:
        response = metadata_generator.generate(req.image)
        return {"metadata":response}
    except Exception as e:
        return HTTPException(status_code=400,detail=str(e))
