from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import style_transfer, generate_art, onboard, painter_chat,metadata_generator


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
# app.include_router(audio.router, prefix="/audio", tags=['Audio Processing'])
# app.include_router(image.router, prefix="/personal-painter", tags=['Personal Painter'])
app.include_router(style_transfer.router, prefix="/style-transfer", tags=['Style Transfer'])
app.include_router(generate_art.router, prefix="/generate-art", tags=['Generate Art'])
app.include_router(onboard.router, prefix="/onboarding", tags=['Onboarding'])
app.include_router(painter_chat.router, prefix="/painter-chat", tags=['Painter Chat'])
app.include_router(metadata_generator.router, prefix="/metadata-generator", tags=['Metadata Generator'])

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "deckoviz_ai"}
 