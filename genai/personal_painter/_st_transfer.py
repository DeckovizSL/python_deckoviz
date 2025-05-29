import requests
import os
import base64
from dotenv import load_dotenv

load_dotenv()

# See Here: 
def style_transfer(source_file, style_file):
    """Call style transfer API and return image bytes or error."""
    # api_key = os.getenv('STABILITY_API_KEY', '')
    # headers = {"Authorization": f"Bearer {api_key}"}
    # files = {
    #     "init_image": source_file.getvalue(),
    #     "style_image": style_file.getvalue()
    # }
    # data = {"image_strength": 0.8}
    # img_engine = "stable-diffusion-xl-1024-v1-0"
    # url = f"https://api.stability.ai/v1alpha/generation/{img_engine}/image-to-image"
    # response = requests.post(url, headers=headers, files=files, data=data)
    # if response.status_code != 200:
    #     return None, response.text
    # data_json = response.json()
    # img_b64 = data_json["artifacts"][0]["base64"]
    # return base64.b64decode(img_b64), None

    # Return fake image file from fake_data folder
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    fake_path = os.path.join(root_dir, "fake_data", "image.jpg")
    with open(fake_path, "rb") as f:
        return f.read(), None
