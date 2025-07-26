from fastapi import APIRouter, Depends
from deckoviz_ai.embeddings import JSONEmbedder
from fastapi.responses import JSONResponse
from typing import List 
from utils.token import get_current_user
from schemas.user import User 


router = APIRouter()


@router.post("/from-json")
async def generate_embedding(body: dict, model_name: str = 'all-MiniLM-L6-v2', current_user: User = Depends(get_current_user)):
    """
    Generate embedding from JSON data\n
    
    Args:
        body: JSON data to embed\n
        model_name: Sentence transformer model to use\n
        Supported Models: 'all-MiniLM-L6-v2', 'all-mpnet-base-v2', 'all-distilroberta-v1'
    """
    try:
        embedder = JSONEmbedder(model_name)
        embedding = embedder.embed_json(body)
        return JSONResponse(content=embedding.tolist(),status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)},status_code=500)

@router.post("/from-json-batch")
async def generate_embedding_batch(body: List[dict], model_name: str = 'all-MiniLM-L6-v2', current_user: User = Depends(get_current_user)):
    """
    Generate embeddings from a batch of JSON data\n
    
    Args:
        body: List of JSON data to embed\n
        model_name: Sentence transformer model to use\n
        Supported Models: 'all-MiniLM-L6-v2', 'all-mpnet-base-v2', 'all-distilroberta-v1'
    """ 
    try:
        embedder = JSONEmbedder(model_name)
        embeddings = embedder.embed_json_batch(body)
        return JSONResponse(content=embeddings.tolist(), status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

 