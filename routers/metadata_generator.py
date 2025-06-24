from fastapi import APIRouter,Depends, HTTPException,UploadFile,File
from schemas.user import User
from utils.token import get_current_user
import os 
from deckoviz_ai.metadata_generator import MetadataGenerator
from schemas.image import MetadataGenerateRequest
from dotenv import load_dotenv
import tempfile
import hashlib
import time

load_dotenv()

router = APIRouter()

# Create a new instance for each request to avoid state sharing
def get_metadata_generator():
    return MetadataGenerator()

@router.post("/generate")
async def generate_metadata(image: UploadFile=File(...),current_user: User = Depends(get_current_user)):
    request_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    print(f"\n[{request_id}] Starting file upload request")
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await image.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            print(f"[{request_id}] Wrote {len(content)} bytes to temp file: {temp_file_path}")
            print(f"[{request_id}] First 50 bytes (hex): {content[:50].hex()}")

        # Get a fresh generator instance
        metadata_generator = get_metadata_generator()
        print(f"[{request_id}] Created new MetadataGenerator instance")
        
        response = metadata_generator.generate(temp_file_path)
        print(f"[{request_id}] Generated metadata successfully")
        
        os.unlink(temp_file_path)
        print(f"[{request_id}] Cleaned up temp file")
        
        return {"metadata": response}
    except Exception as e:
        print(f"[{request_id}] Error: {str(e)}")
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            print(f"[{request_id}] Cleaned up temp file after error")
        return HTTPException(status_code=400,detail=str(e))

@router.post("/generate-from-url")
async def generate_metadata(req: MetadataGenerateRequest,current_user: User = Depends(get_current_user)):
    request_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    print(f"\n[{request_id}] Starting URL request for: {req.image}")
    try:
        # Get a fresh generator instance
        metadata_generator = get_metadata_generator()
        print(f"[{request_id}] Created new MetadataGenerator instance")
        
        response = metadata_generator.generate(req.image)
        print(f"[{request_id}] Generated metadata successfully")
        
        return {"metadata": response}
    except Exception as e:
        print(f"[{request_id}] Error: {str(e)}")
        return HTTPException(status_code=400,detail=str(e))
