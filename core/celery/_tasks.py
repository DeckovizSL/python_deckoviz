 
from ._celery import celery_app
from datetime import datetime,timezone 
import traceback 
from core.logger import logger
from services import ImageService
from utils.settings import get_settings
from deckoviz_ai.metadata_generator import MetadataGenerator
from deckoviz_ai.embeddings import JSONEmbedder
from deckoviz_ai.milvus_db import milvus_db
settings = get_settings()

image_service = ImageService()
generator = MetadataGenerator()
embedder = JSONEmbedder()
 
@celery_app.task(name="core.celery._tasks.create_metadata", bind=True)
def create_metadata(self):
    try:   
        images = image_service.get_images()

        if not images: 
            logger.info("No images found")
            return 
        for image in images:
            url = f"{settings.aws_base_url}/{image['file']}"
            metadata = generator.generate(url) 
            metadata = metadata.model_dump()
            image_service.update_metadata(image['id'], metadata)
            continue
        logger.info(f"Found {len(images)} images") 
        
        logger.info(f"✅ Task completed at {datetime.now(timezone.utc).isoformat()}")
        
    except Exception as e:
        error_msg = f"Task failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise  RuntimeError(error_msg)

@celery_app.task(name="core.celery._tasks.create_embedding", bind=True)
def create_embedding(self):
    try:   
        images = image_service.get_images_with_metadata()

        if not images: 
            logger.info("No images found")
            return 
        for image in images: 
            img_metadata = image['metadata']
            embedding = embedder.embed_json(img_metadata) 
            last_index = image_service.get_last_index()
            metadata = {
                "created_at": datetime.now(timezone.utc).isoformat(),  
                "source": "image_metadata", 
                "id": last_index + 1, 
                "vector": embedding.tolist(),
                "metadata": img_metadata
            }
            milvus_db.upsert(data=[metadata])
            image_service.update_embedding(image['id'], last_index + 1)
            continue
        logger.info(f"Found {len(images)} images") 
        
        logger.info(f"✅ Task completed at {datetime.now(timezone.utc).isoformat()}")
        
    except Exception as e:
        error_msg = f"Task failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise  RuntimeError(error_msg)