# app.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "common.deckoviz.settings")
django.setup()

from fastapi import FastAPI, Depends
import logging
from fastapi.middleware.cors import CORSMiddleware
import sys
from routers import device_pairing, device_ws
# Ensure debug logs for all modules (including WebSocket router)
logging.basicConfig(level=logging.DEBUG)

# Ensure project root (parent of api) is on PYTHONPATH so deckoviz_ai is importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from routers import  websocket, rooms, qr_code_redis, curations, curations
from databases.configs import get_redis_client
from middleware.logging import RequestLoggingMiddleware

# Initialize the application
app = FastAPI()

# Add request logging middleware (should be first)
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers 
app.include_router(websocket.router)
app.include_router(rooms.router)
app.include_router(qr_code_redis.router)
app.include_router(curations.router)

# THE 2 NEW ADDED ROUTES FOR QR CODE SCANNER
app.include_router(device_pairing.router)
app.include_router(device_ws.router)

@app.get("/", dependencies=[Depends(get_redis_client)])
async def root():
    return {"message": "Welcome to the Deckoviz API."}
