style_transfer_prompt:str='dz-style-transfer'
image_analysis_prompt:str='image-analysis-prompt'
style_refinement_prompt:str='style_refinement_prompt'
multi_style_fusion_prompt:str='multi_style_fusion_prompt'



"""
AI Image Style Transfer Implementation using LangChain and LangGraph
Supports both preset styles and custom text descriptions
"""

import os
import base64
from typing import List, Dict, Any, Optional, TypedDict
from enum import Enum
import asyncio
from datetime import datetime
from langsmith import Client
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableSequence
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from langchain_core.language_models.llms import LLM
from google.generativeai import GenerativeModel
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
import os 

load_dotenv()


class GeminiLLM(LLM):
    model_name: str = Field(default="gemini-1.5-flash-latest") # USE A VALID MODEL NAME (e.g., "gemini-1.5-flash-latest", "gemini-1.0-pro")
    model: GenerativeModel = Field(default=None, exclude=True)

    @property
    def _llm_type(self) -> str:
        return "gemini_custom"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from google import generativeai as genai
        api_key=os.getenv("GOOGLE_API_KEY")
        if not api_key: 
            raise RuntimeError("GOOGLE_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name) # Make sure self.model_name is valid

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,  # <-- Add this
        **kwargs: Any,                                          # <-- And this
    ) -> str:
        # The run_manager and kwargs are now accepted but not explicitly used in this simple _call.
        # This makes the signature compatible with what LangChain expects.
        response = self.model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else response.parts[0].text
    
class StyleCategory(str, Enum):
    """Predefined style categories"""
    VAN_GOGH = "van_gogh"
    PICASSO = "picasso"
    MONET = "monet"
    IMPRESSIONISM = "impressionism"
    ABSTRACT = "abstract"
    REALISTIC = "realistic"
    WATERCOLOR = "watercolor"
    OIL_PAINTING = "oil_painting"
    SKETCH = "sketch"
    ANIME = "anime"
    POP_ART = "pop_art"
    SURREALISM = "surrealism"
    NONE = "none"

class StyleTransferRequest(BaseModel):
    """Input model for style transfer requests"""
    image_base64: Optional[str] = Field(None, description="Base64 encoded image")
    preset_style: Optional[StyleCategory] = Field(None, description="Predefined style category")
    custom_style_description: Optional[str] = Field(None, description="Custom style description")
    height: int = Field(512, description="Height of the generated image")
    width: int = Field(512, description="Width of the generated image")
    intensity: float = Field(0.7, description="Style transfer intensity (0.1-1.0)")
    preserve_content: bool = Field(True, description="Whether to preserve original content structure")

class StyleAnalysis(BaseModel):
    """Analysis of the input image and style requirements"""
    image_description: str = Field(..., description="Description of the input image")
    recommended_techniques: List[str] = Field(..., description="Recommended artistic techniques")
    color_palette: List[str] = Field(..., description="Suggested color palette")
    composition_notes: str = Field(..., description="Notes about composition")

class StyleTransferResult(BaseModel):
    """Result of style transfer operation"""
    success: bool = Field(..., description="Whether the operation was successful")
    styled_image_prompt: str = Field(..., description="Generated prompt for image creation")
    style_description: str = Field(..., description="Description of applied style")
    processing_notes: str = Field(..., description="Notes about the processing")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    generated_image: Optional[str] = Field(None, description="Generated image in base64 format")
    
class GraphState(TypedDict):
    """State management for the LangGraph workflow"""
    request: StyleTransferRequest
    image_analysis: Optional[StyleAnalysis]
    style_prompt: Optional[str]
    result: Optional[StyleTransferResult]
    error: Optional[str]

