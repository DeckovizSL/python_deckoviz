# Deckoviz Personal Painter - Streamlit Interface

A web interface for the Deckoviz Personal Painter feature, allowing users to:

- Express their thoughts and emotions through text
- Receive emotional analysis of their input
- Generate art prompts based on their emotional state
- View a visualization representing their emotions

## Setup Instructions

1. Install the required dependencies:

```bash
pip install -r deckoviz_ai/streamlit/requirements.txt
```

2. (Optional) Set up your Stability API Key for actual image generation:
   - Create a `.env` file in the project root
   - Add your API key: `STABILITY_API_KEY=your_api_key_here`
   - Or enter it directly in the app's settings panel

3. Run the Streamlit app:

```bash
streamlit run deckoviz_ai/streamlit/app.py
```

## Docker Deployment

You can also run the app using Docker:

```bash
# Build the Docker image
docker build -f deckoviz_ai/streamlit/Dockerfile -t deckoviz-streamlit .

# Run the container
docker run -p 8501:8501 deckoviz-streamlit
```

The app will be available at `http://localhost:8501`.
