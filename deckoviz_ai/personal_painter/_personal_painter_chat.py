from dotenv import load_dotenv
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableSequence
from langsmith import Client
from ..llm import GeminiLLM
import uuid
from ._db import PersonalPainterDatabase


load_dotenv()


class Question(BaseModel):
    content: str = Field(default='Next question for the user', description='The content of the question.')
    role: str = Field(default='ai', description='The role of the entity asking the question (e.g., "ai", "user").')

    
class PersonalPainterConversation:
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model_name: str = "gemini-2.0-flash",
                 langsmith_api_key: Optional[str] = None,
                 prompt_repo: str = "dharmendra622/dz_personal_painter"
               ):
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
        self.output_parser = PydanticOutputParser(pydantic_object=Question)
        
        # Create fallback prompt template
        self.prompt_template = self._load_prompt_from_langsmith(prompt_repo)
        
        # Create the chain
        self.chain = RunnableSequence(self.prompt_template, self.llm, self.output_parser)
        
        self.database = PersonalPainterDatabase()
 
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
    

    def next_chat(self, chat_history: List=[]) -> Question:
        """Generate a single question card based on user profile""" 
        response = self.chain.invoke({
            'chat_history': chat_history, 
            'format_instructions': self.output_parser.get_format_instructions()
        })
        return response



 