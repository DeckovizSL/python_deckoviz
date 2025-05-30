"""
Multi-Agent Image Style Transfer System
Combines style analysis with image generation using LangChain, LangGraph, and LangSmith
"""
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from ._schemas import MultiAgentState,FinalResult
from .agents._style_transfer import StyleTransferAgent
from .agents._image_generator import ImageGenerationAgent
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser
from ._schemas import StyleAnalysis, StyleTransferResult
from dotenv import load_dotenv

load_dotenv()

# Main Multi-Agent Orchestrator
class ImageStyleTransferSystem:
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.style_agent = StyleTransferAgent(model_name)
        self.image_agent = ImageGenerationAgent()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self):
        """Create the multi-agent LangGraph workflow"""
        workflow = StateGraph(MultiAgentState)
        
        # Add nodes for each step
        workflow.add_node("analyze_image", self.analyze_image_node)
        workflow.add_node("generate_style", self.generate_style_node)
        workflow.add_node("generate_image", self.generate_image_node)
        workflow.add_node("finalize_result", self.finalize_result_node)
        
        # Define the workflow edges
        workflow.add_edge(START, "analyze_image")
        workflow.add_edge("analyze_image", "generate_style")
        workflow.add_edge("generate_style", "generate_image")
        workflow.add_edge("generate_image", "finalize_result")
        workflow.add_edge("finalize_result", END)
        
        # Compile with memory
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    async def analyze_image_node(self, state: MultiAgentState) -> MultiAgentState:
        """Node 1: Analyze the input image"""
        print("🔍 Step 1: Analyzing image...")
        state["current_step"] = "analyzing_image"
        
        try:
            request = state["request"]
            parser = PydanticOutputParser(pydantic_object=StyleAnalysis)
            
            analysis = await self.style_agent.image_analyzer.ainvoke({
                "image_base64": request.image_base64,
                "format_instructions": parser.get_format_instructions(),
                "additional_context": "Detailed image analysis for style transfer"
            })
            
            state["image_analysis"] = analysis
            print(f"✅ Image analysis complete: {analysis.image_description[:100]}...")
            
        except Exception as e:
            error_msg = f"Image analysis failed: {str(e)}"
            state["error"] = error_msg
            print(f"❌ {error_msg}")
        
        return state
    
    async def generate_style_node(self, state: MultiAgentState) -> MultiAgentState:
        """Node 2: Generate style transfer instructions"""
        print("🎨 Step 2: Generating style transfer...")
        state["current_step"] = "generating_style"
        
        if state.get("error"):
            return state
        
        try:
            request = state["request"]
            analysis = state["image_analysis"]
            
            result = await self.style_agent.style_generator.ainvoke({
                "image_analysis": analysis.model_dump() if analysis else {},
                "preset_style": request.preset_style.value if request.preset_style else "none",
                "custom_style_description": request.custom_style_description or "none",
                "intensity": request.intensity,
                "preserve_content": request.preserve_content,
                "format_instructions": PydanticOutputParser(pydantic_object=StyleTransferResult).get_format_instructions()
            })
            
            state["style_result"] = result
            print(f"✅ Style transfer complete: {result.style_description[:100]}...")
            
        except Exception as e:
            error_msg = f"Style generation failed: {str(e)}"
            state["error"] = error_msg
            print(f"❌ {error_msg}")
        
        return state
    
    async def generate_image_node(self, state: MultiAgentState) -> MultiAgentState:
        """Node 3: Generate the final styled image"""
        print("🖼️ Step 3: Generating styled image...")
        state["current_step"] = "generating_image"
        
        if state.get("error"):
            return state
        
        try:
            style_result = state["style_result"]
            image_result = await self.image_agent.generate_image(style_result)
            state["image_generation_result"] = image_result
            
            if image_result.success:
                print("✅ Image generation complete!")
            else:
                print(f"❌ Image generation failed: {image_result.error_message}")
            
        except Exception as e:
            error_msg = f"Image generation failed: {str(e)}"
            state["error"] = error_msg
            print(f"❌ {error_msg}")
        
        return state
    
    async def finalize_result_node(self, state: MultiAgentState) -> MultiAgentState:
        """Node 4: Finalize and package the complete result"""
        print("📦 Step 4: Finalizing results...")
        state["current_step"] = "finalizing"
        
        processing_time = datetime.now().timestamp() - state["processing_start_time"]
        
        if state.get("error"):
            final_result = FinalResult(
                success=False,
                processing_time=processing_time,
                error_message=state["error"]
            )
        else:
            final_result = FinalResult(
                success=True,
                original_image_analysis=state.get("image_analysis"),
                style_transfer_result=state.get("style_result"),
                generated_image_result=state.get("image_generation_result"),
                processing_time=processing_time
            )
        
        state["final_result"] = final_result
        print(f"✅ Processing complete in {processing_time:.2f} seconds!")
        
        return state
    
    async def process_request(self, request: StyleTransferRequest) -> FinalResult:
        """Main method to process the complete multi-agent workflow"""
        print("🚀 Starting multi-agent image style transfer...")
        
        initial_state = MultiAgentState(
            request=request,
            image_analysis=None,
            style_result=None,
            image_generation_result=None,
            final_result=None,
            error=None,
            current_step="initializing",
            processing_start_time=datetime.now().timestamp()
        )
        
        # Generate unique thread ID
        thread_id = f"multi_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        config = {"configurable": {"thread_id": thread_id}}
        
        # Run the complete workflow
        final_state = await self.workflow.ainvoke(initial_state, config=config)
        
        return final_state["final_result"]