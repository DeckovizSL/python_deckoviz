from dotenv import load_dotenv
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableSequence
from ..llm import GeminiLLM

load_dotenv()

class DreamChatPrompt(BaseModel):
    prompt: str = Field(None, description='The final generated prompt for image creation.')

class DreamVisualizerChatPrompt:
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model_name: str = "gemini-2.5-flash"
               ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is required. Please set in environment variables.")
        
        self.llm = GeminiLLM(model_name=model_name)  
        self.output_parser = PydanticOutputParser(pydantic_object=DreamChatPrompt)
        
        # Define the prompt directly in the code
        self.prompt_template = self._get_prompt_template()
        
        self.chain = RunnableSequence(self.prompt_template, self.llm, self.output_parser)
 
    def _get_prompt_template(self) -> PromptTemplate:
        # Prompt is defined here instead of being loaded from LangSmith
        prompt = """
You are a prompt engineer for a dream visualization AI. Your task is to convert a user's dream description from a chat into a simple, high-definition, and to-the-point prompt for the Runware image generation model.

Carefully review the entire chat history and identify all key visual elements, characters, actions, and the overall environment mentioned by the user. Synthesize these elements into a single, cohesive scene.

The prompt should be a single, concise string focusing on key visual elements, style, and atmosphere. Omit conversational filler. Be direct and descriptive.

Here are some guidelines for a Runware-compatible prompt:
- Focus on nouns, adjectives, and strong verbs.
- Use keywords to define the art style (e.g., "digital painting," "surrealist," "photorealistic," "fantasy art").
- Specify lighting and mood (e.g., "dramatic lighting," "ethereal glow," "ominous atmosphere").
- Include composition details (e.g., "wide angle shot," "close-up portrait").
- End with quality tags like "masterpiece, 8k, high detail, sharp focus".

Chat History:
{chat_history}

Based on the chat history, create a single, optimized prompt string that includes all the important details from the user's descriptions.

{format_instructions}
"""
        return PromptTemplate.from_template(prompt)
    
    def generate_prompt(self, chat_history: List[dict]) -> DreamChatPrompt:
        """Generate a single art prompt from the chat history.""" 
        response = self.chain.invoke({
            'chat_history': chat_history, 
            'format_instructions': self.output_parser.get_format_instructions()
        })
        return response 