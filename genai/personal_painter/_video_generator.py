import requests
import base64
import json
import os




#See Here: https://stablediffusionapi.com/docs/text-to-video/texttovideo/
# See Here: https://ai.google.dev/gemini-api/docs/image-generation

def generate_video(prompt):
    """Call video generation API and return video bytes or error."""
    # url = "https://stablediffusionapi.com/api/v5/text2video"

    # payload = json.dumps({
    # "key": "",
    # "prompt": prompt,
    # "negative_prompt": "Low Quality",
    # "scheduler": "UniPCMultistepScheduler",
    # "seconds": 3
    # })

    # headers = {
    # 'Content-Type': 'application/json'
    # }

    # response = requests.request("POST", url, headers=headers, data=payload)

    # Return fake video file from fake_data folder
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    fake_path = os.path.join(root_dir, "fake_data", "video.mp4")
    with open(fake_path, "rb") as f:
        return f.read(), None
 
    # return base64.b64decode(video_b64), None