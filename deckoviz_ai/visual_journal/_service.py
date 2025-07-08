from ..llm import GeminiLLM
from ._prompt import VISUAL_JOURNAL_SYSTEM_PROMPT
from schemas.visual_journal import UserInput, VisualJournalEntry, VisualFrame, VisualJournalHistoryEntry
import json
import os
import uuid
import sqlite3
from datetime import datetime
from runware import Runware, IImageInference
from typing import List, Dict, Any, Optional

class VisualJournalService:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.llm = GeminiLLM(model_name=model_name)

    async def generate_visual_journal(self, user_input: UserInput, user_id: str) -> VisualJournalEntry:
        """Generate a complete visual journal entry with images"""
        # Step 1: Analyze the user's input and generate image prompts
        analysis = await self._analyze_user_input(user_input.text, user_input.num_frames)
        
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
        
        # Step 4: Save to database
        await self._save_to_database(journal_entry, user_id, user_input.text)
        
        return journal_entry

    async def _analyze_user_input(self, text: str, num_frames: int = 1) -> Dict[str, Any]:
        """Analyze user input and extract key elements for visualization"""
        prompt = self._create_analysis_prompt(text, num_frames)
        
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
            return self._create_dynamic_fallback(text, num_frames)
        except Exception as e:
            print(f"DEBUG: Other error occurred: {e}")
            return self._create_dynamic_fallback(text, num_frames)

    def _create_dynamic_fallback(self, text: str, num_frames: int = 1) -> Dict[str, Any]:
        """Create a dynamic fallback based on the actual user input"""
        print(f"DEBUG: Creating dynamic fallback for: {text} with {num_frames} frames")
        
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
            title_theme = 'From Shadow to Light'
        else:
            mood = 'peaceful'
            title_theme = 'Daily Moment'
        
        # Create frames based on content analysis
        frames = []
        
        # For the specific input about anxiety and dog walk, create appropriate frames
        if 'anxious' in text_lower and 'dog' in text_lower and num_frames >= 2:
            frames = [
                {
                    "title": "Morning Struggle",
                    "mood": "anxious",
                    "style": "cinematic photography",
                    "prompt": "A person sitting on the edge of their bed in dim morning light, head in hands, showing the weight of anxiety and worry. Soft, muted lighting filters through partially closed curtains, creating a melancholic atmosphere. The room feels heavy with unspoken thoughts, captured with shallow depth of field to emphasize the isolation. Cool color tones dominate the scene - blues and grays - representing the emotional state. Professional photography style, intimate composition, contemplative mood, 8k resolution.",
                    "reflection": "The morning heaviness that clouds the start of the day"
                },
                {
                    "title": "Evening Healing",
                    "mood": "hopeful",
                    "style": "cinematic photography", 
                    "prompt": "A person walking peacefully with a golden retriever on a tree-lined path during golden hour. The sky displays soft pink and orange hues, casting a warm, healing glow over the scene. The dog walks happily beside them, tail wagging, symbolizing companionship and joy. Gentle sunlight filters through the trees, creating a magical atmosphere of renewal and hope. The scene captures the transformative power of nature and connection. Warm color palette, professional photography style, peaceful composition, 8k resolution.",
                    "reflection": "Finding light and healing through simple moments with a faithful companion"
                }
            ]
        elif 'office' in text_lower and 'appraisal' in text_lower:
            frames.append({
                "title": "Professional Triumph",
                "mood": "accomplished",
                "style": "cinematic photography",
                "prompt": "A modern glass office building reflecting golden sunlight, with a confident professional standing in front, arms crossed in victory. The scene symbolizes career success and achievement. Bright, uplifting lighting with warm tones, shot from a low angle to emphasize empowerment. Clear blue sky with clouds in the background, suggesting unlimited possibilities. Professional photography style, inspiring atmosphere, 8k resolution.",
                "reflection": "Recognition and success in professional endeavors"
            })
        elif 'driving' in text_lower:
            frames.append({
                "title": "Open Road Ahead",
                "mood": "adventurous",
                "style": "cinematic photography",
                "prompt": "A scenic open road stretching toward the horizon under a beautiful blue sky with scattered white clouds. A modern car positioned on the road, ready for adventure. Rolling hills and green fields on both sides, creating a sense of freedom and possibility. Bright, optimistic lighting with dramatic shadows. Wide-angle perspective emphasizing the journey ahead. Vibrant colors, sense of movement, 8k resolution.",
                "reflection": "The excitement of new journeys and adventures ahead"
            })
        
        # If we still need more frames or haven't created any, add generic ones
        while len(frames) < num_frames:
            frame_titles = ["Peaceful Reflection", "Inner Strength", "Quiet Moment", "Gentle Light", "Serene Thoughts", "Calm Waters"]
            title = frame_titles[len(frames)] if len(frames) < len(frame_titles) else f"Frame {len(frames) + 1}"
            
            frames.append({
                "title": title,
                "mood": mood,
                "style": "cinematic photography",
                "prompt": f"A beautiful, serene landscape that reflects the mood of: '{text}'. The scene features natural elements like trees, water, or sky that create a peaceful, contemplative atmosphere. Soft, natural lighting enhances the emotional tone of the moment. The composition is balanced and harmonious, creating a sense of tranquility and reflection. Professional photography style, natural colors, peaceful mood, 8k resolution.",
                "reflection": f"Capturing the essence of today's experience: {text[:100]}..."
            })
        
        # Trim to exact number requested
        frames = frames[:num_frames]
        
        return {
            "title": f"Visual Journal — {datetime.now().strftime('%Y-%m-%d')} — {title_theme}",
            "overall_mood": mood,
            "frames": frames
        }

    def _create_analysis_prompt(self, text: str, num_frames: int = 1) -> str:
        """Create a prompt for analyzing user input"""
        
        frames_instruction = f"Create exactly {num_frames} frame{'s' if num_frames > 1 else ''} based on the user's journal entry."
        if num_frames > 1:
            frames_instruction += " Each frame should represent a different aspect, moment, or emotion from their experience."
        
        prompt = f"""
You are an expert visual storyteller who creates beautiful, meaningful scenes for display on TV screens. 

IMPORTANT: You must create a UNIQUE scene that directly reflects the SPECIFIC content of the user's journal entry. DO NOT use generic or repeated imagery.

FRAME REQUIREMENTS: {frames_instruction}

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
        {self._generate_frame_template(num_frames)}
    ]
}}

EXAMPLES OF CONTENT-SPECIFIC SCENES:
- Office + Appraisal → Modern office building, person in business attire, success imagery
- Driving → Open road, car, journey ahead, freedom imagery  
- Dog walk → Person with dog, park or nature setting, companionship
- Anxiety → Calming scene with soft lighting, peaceful elements

Create {num_frames} scene{'s' if num_frames > 1 else ''} that someone would immediately recognize as reflecting their specific journal entry.

Return ONLY the JSON response:
"""
        return prompt

    def _generate_frame_template(self, num_frames: int) -> str:
        """Generate the frame template for the JSON structure"""
        frame_template = '''
        {
            "title": "[title reflecting user's specific content]",
            "mood": "[mood from user's text]",
            "style": "cinematic photography",
            "prompt": "[DETAILED scene description that DIRECTLY reflects what the user wrote about - be specific to their content]",
            "reflection": "[reflection about user's specific experience]"
        }'''
        
        if num_frames == 1:
            return frame_template
        else:
            templates = []
            for i in range(num_frames):
                templates.append(frame_template)
            return ',\n        '.join(templates)

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

    async def _save_to_database(self, journal_entry: VisualJournalEntry, user_id: str, original_text: str):
        """Save the journal entry to database"""
        try:
            entry_id = str(uuid.uuid4())
            
            # Create the visual_journal_entries table if it doesn't exist
            conn = sqlite3.connect('data/chat_history.db')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS visual_journal_entries (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    original_text TEXT NOT NULL,
                    overall_mood TEXT NOT NULL,
                    date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    frames_data TEXT NOT NULL
                )
            ''')
            
            # Insert the journal entry
            cursor.execute('''
                INSERT INTO visual_journal_entries 
                (id, user_id, title, original_text, overall_mood, date, created_at, frames_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_id,
                user_id,
                journal_entry.title,
                original_text,
                journal_entry.overall_mood,
                journal_entry.date,
                datetime.now().isoformat(),
                json.dumps([frame.dict() for frame in journal_entry.frames])
            ))
            conn.commit()
            conn.close()
                
        except Exception as e:
            print(f"DEBUG: Error saving to database: {e}")

    async def get_journal_timeline(self, user_id: str, limit: int = 20) -> List[VisualJournalHistoryEntry]:
        """Get the visual journal timeline for a user"""
        try:
            conn = sqlite3.connect('data/chat_history.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, overall_mood, date, created_at, frames_data, original_text
                FROM visual_journal_entries
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            entries = []
            for row in cursor.fetchall():
                frames_data = json.loads(row[5])
                original_text = row[6] if len(row) > 6 else ""
                
                # Extract frame information
                all_frame_urls = [frame['image_url'] for frame in frames_data if frame.get('image_url')]
                frame_titles = [frame['title'] for frame in frames_data]
                preview_image_url = all_frame_urls[0] if all_frame_urls else ""
                
                # Create journey summary
                if len(frames_data) > 1:
                    journey_summary = f"A {len(frames_data)}-part visual journey: {' → '.join(frame_titles[:3])}"
                    if len(frame_titles) > 3:
                        journey_summary += f" + {len(frame_titles) - 3} more"
                else:
                    journey_summary = f"Single moment: {frame_titles[0] if frame_titles else 'Visual reflection'}"
                
                entry = VisualJournalHistoryEntry(
                    id=row[0],
                    title=row[1],
                    overall_mood=row[2],
                    date=row[3],
                    created_at=row[4],
                    frame_count=len(frames_data),
                    preview_image_url=preview_image_url,
                    all_frame_urls=all_frame_urls,
                    frame_titles=frame_titles,
                    original_text_preview=original_text[:100] + "..." if len(original_text) > 100 else original_text,
                    journey_summary=journey_summary
                )
                entries.append(entry)
            
            conn.close()
            return entries
                
        except Exception as e:
            print(f"DEBUG: Error getting timeline: {e}")
            return []

    async def get_journal_entry_by_id(self, entry_id: str, user_id: str) -> Optional[VisualJournalEntry]:
        """Get a specific journal entry by ID"""
        try:
            conn = sqlite3.connect('data/chat_history.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, overall_mood, date, frames_data
                FROM visual_journal_entries
                WHERE id = ? AND user_id = ?
            ''', (entry_id, user_id))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                frames_data = json.loads(row[3])
                frames = [VisualFrame(**frame) for frame in frames_data]
                
                return VisualJournalEntry(
                    title=row[0],
                    frames=frames,
                    overall_mood=row[1],
                    date=row[2],
                    saved_to="My Visual Journal"
                )
                
        except Exception as e:
            print(f"DEBUG: Error getting entry by ID: {e}")
            return None
