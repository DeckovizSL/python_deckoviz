"""
Personal Painter Module for Deckoviz AI

This module provides functionality for the Personal Painter feature of Deckoviz,
which helps users process emotions through AI-generated art. The Personal Painter
analyzes user's emotional states and creates personalized visual art experiences.
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Image generation imports
import requests

# Load environment variables
from dotenv import load_dotenv
load_dotenv()  # Load .env file from the current or parent directories

# Set up logging: only warnings and above
import logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Constants
DEFAULT_STYLE_PRESETS = [
    "3d-model", "analog-film", "anime", "cinematic", "comic-book", 
    "digital-art", "enhance", "fantasy-art", "isometric", "line-art", 
    "low-poly", "modeling-compound", "neon-punk", "origami", "photographic", 
    "pixel-art", "tile-texture"
]

EMOTION_TO_STYLE_MAP = {
    "joy": ["fantasy-art", "digital-art", "cinematic", "enhance"],
    "sadness": ["analog-film", "photographic", "line-art"],
    "anger": ["neon-punk", "comic-book", "3d-model"],
    "fear": ["low-poly", "isometric", "pixel-art"],
    "disgust": ["tile-texture", "modeling-compound"],
    "surprise": ["origami", "anime", "fantasy-art"],
    "neutral": ["enhance", "photographic", "digital-art"]
}

EMOTION_TO_COLOR_MAP = {
    "joy": ["vibrant", "yellow", "golden", "bright", "sunshine"],
    "sadness": ["blue", "gray", "muted", "dark blue", "faded"],
    "anger": ["red", "fiery", "crimson", "intense", "burning"],
    "fear": ["dark", "black", "shadowy", "misty", "gloomy"],
    "disgust": ["green", "sickly", "murky", "muddy"],
    "surprise": ["rainbow", "colorful", "sparkling", "glowing"],
    "neutral": ["balanced", "natural", "earthy", "soft"]
}

class PersonalPainter:
    """
    Main class for the Personal Painter functionality.
    Processes emotions and generates appropriate art.
    """
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 image_dir: str = "output/personal_painter",
                 max_history: int = 10):
        """
        Initialize the Personal Painter.
        
        Args:
            api_key: API key for image generation service
            image_dir: Directory to save generated images
            max_history: Maximum number of interactions to keep in history
        """
        # Try to get API key from parameter, then environment variable
        self.api_key = api_key or os.getenv("STABILITY_API_KEY")
        if not self.api_key:
            logger.warning("No Stability API key found. Image generation will be disabled.")
            logger.warning("Set STABILITY_API_KEY in your .env file or pass it as a parameter.")
        else:
            logger.info("Stability API key loaded successfully")
        self.image_dir = image_dir
        self.max_history = max_history
        self.user_history = []
        
        # Ensure the output directory exists and is absolute
        self.image_dir = os.path.abspath(self.image_dir)
        os.makedirs(self.image_dir, exist_ok=True)
        logger.info(f"Image directory set to: {self.image_dir}")
        
        logger.info("Personal Painter initialized")
    
    async def process_input(self, user_input: str) -> Dict:
        """
        Process user input and determine emotional content.
        
        Args:
            user_input: Text input from the user
            
        Returns:
            Dict containing processed information including emotional assessment
        """
        # Extract emotion (in a production system, this would use a proper emotion detection model)
        emotion_data = await self._analyze_emotion(user_input)
        
        # Add to user history
        self.user_history.append({
            "timestamp": datetime.now().isoformat(),
            "input": user_input,
            "emotion_data": emotion_data
        })
        
        # Limit history size
        if len(self.user_history) > self.max_history:
            self.user_history = self.user_history[-self.max_history:]
        
        return {
            "input": user_input,
            "emotion": emotion_data,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _analyze_emotion(self, text: str) -> Dict:
        """
        Analyze text to extract emotion (simplified version).
        In production, this would use a proper emotion detection model.
        
        Args:
            text: User input text
            
        Returns:
            Dict with detected emotion and confidence
        """
        # This is a simplified emotion detection - in production use a proper model
        emotions = ["joy", "sadness", "anger", "fear", "disgust", "surprise", "neutral"]
        
        # Very simple keyword matching (for demonstration only)
        emotion_keywords = {
            "joy": ["happy", "joy", "glad", "excited", "delighted", "pleased"],
            "sadness": ["sad", "unhappy", "depressed", "down", "melancholy", "grief"],
            "anger": ["angry", "mad", "furious", "outraged", "annoyed", "irritated"],
            "fear": ["afraid", "scared", "fearful", "terrified", "anxious", "worried"],
            "disgust": ["disgusted", "revolted", "repulsed", "sickened", "gross"],
            "surprise": ["surprised", "amazed", "astonished", "shocked", "startled"],
            "neutral": ["fine", "okay", "alright", "normal", "neutral"]
        }
        
        # Count keyword matches
        scores = {emotion: 0 for emotion in emotions}
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    scores[emotion] += 1
        
        # If no keywords matched, default to neutral
        if sum(scores.values()) == 0:
            primary_emotion = "neutral"
            confidence = 0.7
        else:
            # Get emotion with highest score
            primary_emotion = max(scores, key=scores.get)
            total = sum(scores.values())
            confidence = scores[primary_emotion] / total if total > 0 else 0.5
        
        return {
            "primary_emotion": primary_emotion,
            "confidence": confidence,
            "emotion_scores": scores
        }
    
    async def generate_art(self, 
                         emotion_data: Dict, 
                         user_input: str,
                         use_stable_diffusion: bool = True) -> Dict:
        """
        Generate art based on emotion and user input.
        
        Args:
            emotion_data: Dict with emotion analysis results
            user_input: Original user input
            use_stable_diffusion: Whether to use Stable Diffusion (if False, uses text prompt only)
            
        Returns:
            Dict with generated art info
        """
        # Create prompt for image generation
        prompt = await self._create_art_prompt(emotion_data, user_input)
        
        # Select style based on emotion
        style = self._select_style(emotion_data["primary_emotion"])
        
        image_bytes, filename = None, None
        error_message: Optional[str] = None
        
        try:
            if use_stable_diffusion and self.api_key:
                logger.info("Starting image generation with Stability API")
                image_bytes, filename = await self._call_image_generation_api(prompt, style)
                logger.info(f"Image generation complete, filename: {filename}")
            else:
                # Mock image generation for development
                logger.info(f"API key missing or mock mode enabled. Would generate image with prompt: {prompt}, style: {style}")
        except Exception as e:
            import traceback
            error_message = traceback.format_exc()
            logger.error(f"Unexpected error in generate_art: {e}")
            logger.error(error_message)
         
        # Return result
        result = {
            "prompt": prompt,
            "style": style,
            "image_bytes": image_bytes,
            "filename": filename,
            "emotion": emotion_data["primary_emotion"],
            "timestamp": datetime.now().isoformat()
        }
        # Include error message if any
        if error_message:
            result["error"] = error_message
         
        # Log summary without raw bytes
        logger.info(
            f"Generated art result: prompt={result.get('prompt')}, "
            f"filename={result.get('filename')}, emotion={result.get('emotion')}"
        )
        return result
    
    async def _create_art_prompt(self, emotion_data: Dict, user_input: str) -> str:
        """
        Create an art generation prompt based on emotion and user input.
        
        Args:
            emotion_data: Dict with emotion analysis
            user_input: User's original input
            
        Returns:
            String prompt for image generation
        """
        emotion = emotion_data["primary_emotion"]
        
        # Get color themes based on emotion
        color_themes = EMOTION_TO_COLOR_MAP.get(emotion, ["colorful"])
        
        # Extract key themes from user input (simplified)
        # In production, use a more sophisticated theme extraction
        words = user_input.lower().split()
        nouns = [word for word in words if len(word) > 3 and word not in ["this", "that", "with", "from"]]
        
        # Create base prompt
        if nouns:
            subject = ", ".join(nouns[:3])  # Take up to 3 main subjects
        else:
            # Default subjects based on emotion if none extracted
            emotion_subjects = {
                "joy": "sunlight streaming through trees",
                "sadness": "solitary figure in rain",
                "anger": "storm brewing over mountains",
                "fear": "dark forest pathway",
                "disgust": "abstract discordant shapes",
                "surprise": "unexpected cosmic event",
                "neutral": "peaceful landscape"
            }
            subject = emotion_subjects.get(emotion, "abstract painting")
        
        # Select a random color theme
        import random
        color_theme = random.choice(color_themes)
        
        # Create the prompt
        prompt = f"A {color_theme} artistic representation of {subject}, evoking feelings of {emotion}."
        
        # Add artistic quality terms
        artistic_terms = ["detailed", "high quality", "artistic", "professional"]
        prompt += f" {', '.join(artistic_terms)}"
        
        return prompt
    
    def _select_style(self, emotion: str) -> str:
        """
        Select an appropriate art style based on the detected emotion.
        
        Args:
            emotion: The primary detected emotion
            
        Returns:
            Style name for image generation
        """
        import random
        
        style_options = EMOTION_TO_STYLE_MAP.get(emotion, DEFAULT_STYLE_PRESETS)
        return random.choice(style_options)
    
    async def _call_image_generation_api(self, prompt: str, style: str) -> Optional[tuple[bytes, str]]:
        """
        Call image generation API (Stable Diffusion or similar).
        
        Args:
            prompt: Text prompt for image generation
            style: Style preset to use
            
        Returns:
            Tuple of image bytes and filename or None if generation failed
        """
        if not self.api_key:
            logger.error("Cannot call Stability API: No API key provided")
            return None
            
        logger.info(f"Calling Stability API with prompt: '{prompt}', style: '{style}'")
        logger.info(f"Using API key: {self.api_key[:4]}...{self.api_key[-4:] if len(self.api_key) > 8 else ''}")
        
        try:
            import base64
            
            # Use correct API endpoint for Stable Diffusion XL
            request_url = "https://api.stability.ai/v1alpha/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            logger.info(f"Making request to: {request_url}")
            
            request_payload = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 8,
                "style_preset": style,
                "height": 1024,
                "width": 1024,
                "samples": 1,
            }
            logger.info(f"Request payload: {json.dumps(request_payload)}")
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            logger.info("Headers prepared (auth header masked)")
            
            response = requests.post(
                request_url,
                headers=headers,
                json=request_payload
            )
            logger.info(f"API response status code: {response.status_code}")

            if response.status_code != 200:
                try:
                    error_details = response.json()
                    logger.error(f"API error details: {json.dumps(error_details)}")
                except Exception:
                    logger.error(f"API error response text: {response.text[:500]}")
            
            if response.status_code == 200:
                logger.info("API call successful!")
                data = response.json()
                if "artifacts" in data and len(data["artifacts"]) > 0:
                    logger.info(f"Received {len(data['artifacts'])} artifacts")
                    image_b64 = data["artifacts"][0]["base64"]
                    
                    # Decode and return image bytes and filename
                    image_bytes = base64.b64decode(image_b64)
                    # Generate filename
                    try:
                        emotion = prompt.split("evoking feelings of")[1].split(".")[0].strip()
                    except:
                        emotion = "emotion"
                    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{emotion}.png"
                    return image_bytes, filename
                else:
                    logger.error("No artifacts found in the API response")
            else:
                logger.error(f"Error from Stability API: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            import traceback
            logger.error(f"Exception calling image generation API: {e}")
            logger.error(traceback.format_exc())
            
        return None
    
    def get_user_history(self) -> List[Dict]:
        """Get the user interaction history."""
        return self.user_history
    
    def clear_history(self) -> None:
        """Clear the user interaction history."""
        self.user_history = []
        logger.info("User history cleared")

# Utility functions for the Personal Painter
async def process_emotion_and_generate_art(painter: PersonalPainter, user_input: str) -> Dict:
    """
    Process user input and generate art in one step.
    
    Args:
        painter: PersonalPainter instance
        user_input: User's input text
        
    Returns:
        Dict with processed info and generated art
    """
    # Process the input
    processed = await painter.process_input(user_input)
    
    # Generate art based on emotion
    art_result = await painter.generate_art(processed["emotion"], user_input)
    
    return {
        "processed": processed,
        "art": art_result
    }

async def personal_painter_callback(session, user_input: str, **kwargs) -> Dict:
    """
    Callback function to use with agent system.
    
    Args:
        session: The agent session
        user_input: User's input text
        kwargs: Additional parameters
        
    Returns:
        Dict with processing results
    """
    # Create painter instance if it doesn't exist in the session
    if not hasattr(session, "personal_painter"):
        session.personal_painter = PersonalPainter()
    
    # Process input and generate art
    result = await process_emotion_and_generate_art(session.personal_painter, user_input)
    
    # If there's an image path, prepare it for display
    if result["art"]["image_bytes"]:
        # Return data for the agent to use
        return {
            "image_bytes": result["art"]["image_bytes"],
            "filename": result["art"]["filename"],
            "prompt": result["art"]["prompt"],
            "emotion": result["art"]["emotion"]
        }
    else:
        # If no image was generated, just return the emotion and prompt
        return {
            "prompt": result["art"]["prompt"],
            "emotion": result["art"]["emotion"]
        }

# Example prompt for personal painter mode
PERSONAL_PAINTER_PROMPT = """
You are the Personal Painter, an AI assistant specialized in helping users process emotions through art.
Your goal is to understand the user's emotional state and create personalized visual art experiences.

When interacting with the user:
1. Listen carefully to understand their emotional state and needs
2. Respond with empathy and understanding
3. Ask meaningful questions about their feelings or what they'd like to express through art
4. Generate art that reflects their emotional state or helps them process their emotions
5. Explain how the art connects to their emotions and experiences
6. Be supportive and non-judgmental throughout the conversation

Remember that art is a powerful tool for emotional expression and healing.
Your primary role is to help users explore and process their emotions through visual art.
"""