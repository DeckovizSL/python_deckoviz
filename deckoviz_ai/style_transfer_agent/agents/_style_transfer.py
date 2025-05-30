from ...llm._llm import GeminiLLM
from langchain_core.runnables import RunnableSequence
from langchain_core.output_parsers import PydanticOutputParser
from langsmith import Client
from .._schemas import StyleAnalysis, StyleTransferResult
from ._prompt import style_transfer_prompt, image_analysis_prompt
import os 

class StyleTransferAgent:
    def __init__(self, model_name: str = "gemini-2.0-flash"): 
        self.llm = GeminiLLM(model_name=model_name)
        
        # Initialize LangSmith client if available
        langsmith_key = os.getenv("LANGSMITH_API_KEY")
        if langsmith_key:
            self.langsmith_client = Client(api_key=langsmith_key)
        else:
            self.langsmith_client = None
            print("⚠️ LangSmith not configured, using fallback prompts")
        
        self.image_analyzer = self._create_image_analyzer()
        self.style_generator = self._create_style_generator()
        
    def _create_image_analyzer(self)->RunnableSequence:
        """Create image analysis chain with fallback prompt"""
        parser = PydanticOutputParser(pydantic_object=StyleAnalysis)
        
        if self.langsmith_client:
            try:
                analysis_prompt = self.langsmith_client.pull_prompt(image_analysis_prompt)
            except:
                print("⚠️ Could not pull LangSmith prompt, using fallback")
        return RunnableSequence(analysis_prompt, self.llm, parser)
    
    def _create_style_generator(self)->RunnableSequence:
        """Create style generation chain with fallback prompt"""
        parser = PydanticOutputParser(pydantic_object=StyleTransferResult)
        
        if self.langsmith_client:
            try:
                style_prompt = self.langsmith_client.pull_prompt(style_transfer_prompt)
            except:
                print("⚠️ Could not pull LangSmith prompt, using fallback")
        return RunnableSequence(style_prompt, self.llm, parser)

