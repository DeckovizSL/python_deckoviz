from dotenv import load_dotenv
import os
from typing import Dict, List, Optional,Any
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableSequence
from langsmith import Client
from datetime import datetime
from PIL import Image
import io
import base64
import boto3
import re
from ..llm import GeminiLLM

load_dotenv()


class Descriptions(BaseModel):
    literal: str = Field(..., description="A literal description of the image.")
    emotive: str = Field(..., description="An emotive interpretation of the image.")


class Sentiment(BaseModel):
    overall_mood: str = Field(..., description="The general mood conveyed by the image.")
    emotions_detected: List[str] = Field(..., description="List of specific emotions detected in the image.")
    confidence_score: float = Field(..., description="Confidence score for sentiment analysis.")


class TechnicalDetails(BaseModel):
    objects_detected: List[str] = Field(..., description="Objects identified within the image.")
    scene_composition: str = Field(..., description="Description of the scene's composition.")
    artistic_style: str = Field(..., description="Artistic style of the image.")


class ImageMetadata(BaseModel):
    title: str = Field(..., description="Title of the image.")
    upload_date: datetime = Field(..., description="Date and time when the image was uploaded.")
    descriptions: Descriptions = Field(..., description="Descriptions of the image in literal and emotive terms.")
    labels: List[str] = Field(..., description="Tags or labels associated with the image.")
    sentiment: Sentiment = Field(..., description="Sentiment and emotion analysis of the image.")
    technical_details: TechnicalDetails = Field(..., description="Technical and artistic information of the image.")


class MetadataGenerator:

    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model_name: str = "gemini-2.0-flash",
                 langsmith_api_key: Optional[str] = None,
                 prompt_repo: str = "dharmendra622/dz_metadata_generator"):
        """
        Initialize the search mode system with LangChain and structured output
        
        Args:
            api_key: Google API key (optional, will use env var if not provided)
            model_name: Gemini model name to use
            langsmith_api_key: LangSmith API key (optional, will use env var if not provided)
            prompt_repo: LangSmith prompt repository name
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is required. Please set in environment variables.")
        
        # Store prompt_repo as instance variable
        self.prompt_repo = prompt_repo
        
        # Initialize LangSmith client
        self.langsmith_api_key = langsmith_api_key or os.getenv("LANGSMITH_API_KEY")
        if self.langsmith_api_key:
            os.environ["LANGSMITH_API_KEY"] = self.langsmith_api_key
            self.langsmith_client = Client(api_key=self.langsmith_api_key)
        else:
            print("Warning: LANGSMITH_API_KEY not found. Will use fallback prompt.")
            self.langsmith_client = None
            
        # Initialize LangChain components - Fixed the class name
        self.llm = GeminiLLM(model_name=model_name)  
        
        # Set up Pydantic output parser
        self.output_parser = PydanticOutputParser(pydantic_object=ImageMetadata)
        
        # Create fallback prompt template
        self.prompt_template = self._load_prompt_from_langsmith(prompt_repo)
        
        # Create the chain
        self.chain = RunnableSequence(self.prompt_template, self.llm, self.output_parser)
    

    def _load_prompt_from_langsmith(self, prompt_repo: str) -> PromptTemplate:
        """
        Load prompt from LangSmith hub or use fallback
        
        Args:
            prompt_repo: LangSmith prompt repository name
            
        Returns:
            PromptTemplate: Loaded or fallback prompt template
        """
        try:
            if self.langsmith_client:
                # Try to pull from LangSmith hub 
                prompt_template = self.langsmith_client.pull_prompt(prompt_repo)
                print(f"Successfully loaded prompt from LangSmith: {prompt_repo}")
                return prompt_template
            else:
                raise Exception("LangSmith client not initialized")
                
        except Exception as e:
            raise RuntimeError(f"Failed to load prompt from LangSmith ({e}). Using fallback prompt.")
            
    def _prepare_image_for_gemini(self, image_path: str) -> Dict[str, Any]:
        """
        Prepare image data for Gemini API
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict: Formatted image data for Gemini
        """
        if not image_path:
            raise ValueError("Image path is required")
        if image_path.startswith('https://'):
            match = re.match(r'https://([^.]+)\.s3\.([^/]+)\.amazonaws\.com/(.+)', image_path)
            if not match:
                raise ValueError(f"Invalid S3 URL format: {image_path}")
            # Extract bucket and key from s3 URL
            bucket, region, key = match.groups()
            s3_client = boto3.client('s3', region_name=region)
            response = s3_client.get_object(Bucket=bucket, Key=key)
            image_data = response['Body'].read()
        else:
            # Read image as binary
            with open(image_path, "rb") as image_file: 
                image_data = image_file.read()
        
        # Get image format
        image = Image.open(io.BytesIO(image_data))
        image_format = image.format.lower() 
        # Convert image to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Return the image in the format expected by Gemini
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/{image_format};base64,{image_base64}"
            }
        }
    
    def generate(self, image_path:str) -> ImageMetadata:
        """Generate metadata based on image""" 
        try:
            if not image_path: 
                raise RuntimeError("Image path is empty.Pass {image_path} is required to analyse it.")
            response = self.chain.invoke({
                'image': self._prepare_image_for_gemini(image_path), 
                'format_instructions': self.output_parser.get_format_instructions()
            })
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to generate metadata: {e}")


 