from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import style_transfer


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

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "deckoviz_ai"}
 