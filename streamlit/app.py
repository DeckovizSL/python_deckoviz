"""
Streamlit application for Deckoviz Personal Painter

This app provides a web interface for the Personal Painter feature,
allowing users to input their emotions and generate personalized art experiences.
"""

import os
import json
import asyncio
import streamlit as st
from PIL import Image
from datetime import datetime
import base64
from io import BytesIO
import requests
from dotenv import load_dotenv, find_dotenv
import pathlib
import sys

# Ensure deckoviz_ai package is on sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# Load environment variables from nearest .env file
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)
    # print(f"Loaded .env from {dotenv_path}")

# Set page configuration
st.set_page_config(
    page_title="Deckoviz Personal Painter",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .emotion-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .prompt-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #000;
        color: #fff;
        margin: 1rem 0;
        font-style: italic;
    }
    .history-item {
        padding: 0.5rem;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def get_emotion_color(emotion):
    """Return a color based on the emotion"""
    emotion_colors = {
        "joy": "#FFC107",       # Yellow
        "sadness": "#0D47A1",   # Deep Blue
        "anger": "#D32F2F",     # Red
        "fear": "#455A64",      # Dark Grey
        "disgust": "#558B2F",   # Green
        "surprise": "#7B1FA2",  # Purple
        "neutral": "#607D8B"    # Blue Grey
    }
    return emotion_colors.get(emotion, "#607D8B")

def get_emotion_emoji(emotion):
    """Return an emoji based on the emotion"""
    emotion_emojis = {
        "joy": "😊",
        "sadness": "😢",
        "anger": "😠",
        "fear": "😨",
        "disgust": "🤢",
        "surprise": "😲",
        "neutral": "😐"
    }
    return emotion_emojis.get(emotion, "🎨")

def create_color_image(emotion):
    """Create a gradient image based on the emotion"""
    # Get a color theme for the emotion
    color_themes = EMOTION_TO_COLOR_MAP.get(emotion, ["colorful"])
    import random
    color_theme = random.choice(color_themes)
    
    # Create a simple gradient image
    width, height = 512, 512
    from PIL import Image, ImageDraw
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    
    if color_theme == "vibrant" or color_theme == "colorful" or color_theme == "rainbow":
        # Create rainbow gradient
        colors = ["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#9400D3"]
        for i, color in enumerate(colors):
            draw.rectangle([0, i * height // len(colors), width, (i + 1) * height // len(colors)], fill=color)
    else:
        # Create gradient based on emotion color
        base_color = get_emotion_color(emotion)
        # Convert hex to RGB
        r = int(base_color[1:3], 16)
        g = int(base_color[3:5], 16)
        b = int(base_color[5:7], 16)
        
        for y in range(height):
            # Create a gradient effect
            factor = y / height
            r_new = int(r * (1 - factor) + 255 * factor)
            g_new = int(g * (1 - factor) + 255 * factor)
            b_new = int(b * (1 - factor) + 255 * factor)
            draw.line([(0, y), (width, y)], fill=(r_new, g_new, b_new))
    
    return image

async def async_process_input(user_input):
    """Process user input asynchronously"""
    # Initialize the Personal Painter
    # Determine output directory relative to project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    output_dir = os.path.join(project_root, "output", "personal_painter")
    
    # Use session API key or fallback to env var
    key = st.session_state.stability_api_key or os.getenv("STABILITY_API_KEY", "")
    painter = PersonalPainter(api_key=key, image_dir=output_dir)
    
    # Process the input and generate art
    result = await process_emotion_and_generate_art(painter, user_input)
    return result

def run_async(coroutine):
    """Run an async function synchronously"""
    import asyncio
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(coroutine)
    loop.close()
    return result

# Mode selection
mode = st.sidebar.selectbox(
    "Select Mode",
    ["Text to Image", "Text to Video", "Style Transfer"]
)

# Initialize session state for history and API key
if 'history' not in st.session_state:
    st.session_state.history = []
if 'stability_api_key' not in st.session_state:
    st.session_state.stability_api_key = os.getenv('STABILITY_API_KEY', '')

# App header
st.markdown("<h1 class='main-header'>Deckoviz Personal Painter</h1>", unsafe_allow_html=True)
st.markdown(
    "Transform your emotions into art with Deckoviz's Personal Painter. "
    "Enter your thoughts and feelings to create a personalized artistic experience."
)

# Main content area
col1, col2 = st.columns([3, 2])

with col1:
    if mode == "Text to Image":
        # User input section
        st.markdown("<h2 class='sub-header'>Express Yourself</h2>", unsafe_allow_html=True)
        user_input = st.text_area(
            "Share your thoughts, feelings, or experiences...",
            height=150,
            placeholder="For example: I'm feeling really excited about my upcoming vacation to the mountains..."
        )
        
        submit_button = st.button("Generate Art", type="primary")
        
        # Process input when button is clicked
        if submit_button and user_input:
            with st.spinner("Analyzing your emotions and creating art..."):
                # Process the input
                result = run_async(async_process_input(user_input))
                
                # Raw JSON debug in an expander
                with st.expander("Show raw art JSON"):
                    st.json(result["art"])
                
                # Add to history
                st.session_state.history.append({
                    "input": user_input,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Display results
                emotion_data = result["processed"]["emotion"]
                art_data = result["art"]
                
                # Emotion analysis results
                primary_emotion = emotion_data["primary_emotion"]
                confidence = emotion_data["confidence"]
                emotion_color = get_emotion_color(primary_emotion)
                emotion_emoji = get_emotion_emoji(primary_emotion)
                
                st.markdown(f"<h2 class='sub-header'>Emotional Analysis</h2>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='emotion-box' style='background-color: {emotion_color}; color: white;'>"
                    f"<h3>{emotion_emoji} {primary_emotion.capitalize()}</h3>"
                    f"<p>Confidence: {confidence:.2f}</p>"
                    "</div>",
                    unsafe_allow_html=True
                )
                
                # Art prompt
                st.markdown("<h2 class='sub-header'>Art Prompt</h2>", unsafe_allow_html=True)
                st.markdown(f"<div class='prompt-box'>{art_data['prompt']}</div>", unsafe_allow_html=True)
                
                # Display the generated image or a placeholder
                st.markdown("<h2 class='sub-header'>Visual Representation</h2>", unsafe_allow_html=True)
                
                image_bytes = art_data.get('image_bytes')
                if image_bytes:
                    st.image(image_bytes, caption=f"Generated art: {art_data['prompt']}", use_container_width=True)
                else:
                    error_message = art_data.get('error', '')
                    if error_message:
                        st.error(f"Image generation error: {error_message}")
                    else:
                        st.error("Image generation wasn't successful.")
    elif mode == "Text to Video":
        st.markdown("<h2 class='sub-header'>Text to Video Generation</h2>", unsafe_allow_html=True)
        video_prompt = st.text_area(
            "Enter a prompt for video generation...",
            height=150,
            placeholder="For example: A calm beach at sunset with gentle waves"
        )
        if st.button("Generate Video", type="primary"):
            with st.spinner("Generating video..."):
                if not st.session_state.stability_api_key:
                    st.error("Please enter your Stability API key.")
                    # return
                video_bytes, error = video_generator.generate_video(video_prompt)
                if error:
                    st.error(f"Video generation error: {error}")
                else:
                    st.video(video_bytes, format="video/mp4", start_time=0)
    elif mode == "Style Transfer":
        st.markdown("<h2 class='sub-header'>Image Style Transfer</h2>", unsafe_allow_html=True)
        source_img = st.file_uploader("Upload source image", type=["png", "jpg", "jpeg"])
        style_img = st.file_uploader("Upload style reference image", type=["png", "jpg", "jpeg"])
        if st.button("Transfer Style", type="primary"):
            if source_img and style_img:
                with st.spinner("Transferring style..."):
                    img_bytes, error = st_transfer.style_transfer(source_img, style_img)
                    if error:
                        st.error(f"Style transfer error: {error}")
                    else:
                        st.image(img_bytes, caption="Stylized image", use_container_width=True)
            else:
                st.warning("Please upload both source and style images.")

with col2:
    # History/sidebar section
    st.markdown("<h2 class='sub-header'>Your Art History</h2>", unsafe_allow_html=True)
    
    if not st.session_state.history:
        st.info("Your art creation history will appear here after you generate your first piece.")
    else:
        # Display history in reverse order (newest first)
        for item in reversed(st.session_state.history):
            primary_emotion = item["result"]["processed"]["emotion"]["primary_emotion"]
            emotion_emoji = get_emotion_emoji(primary_emotion)
            timestamp = datetime.fromisoformat(item["timestamp"]).strftime("%H:%M:%S")
            
            st.markdown(
                f"<div class='history-item'>"
                f"<p><strong>{timestamp}</strong> {emotion_emoji} {primary_emotion.capitalize()}</p>"
                f"<p><em>{item['input'][:50]}{'...' if len(item['input']) > 50 else ''}</em></p>"
                f"</div>",
                unsafe_allow_html=True
            )
    
    # Settings
    st.markdown("<h2 class='sub-header'>Settings</h2>", unsafe_allow_html=True)
    
    with st.expander("API Settings"):
        current_key = st.session_state.stability_api_key
        masked_key = "••••••" + current_key[-4:] if current_key else ""
        
        st.info(
            f"Current API key status: {'Active' if current_key else 'Not set'} {masked_key}"
        )
        
        # Add a test API connection button
        if current_key:
            if st.button("Test API Connection"):
                with st.spinner("Testing connection to Stability AI API..."):
                    try:
                        # Simple test request
                        response = requests.get(
                            "https://api.stability.ai/v1/user/balance",
                            headers={
                                "Authorization": f"Bearer {current_key}"
                            }
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ Connection successful! Credits remaining: {data.get('credits', 'unknown')}")
                        else:
                            error_msg = "Unknown error"
                            try:
                                error_data = response.json()
                                error_msg = error_data.get('message', 'Unknown error')
                            except:
                                error_msg = response.text[:100] if response.text else "No error details available"
                                
                            st.error(f"❌ API Test Failed: Status {response.status_code}, Error: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Connection Error: {str(e)}")
        
        api_key = st.text_input(
            "Update Stability API Key", 
            value=current_key,
            type="password",
            placeholder="Enter new API key here to update",
            help="For image generation using Stability AI. Will be saved for this session only."
        )
        if api_key:
            st.session_state.stability_api_key = api_key
            st.success("API key updated for this session!")
    
    # Clear history button
    if st.button("Clear History", type="secondary"):
        st.session_state.history = []
        st.success("History cleared!")

# Footer
st.markdown("---")
st.markdown(
    "Deckoviz Personal Painter | AI-powered Smart Art Frame | "
    " 2025 Deckoviz"
)

from deckoviz_ai.personal_painter import st_transfer, video_generator
from deckoviz_ai.personal_painter.personal_painter import (
    PersonalPainter,
    process_emotion_and_generate_art,
    EMOTION_TO_COLOR_MAP,
)
