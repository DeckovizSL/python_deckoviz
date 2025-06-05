import json
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Any, Union
from sklearn.metrics.pairwise import cosine_similarity


class JSONEmbedder:
    """
    Convert JSON objects to vector embeddings using preprocessing and Sentence Transformers
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the JSON embedder
        
        Args:
            model_name: Sentence transformer model to use
                      Options: 'all-MiniLM-L6-v2', 'all-mpnet-base-v2', 'all-distilroberta-v1'
        """
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        print(f"Loaded model: {model_name}")
    
    def flatten_json(self, json_obj: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        Flatten nested JSON object using dot notation
        
        Args:
            json_obj: JSON object to flatten
            parent_key: Parent key for nested objects
            sep: Separator for nested keys
            
        Returns:
            Flattened dictionary
        """
        items = []
        
        for key, value in json_obj.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            
            if isinstance(value, dict):
                items.extend(self.flatten_json(value, new_key, sep=sep).items())
            elif isinstance(value, list):
                # Handle lists by converting to string or processing each item
                if value and isinstance(value[0], dict):
                    # List of objects - flatten each
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            items.extend(self.flatten_json(item, f"{new_key}[{i}]", sep=sep).items())
                        else:
                            items.append((f"{new_key}[{i}]", str(item)))
                else:
                    # Simple list - join as string
                    items.append((new_key, ', '.join(map(str, value))))
            else:
                items.append((new_key, str(value)))
        
        return dict(items)
    
    def json_to_text(self, json_obj: Dict[str, Any], strategy: str = 'key_value') -> str:
        """
        Convert JSON to text using different strategies
        
        Args:
            json_obj: JSON object to convert
            strategy: Conversion strategy
                     'key_value': "key: value, key2: value2"
                     'natural': "The user name is John and age is 30"
                     'flat': "user.name: John, user.age: 30"
                     'concat': "John 30 Engineer"
                     
        Returns:
            Text representation of JSON
        """
        if strategy == 'key_value':
            flattened = self.flatten_json(json_obj)
            return ', '.join([f"{k}: {v}" for k, v in flattened.items()])
        
        elif strategy == 'natural':
            # Convert to more natural language (basic implementation)
            flattened = self.flatten_json(json_obj)
            text_parts = []
            for key, value in flattened.items():
                # Simple natural language conversion
                clean_key = key.replace('_', ' ').replace('.', ' ')
                text_parts.append(f"the {clean_key} is {value}")
            return '. '.join(text_parts)
        
        elif strategy == 'flat':
            flattened = self.flatten_json(json_obj)
            return ', '.join([f"{k}: {v}" for k, v in flattened.items()])
        
        elif strategy == 'concat':
            # Just concatenate all values
            flattened = self.flatten_json(json_obj)
            return ' '.join([str(v) for v in flattened.values()])
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def embed_json(self, json_obj: Union[Dict, str], strategy: str = 'key_value') -> np.ndarray:
        """
        Convert single JSON object to embedding
        
        Args:
            json_obj: JSON object or JSON string
            strategy: Text conversion strategy
            
        Returns:
            Embedding vector as numpy array
        """
        # Parse JSON string if needed
        if isinstance(json_obj, str):
            json_obj = json.loads(json_obj)
        
        # Convert to text
        text = self.json_to_text(json_obj, strategy)
        
        # Generate embedding
        embedding = self.model.encode(text)
        
        return embedding
    
    def embed_json_batch(self, json_objects: List[Union[Dict, str]], strategy: str = 'key_value') -> np.ndarray:
        """
        Convert multiple JSON objects to embeddings in batch
        
        Args:
            json_objects: List of JSON objects or JSON strings
            strategy: Text conversion strategy
            
        Returns:
            Array of embeddings with shape (n_objects, embedding_dim)
        """
        # Convert all JSON objects to text
        texts = []
        for json_obj in json_objects:
            if isinstance(json_obj, str):
                json_obj = json.loads(json_obj)
            texts.append(self.json_to_text(json_obj, strategy))
        
        # Generate embeddings in batch (more efficient)
        embeddings = self.model.encode(texts)
        
        return embeddings
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score
        """
        return cosine_similarity([embedding1], [embedding2])[0][0]
    
    def find_similar(self, query_json: Union[Dict, str], 
                    json_database: List[Union[Dict, str]], 
                    top_k: int = 5, 
                    strategy: str = 'key_value') -> List[tuple]:
        """
        Find most similar JSON objects from a database
        
        Args:
            query_json: Query JSON object
            json_database: List of JSON objects to search
            top_k: Number of top results to return
            strategy: Text conversion strategy
            
        Returns:
            List of (index, similarity_score, json_object) tuples
        """
        # Get query embedding
        query_embedding = self.embed_json(query_json, strategy)
        
        # Get database embeddings
        db_embeddings = self.embed_json_batch(json_database, strategy)
        
        # Calculate similarities
        similarities = []
        for i, db_embedding in enumerate(db_embeddings):
            sim_score = self.similarity(query_embedding, db_embedding)
            similarities.append((i, sim_score, json_database[i]))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

 

if __name__ == "__main__":
    
    print("=== JSON Embedding Demo ===\n")
    
    # Test different strategies
    strategies = ['key_value', 'natural', 'flat', 'concat']
    
    for strategy in strategies:
        print(f"Strategy: {strategy}")
        text = embedder.json_to_text(sample_data[0], strategy)
        print(f"Text: {text[:100]}...")
        embedding = embedder.embed_json(sample_data[0], strategy)
        print(f"Embedding shape: {embedding.shape}")
        print(f"Embedding (first 5 dims): {embedding[:5]}")
    
    # Test batch embedding
    print("=== Batch Embedding ===")
    batch_embeddings = embedder.embed_json_batch(sample_data)
    print(f"Batch embeddings shape: {batch_embeddings.shape}")
    
    # Test similarity search
    print("\n=== Similarity Search ===")
    similar_items = embedder.find_similar(query, sample_data, top_k=3)
    
    print("Query:", embedder.json_to_text(query))
    print("\nMost similar items:")
    for idx, score, item in similar_items:
        print(f"Index: {idx}, Similarity: {score:.4f}")
        print(f"Item: {embedder.json_to_text(item)}")
