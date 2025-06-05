from pymilvus import connections, Collection
from dotenv import load_dotenv
import os 

load_dotenv()

class MilvusUserSimilarityPipeline:
    def __init__(self, collection_name="tenants", uri=None, token=None):
        """Initialize the Milvus similarity search pipeline using URI and token.
        
        Args:
            collection_name: Name of the Milvus collection
            uri: Milvus URI (defaults to environment variable)
            token: Milvus token (defaults to environment variable)
        """
        # Get URI and token from environment variables if not provided
        self.uri = uri or os.getenv("MILVUS_URI")
        self.token = token or os.getenv("MILVUS_TOKEN")
        
        if not self.uri or not self.token:
            raise ValueError("Milvus URI and token must be provided or set as environment variables")
        
        # Connect to Milvus server using URI and token
        connections.connect(
            alias="default",
            uri=self.uri,
            token=self.token
        )
        
        # Get the collection
        self.collection = Collection(collection_name)
        self.collection.load()
    
    def get_user_vector_by_id(self, user_id):
        """Retrieve a user's vector by their ID."""
        # Define output fields - we need the vector
        output_fields = ["vector"]
        
        # Search for the specific user ID
        expr = f"id == {user_id}" if isinstance(user_id, int) else f'id == "{user_id}"'
        results = self.collection.query(expr=expr, output_fields=output_fields)
        
        if not results:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Extract the vector from the results
        user_vector = results[0]["vector"]
        return user_vector
    
    def find_similar_users(self, query_vector, top_k=10, exclude_ids=None):
        """Find similar users based on vector similarity."""
        search_params = {
            "metric_type": "COSINE",  # or "IP" for inner product, "COSINE" for cosine similarity
            "params": {"nprobe": 10}
        }
        
        # Prepare search parameters
        results = self.collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=top_k,
            expr=None if not exclude_ids else f"id != {exclude_ids}",
            output_fields=["id", "*"]  # Return ID and all metadata fields
        )
        
        # Process and return results
        similar_users = []
        for hits in results:
            for hit in hits:
                similar_users.append({
                    "id": hit.id,
                    "score": hit.distance,
                    "metadata": hit.entity.get('metadata', {})
                })
        
        return similar_users
    
    def find_similar_users_by_id(self, user_id, top_k=10, include_self=False):
        """Pipeline to find similar users based on a user ID."""
        # Get the user's vector
        user_vector = self.get_user_vector_by_id(user_id)
        
        # Find similar users
        exclude_ids = None if include_self else user_id
        similar_users = self.find_similar_users(
            query_vector=user_vector,
            top_k=top_k,
            exclude_ids=exclude_ids
        )
        
        return similar_users
    
    def close(self):
        """Close the connection to Milvus."""
        connections.disconnect("default")