class ImageStyleTransferAgent:
    """Main agent for handling image style transfer operations"""
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        langsmith_key = os.getenv("LANGSMITH_API_KEY")
        if not langsmith_key:
            raise RuntimeError("LANGSMITH_API_KEY not found in environment variables.")
        
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise RuntimeError("GOOGLE_API_KEY not found in environment variables for ChatGoogleGenerativeAI.")

        # Initialize LangChain components
        self.llm =  GeminiLLM(model_name=model_name)   
        self.langsmith_client = Client(api_key=langsmith_key)
        self.image_analyzer = self._create_image_analyzer()
        self.style_generator = self._create_style_generator()
        self.workflow = self._create_workflow()
        
    def _create_image_analyzer(self):
        """Create the image analysis chain for style transfer."""
    
        # Initialize the parser for the expected output format
        _parser = PydanticOutputParser(pydantic_object=StyleAnalysis)
    
        # Pull the prompt template from LangSmith
        analysis_prompt_template = self.langsmith_client.pull_prompt(image_analysis_prompt)
        
        # Build the final prompt chain (Prompt -> LLM -> Parser)
        _chain =  RunnableSequence(analysis_prompt_template,self.llm,_parser)
        return _chain
    
    def _create_style_generator(self):
        """Create the style generation chain."""
    
        _parser = PydanticOutputParser(pydantic_object=StyleTransferResult)
    
        # Pull the style transfer prompt template from LangSmith
        style_prompt_template = self.langsmith_client.pull_prompt(style_transfer_prompt)   
        _chain = RunnableSequence(style_prompt_template,self.llm,_parser)
        return _chain
    
    def _create_workflow(self):
        """Create the LangGraph workflow"""
        workflow = StateGraph(GraphState)
        
        # Define nodes
        workflow.add_node("analyze_image", self.analyze_image_node)
        workflow.add_node("generate_style", self.generate_style_node)
        workflow.add_node("finalize_result", self.finalize_result_node)
        
        # Define edges
        workflow.add_edge(START, "analyze_image")
        workflow.add_edge("analyze_image", "generate_style")
        workflow.add_edge("generate_style", "finalize_result")
        workflow.add_edge("finalize_result", END)
        
        # Compile with memory
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    async def analyze_image_node(self, state: GraphState) -> GraphState:
        """Node for analyzing the input image"""
        try:
            request = state["request"]
            parser = PydanticOutputParser(pydantic_object=StyleAnalysis) # Defined locally
    
            # Define what 'additional_context_value' should be.
            # It could be a fixed string, derived from the request, or an empty string if allowed.
            additional_context_value = "Default context" # Or derive dynamically
    
            analysis = await self.image_analyzer.ainvoke({
                "image_base64": request.image_base64,
                "format_instructions": parser.get_format_instructions(),
                "additional_context": additional_context_value # Add the missing variable
            })
    
            state["image_analysis"] = analysis
            return state
        except Exception as e:
            state["error"] = f"Image analysis failed: {str(e)}"
            return state
    
    async def generate_style_node(self, state: GraphState) -> GraphState:
        """Node for generating style transfer instructions"""
        try:
            if state.get("error"):
                return state
                
            request = state["request"]
            analysis = state["image_analysis"]
            
            # Generate style transfer result
            result = await self.style_generator.ainvoke({
                "image_analysis": analysis.model_dump() if analysis else {},
                "preset_style": request.preset_style.value if request.preset_style else "none",
                "custom_style_description": request.custom_style_description or "none",
                "intensity": request.intensity,
                "preserve_content": request.preserve_content,
                "format_instructions": PydanticOutputParser(pydantic_object=StyleTransferResult).get_format_instructions()
            })
            
            state["result"] = result
            return state
            
        except Exception as e:
            state["error"] = f"Style generation failed: {str(e)}"
            return state
    
    async def finalize_result_node(self, state: GraphState) -> GraphState:
        """Node for finalizing the result"""
        if state.get("error"):
            state["result"] = StyleTransferResult(
                success=False,
                styled_image_prompt="",
                style_description="",
                processing_notes="",
                error_message=state["error"]
            )
        
        return state
    
    async def process_style_transfer(self, request: StyleTransferRequest) -> StyleTransferResult:
        """Main method to process style transfer requests"""
        initial_state = GraphState(
            request=request,
            image_analysis=None,
            style_prompt=None,
            result=None,
            error=None
        )
        
        # Generate a unique thread ID for this request
        thread_id = f"style_transfer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        config = {"configurable": {"thread_id": thread_id}}
        
        # Run the workflow
        final_state = await self.workflow.ainvoke(initial_state, config=config)
        
        return final_state["result"]

# Utility functions for integration

