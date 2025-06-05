from pymilvus import MilvusClient
import google.generativeai as genai
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from pymilvus import model
from dotenv import load_dotenv
import os 

load_dotenv()


class DeckovizQueryEmbedding: 
    def __init__(self,model=None): 
        self.model_name = 'all-mpnet-base-v2' 
        self.model = SentenceTransformer(self.model_name)

    def create_embedding(self,desc): 
        return self.model.encode(desc) 


class MilvusDB: 
    def __init__(self,collection_name="dz_images",dim=768,top_k=6):
        self._uri = os.getenv("MILVUS_URI")
        if not self._uri: 
            raise RuntimeError("MILVUS_URI not found")
        self._token=os.getenv("MILVUS_TOKEN")
        if not self._token:
            raise RuntimeError("MILVUS_TOKEN not found") 
        self.dim=dim
        self.embedding = DeckovizQueryEmbedding()
        self.collection_name=collection_name
        self.top_k = top_k
        self.embedding_fn = model.DefaultEmbeddingFunction()
        self.client  = MilvusClient(uri=self._uri,token=self._token)
        if not self.client.has_collection(collection_name=self.collection_name):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    dimension=self.dim,
                )
            
    def embed_docs(self,docs):  
        return self.embedding_fn.encode_documents(docs)
        
    def upsert(self,data):
        res = self.client.insert(collection_name=self.collection_name,data=data)
        return res
    
    def query(self,query): 
        query_vector = self.embedding.create_embedding(query)
        return self.client.search(
            collection_name=self.collection_name, 
                anns_field="vector",
                data=[query_vector],
                limit=self.top_k,
        )


 

 
milvus_db = MilvusDB()