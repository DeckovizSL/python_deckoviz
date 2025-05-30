from .._tools import generate_image_with_gemini_tool
from .._schemas import ImageGenerationResult, StyleTransferResult
from langgraph.prebuilt import ToolNode

# Image Generation Agent
class ImageGenerationAgent:
    def __init__(self):
        self.tools = [generate_image_with_gemini_tool]
        self.tool_node = ToolNode(self.tools)
    
    async def generate_image(self, style_result: StyleTransferResult) -> ImageGenerationResult:
        """Generate image based on style transfer result"""
        try:
            # Call the image generation tool
            tool_result = await generate_image_with_gemini_tool.ainvoke({
                "styled_image_prompt": style_result.styled_image_prompt,
                "imagebase64":style_result.generated_image_result.image_data_base64,
                "style_description": style_result.style_description
            })
            
            if tool_result["status"] == "success":
                return ImageGenerationResult(
                    success=True,
                    image_data_base64=tool_result["image_data_base64"],
                    generation_prompt=tool_result.get("generation_prompt", style_result.styled_image_prompt)
                )
            else:
                return ImageGenerationResult(
                    success=False,
                    generation_prompt=style_result.styled_image_prompt,
                    error_message=tool_result.get("error", "Unknown error in image generation")
                )
                
        except Exception as e:
            return ImageGenerationResult(
                success=False,
                generation_prompt=style_result.styled_image_prompt,
                error_message=f"Image generation failed: {str(e)}"
            )
