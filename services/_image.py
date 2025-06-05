 
from database.connection import Session
from typing import List,Any
from fastapi import HTTPException
from sqlalchemy import text
import json
from utils.db_helpers import rows_to_dict_list
from utils.json_helpers import json_dumps

class ImageService:
    def __init__(self):
        self.limit = 10
        self.offset = 0
    
    def get_images(self, limit: int = 10, offset: int = 0) -> List[Any]:
        with Session() as db:
            query = """
                SELECT id, file,external_url,metadata 
                FROM images 
                WHERE metadata IS NULL OR metadata = '{}'::jsonb LIMIT :limit OFFSET :offset;
            """
            images = db.execute(text(query), {"limit": limit, "offset": offset}).fetchall()
            return rows_to_dict_list(images)

    def get_last_index(self):
        with Session() as db:
            # Get the maximum embedding_id value or 0 if no embeddings exist
            query = "SELECT MAX(embedding_id) FROM images"
            max_id = db.execute(text(query)).scalar() or 0
            return max_id
    
    def get_images_with_metadata(self, limit: int = 10, offset: int = 0) -> List[Any]:
        with Session() as db:
            query = """
                SELECT id, file,external_url,metadata 
                FROM images 
                WHERE metadata IS NOT NULL LIMIT :limit OFFSET :offset;
            """
            images = db.execute(text(query), {"limit": limit, "offset": offset}).fetchall()
            return rows_to_dict_list(images)
    
    def update_metadata(self,id:str,metadata:dict):
        metadata_json = json_dumps(metadata)

        with Session() as db:
            result = db.execute(
                text("UPDATE images SET metadata = :metadata WHERE id = :id"),
                {"metadata": metadata_json, "id": id}
            )

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Image not found")

            db.commit()
            print(f"✅ Successfully updated metadata for image {id}")
            return {"detail": f"Metadata updated for image {id}"}
        
    def update_embedding(self,id:str,embedding_id:str):

        with Session() as db:
            result = db.execute(
                text("UPDATE images SET embedding_id = :embedding_id WHERE id = :id"),
                {"embedding_id": embedding_id, "id": id}
            )

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Image not found")

            db.commit()
            print(f"✅ Successfully updated embedding for image {id} to {embedding_id}")
            return {"detail": f"Embedding updated for image {id} to {embedding_id}"}
        
     