from dotenv import load_dotenv
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableSequence
from ..llm import GeminiLLM

load_dotenv()

class Question(BaseModel):
    content: str = Field(default='Next question for the user', description='The content of the question.')
    role: str = Field(default='ai', description='The role of the entity asking the question (e.g., "ai", "user").')

class DreamVisualizerChatConversation:
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model_name: str = "gemini-2.5-flash"
               ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is required. Please set in environment variables.")
        
        self.llm = GeminiLLM(model_name=model_name)  
        self.output_parser = PydanticOutputParser(pydantic_object=Question)
        
        # Define the prompt directly in the code
        self.prompt_template = self._get_prompt_template()
        
        self.chain = RunnableSequence(self.prompt_template, self.llm, self.output_parser)
 
    def _get_prompt_template(self) -> PromptTemplate:
        # Prompt is defined here instead of being loaded from LangSmith
        prompt = """
You are a dream guide, helping a user explore their dream.
Ask one question at a time to gather more details about their dream.
Keep your questions open-ended and encouraging.
The goal is to collect enough information to visualize the dream later.

Here is the chat history so far:
{chat_history}

Your next question should naturally follow the conversation.

{format_instructions}
"""
        return PromptTemplate.from_template(prompt)

    def next_chat(self, chat_history: List=[]) -> Question:
        """Generate the next question for the user based on the chat history.""" 
        response = self.chain.invoke({
            'chat_history': chat_history, 
            'format_instructions': self.output_parser.get_format_instructions()
        })
        return response 