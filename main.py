from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    style_transfer,
    generate_art,
    onboard,
    painter_chat,
    embedding,
    moodboard,
    poster,
    mindscape,
    image,
    dream_visualizer,
    brand_asset,
    image_meta_gen,
    book_to_frames_router,
    dream_visualizer_chat,
    audio,
    vizzy,
    replicate_style_transfer,
)
from database.sqlite import create_sqlite_db

# Initialize database
create_sqlite_db()

app = FastAPI(title="Deckoviz AI API", 
              description="AI services for Deckoviz platform", 
              version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
 
# Include routers
app.include_router(audio.router, prefix="/audio", tags=['Audio Processing'])
# app.include_router(image.router, prefix="/personal-painter", tags=['Personal Painter'])
app.include_router(onboard.router, prefix="/onboard", tags=["onboard"])
app.include_router(style_transfer.router, prefix="/style_transfer", tags=["style_transfer"])
app.include_router(painter_chat.router, prefix="/painter_chat", tags=["painter_chat"])
app.include_router(embedding.router, prefix="/embedding", tags=["embedding"])
app.include_router(moodboard.router, prefix="/moodboard", tags=["moodboard"])
app.include_router(poster.router, prefix="/poster", tags=["poster"])
app.include_router(mindscape.router, prefix="/mindscape", tags=["mindscape"])
app.include_router(generate_art.router, prefix="/generate_art", tags=["generate_art"])
app.include_router(image.router, prefix="/image", tags=["image"])
app.include_router(dream_visualizer.router, prefix="/dream-visualizer", tags=["dream-visualizer"])
app.include_router(brand_asset.router, prefix="/brand-asset", tags=["brand-asset"])
app.include_router(image_meta_gen.router, prefix="/image-meta-gen", tags=["Image Metadata Generation"])
app.include_router(book_to_frames_router, prefix="/book_to_frames", tags=["book_to_frames"])
app.include_router(dream_visualizer_chat.router, prefix="/dream-visualizer-chat", tags=["Dream Visualizer Chat"])
app.include_router(vizzy.router, prefix="/vizzy", tags=["Vizzy Voice Assistant"])
app.include_router(replicate_style_transfer.router, prefix="/replicate_style_transfer", tags=["replicate_style_transfer"])

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "deckoviz_ai"}
 