def encode_image_to_base64(image_path: str) -> str:
    """Encode image file to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_style_presets() -> Dict[str, str]:
    """Get available style presets with descriptions"""
    return {
        "van_gogh": "Van Gogh style with bold brushstrokes and swirling patterns",
        "picasso": "Picasso's cubist style with geometric shapes",
        "monet": "Monet's impressionist style with soft light effects",
        "impressionism": "Classic impressionist style emphasizing light",
        "abstract": "Abstract art focusing on color and form",
        "realistic": "Photorealistic style with fine details",
        "watercolor": "Watercolor painting with soft, flowing colors",
        "oil_painting": "Traditional oil painting with rich textures",
        "sketch": "Pencil sketch or charcoal drawing style",
        "anime": "Japanese anime/manga illustration style",
        "pop_art": "Pop art style with bold colors and patterns",
        "surrealism": "Surrealist style with dreamlike elements"
    }

# Example usage and testing
async def main():
    """Example usage of the style transfer system"""
    print("Initializing agent...")
    try:
        agent = ImageStyleTransferAgent()
        print("Agent initialized successfully.")
    except Exception as e:
        print(f"🚨 Error during ImageStyleTransferAgent initialization: {e}")
        print("   Please ensure 'image_analysis_prompt' and 'style_transfer_prompt' global variables are set to your actual prompt names from LangSmith.")
        print("   Also, check your LANGSMITH_API_KEY and Google API key setup.")
        return

    # Example 1: Using preset style
    print("\nProcessing Preset Style Request...")
    request1 = StyleTransferRequest(
        image_base64=pure_base64_image,  # ✅ Use the defined variable
        preset_style=StyleCategory.VAN_GOGH,
        intensity=0.8,
        preserve_content=True
    )
    
    try:
        result1 = await agent.process_style_transfer(request1)
        print("\n--- Preset Style Debug Output ---")
        print(f"Success: {result1.success}")
        print(f"Styled Image Prompt: '{result1.styled_image_prompt}'")
        print(f"Style Description: '{result1.style_description}'")
        print(f"Processing Notes: '{result1.processing_notes}'")
        print(f"Error Message: {result1.error_message if result1.error_message else 'No error message.'}")
        print("--- End Preset Style Debug Output ---\n")
    except Exception as e:
        print(f"🚨 Error during preset style processing call: {e}")

    # Example 2: Using custom style description
    print("Processing Custom Style Request...")
    request2 = StyleTransferRequest(
        image_base64=pure_base64_image,  # ✅ Use the defined variable
        custom_style_description="Transform into a cyberpunk neon art style with glowing edges and dark urban atmosphere",
        intensity=0.7,
        preserve_content=True
    )
    try:
        result2 = await agent.process_style_transfer(request2)
        print("\n--- Custom Style Debug Output ---")
        print(f"Success: {result2.success}")
        print(f"Styled Image Prompt: '{result2.styled_image_prompt}'")
        print(f"Style Description: '{result2.style_description}'")
        print(f"Processing Notes: '{result2.processing_notes}'")
        print(request2.image)
        print(f"Error Message: {result2.error_message if result2.error_message else 'No error message.'}")
        print("--- End Custom Style Debug Output ---\n")
    except Exception as e:
        print(f"🚨 Error during custom style processing call: {e}")

        
# For Jupyter notebooks or environments with existing event loops
def run_example():
    """Run example in environments with existing event loops"""
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())

# Alternative: Direct awaitable function for Jupyter
async def run_example_async():
    """Direct async function for Jupyter notebooks"""
    await main()
    
if __name__ == "__main__":
    # Ensure placeholder variables are globally accessible here if main() relies on them being global.
    # It's better if main() gets them as arguments or if they are defined at the script's global scope as shown in step 1.

    try:
        # This will work in regular Python scripts without a pre-existing event loop
        asyncio.run(main())
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            print("Detected existing event loop.")
            print("Since `nest_asyncio` is installed, attempting to run with it via `run_example()`.")
            try:
                run_example() # This function applies nest_asyncio and runs main()
                print("Successfully ran with nest_asyncio.")
            except Exception as e_nested:
                print(f"Error even after attempting with nest_asyncio: {e_nested}")
        else:
            # Re-raise other RuntimeErrors
            raise
    except NameError as ne:
        print(f"A NameError occurred: {ne}. This might be due to undefined prompt names ")
    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")