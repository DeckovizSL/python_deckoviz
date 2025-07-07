from ..llm import GeminiLLM
from ._prompt import VISUAL_JOURNAL_SYSTEM_PROMPT
from schemas.visual_journal import UserInput, VisualJournalEntry, VisualFrame
import json
import os
from datetime import datetime
from runware import Runware, IImageInference
from typing import List, Dict, Any

class VisualJournalService:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.llm = GeminiLLM(model_name=model_name)

    async def generate_visual_journal(self, user_input: UserInput) -> VisualJournalEntry:
        """Generate a complete visual journal entry with images"""
        # Step 1: Analyze the user's input and generate image prompts
        analysis = await self._analyze_user_input(user_input.text)
        
        # Step 2: Generate images using Runware API with custom dimensions
        frames = await self._generate_visual_frames(analysis, user_input.width, user_input.height)
        
        # Step 3: Create the final journal entry
        journal_entry = VisualJournalEntry(
            title=analysis.get("title", f"Visual Journal — {datetime.now().strftime('%Y-%m-%d')}"),
            frames=frames,
            overall_mood=analysis.get("overall_mood", "reflective"),
            date=datetime.now().strftime('%Y-%m-%d'),
            saved_to="My Visual Journal"
        )
        
        return journal_entry

    async def _analyze_user_input(self, text: str) -> Dict[str, Any]:
        """Analyze user input and extract key elements for visualization"""
        prompt = self._create_analysis_prompt(text)
        
        print(f"DEBUG: Analyzing user input: {text}")
        print(f"DEBUG: Generated prompt length: {len(prompt)}")
        
        try:
            response = self.llm._call(prompt)
            print(f"DEBUG: LLM raw response: {response}")
            
            # Try to parse the JSON response
            parsed_response = json.loads(response)
            print(f"DEBUG: Successfully parsed JSON response")
            return parsed_response
            
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON parsing failed: {e}")
            print(f"DEBUG: Raw response that failed: {response}")
            # Create a dynamic fallback based on the actual user input
            return self._create_dynamic_fallback(text)
        except Exception as e:
            print(f"DEBUG: Other error occurred: {e}")
            return self._create_dynamic_fallback(text)

    def _create_dynamic_fallback(self, text: str) -> Dict[str, Any]:
        """Create a dynamic fallback based on the actual user input"""
        print(f"DEBUG: Creating dynamic fallback for: {text}")
        
        # Analyze the text for key elements
        text_lower = text.lower()
        
        # Determine mood based on keywords
        if any(word in text_lower for word in ['amazing', 'good', 'great', 'happy', 'wonderful', 'fantastic']):
            mood = 'joyful'
            title_theme = 'Celebration'
        elif any(word in text_lower for word in ['office', 'work', 'appraisal', 'promotion', 'success']):
            mood = 'accomplished'
            title_theme = 'Professional Success'
        elif any(word in text_lower for word in ['driving', 'car', 'road', 'journey']):
            mood = 'adventurous'
            title_theme = 'Journey Ahead'
        elif any(word in text_lower for word in ['heavy', 'anxious', 'difficult', 'hard']):
            mood = 'contemplative'
            title_theme = 'Reflection'
        else:
            mood = 'peaceful'
            title_theme = 'Daily Moment'
        
        # Create specific scene based on content
        if 'office' in text_lower and 'appraisal' in text_lower:
            scene_prompt = "A modern office building with glass windows reflecting golden sunlight, symbolizing success and achievement. A person in professional attire stands confidently in front of the building, with their arms crossed in a victorious pose. The scene captures the feeling of accomplishment and professional growth. Bright, uplifting lighting with warm tones, shot from a low angle to emphasize empowerment. The background shows a clear blue sky with a few white clouds, suggesting unlimited possibilities. Professional photography style, sharp focus, vibrant colors, inspiring atmosphere, 8k resolution."
        elif 'driving' in text_lower:
            scene_prompt = "A scenic open road stretching toward the horizon under a beautiful blue sky with scattered white clouds. A modern car is positioned on the road, ready for adventure. The landscape on both sides shows rolling hills and green fields, creating a sense of freedom and possibility. The lighting is bright and optimistic, with the sun positioned to create dramatic shadows and highlights. Shot from behind the car looking toward the endless road ahead, emphasizing the journey and adventure. Cinematic photography style, wide-angle lens, vibrant colors, sense of movement and freedom, 8k resolution."
        elif 'dog' in text_lower:
            scene_prompt = "A person walking peacefully with a golden retriever on a tree-lined path during golden hour. The dog is walking happily beside them, tail wagging, creating a heartwarming scene of companionship. Soft pink and orange hues fill the sky, casting a warm glow over everything. The path is surrounded by tall trees with dappled sunlight filtering through the leaves. The scene captures the healing power of nature and animal companionship. Shot with a gentle depth of field, warm color palette, peaceful atmosphere, professional photography style, 8k resolution."
        else:
            scene_prompt = f"A beautiful, serene landscape that reflects the mood of: '{text}'. The scene features natural elements like trees, water, or sky that create a peaceful, contemplative atmosphere. Soft, natural lighting enhances the emotional tone of the moment. The composition is balanced and harmonious, creating a sense of tranquility and reflection. Professional photography style, natural colors, peaceful mood, 8k resolution."
        
        return {
            "title": f"Visual Journal — {datetime.now().strftime('%Y-%m-%d')} — {title_theme}",
            "overall_mood": mood,
            "frames": [
                {
                    "title": title_theme,
                    "mood": mood,
                    "style": "cinematic photography",
                    "prompt": scene_prompt,
                    "reflection": f"Capturing the essence of: {text}"
                }
            ]
        }

    def _create_analysis_prompt(self, text: str) -> str:
        """Create a prompt for analyzing user input"""
        
        prompt = f"""
You are an expert visual storyteller who creates beautiful, meaningful scenes for display on TV screens. 

IMPORTANT: You must create a UNIQUE scene that directly reflects the SPECIFIC content of the user's journal entry. DO NOT use generic or repeated imagery.

CRITICAL REQUIREMENTS:
1. READ THE USER'S TEXT CAREFULLY and identify specific elements mentioned
2. Create scenes that DIRECTLY reflect what the user described
3. If user mentions "office" → create office/business scene
4. If user mentions "driving" → create road/car scene  
5. If user mentions "appraisal" → create success/achievement scene
6. If user mentions "dog" → include a dog in the scene
7. If user mentions specific emotions → reflect them in lighting and atmosphere
8. NEVER repeat the same scene - make each one unique to the user's input

USER'S JOURNAL ENTRY TO ANALYZE:
"{text}"

Based on this SPECIFIC input, create a JSON response with this structure:

{{
    "title": "Visual Journal — {datetime.now().strftime('%Y-%m-%d')} — [Theme from user's specific content]",
    "overall_mood": "[mood from user's actual text]",
    "frames": [
        {{
            "title": "[title reflecting user's specific content]",
            "mood": "[mood from user's text]",
            "style": "cinematic photography",
            "prompt": "[DETAILED scene description that DIRECTLY reflects what the user wrote about - be specific to their content]",
            "reflection": "[reflection about user's specific experience]"
        }}
    ]
}}

EXAMPLES OF CONTENT-SPECIFIC SCENES:
- Office + Appraisal → Modern office building, person in business attire, success imagery
- Driving → Open road, car, journey ahead, freedom imagery  
- Dog walk → Person with dog, park or nature setting, companionship
- Anxiety → Calming scene with soft lighting, peaceful elements

Create a scene that someone would immediately recognize as reflecting their specific journal entry.

Return ONLY the JSON response:
"""
        return prompt

    async def _generate_visual_frames(self, analysis: Dict[str, Any], width: int = 768, height: int = 768) -> List[VisualFrame]:
        """Generate visual frames with images using Runware API"""
        frames = []
        
        print(f"DEBUG: Generating frames with dimensions: {width}x{height}")
        print(f"DEBUG: Analysis data: {analysis}")
        
        # Initialize Runware
        runware = Runware(api_key=os.getenv("RUNWARE_API_KEY"))
        await runware.connect()
        
        # Enhanced negative prompt to avoid abstract patterns and ensure concrete scenes
        neg_prompt = "abstract patterns, random shapes, meaningless designs, geometric patterns, swirls, spirals, kaleidoscope, mandala, fractal, blurry, low resolution, pixelated, distorted, deformed, bad anatomy, poorly drawn, amateur, sketchy, rough, unfinished, low detail, flat lighting, overexposed, underexposed, noisy, grainy, artifacts, watermark, signature, text, letters, words, cropped, borders, frame, low contrast, washed out colors, dull, boring, generic, cliché, bad composition, cluttered, messy, chaotic, unclear subject, no focal point, confusing"
        
        for frame_data in analysis.get("frames", []):
            try:
                print(f"DEBUG: Processing frame: {frame_data['title']}")
                print(f"DEBUG: Frame prompt: {frame_data['prompt']}")
                
                # Create image generation request with custom dimensions
                request_image = IImageInference(
                    positivePrompt=frame_data["prompt"],
                    model="civitai:101055@128078",  # Using same model as painter_chat
                    numberResults=1,
                    negativePrompt=neg_prompt,
                    height=height,
                    width=width,
                )
                
                # Generate image
                images = await runware.imageInference(requestImage=request_image)
                print(f"DEBUG: Generated {len(images)} images")
                
                # Create frame with generated image
                frame = VisualFrame(
                    title=frame_data["title"],
                    image_url=images[0].imageURL if images else "",
                    reflection_text=frame_data["reflection"],
                    mood=frame_data["mood"],
                    style=frame_data["style"]
                )
                
                frames.append(frame)
                
            except Exception as e:
                print(f"DEBUG: Error generating frame: {e}")
                # Create frame without image if generation fails
                frame = VisualFrame(
                    title=frame_data["title"],
                    image_url="",
                    reflection_text=frame_data["reflection"],
                    mood=frame_data["mood"],
                    style=frame_data["style"]
                )
                frames.append(frame)
        
        return frames
