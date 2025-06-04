from fastapi import APIRouter,Depends,UploadFile,File
from schemas.user import User
from utils.token import get_current_user
import os 
from deckoviz_ai.metadata_generator import MetadataGenerator
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

metadata_generator = MetadataGenerator()

@router.post("/")
async def generate_metadata(image: UploadFile=File(...),current_user: User = Depends(get_current_user)):
    try:
        response = metadata_generator.generate(image.file)
        return response
    except Exception as e:
        return {"error": str(e)}
