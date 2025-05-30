import os
from typing import List, Any, Optional
from pydantic import Field
from dotenv import load_dotenv
from langchain_core.language_models.llms import LLM
from google.generativeai import GenerativeModel
from google import generativeai as genai
from langchain_core.callbacks.manager import CallbackManagerForLLMRun


load_dotenv()

class GeminiLLM(LLM):
    model_name: str = Field(default="gemini-2.0-flash")
    model: GenerativeModel = Field(default=None, exclude=True)

    @property
    def _llm_type(self) -> str:
        return "gemini_custom"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key: 
            raise RuntimeError("GOOGLE_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        response = self.model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else response.parts[0].text
