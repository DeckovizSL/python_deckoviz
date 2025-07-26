from fastapi import APIRouter
import os 
from deckoviz_ai.onboarding import VoiceCallHandler, OnboardingGraph, OnboardingState
from core.memory import PostgresChatMemory
from models.chat import OnboardingSession
from database.connection import Session,get_db
import uuid
from typing import Dict
from fastapi import WebSocket, Depends, Request
import json
from datetime import datetime
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from fastapi import WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from redis import Redis
from utils.settings import get_settings
from langchain.schema import HumanMessage 
from utils.token import get_current_user
from schemas.user import User 

load_dotenv()
 
settings = get_settings()

redis_client = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password,
    db=settings.redis_db,
    decode_responses=True
)

def get_session(session_id: str):
    """Retrieve session from Redis or return None if not found"""
    session_data = redis_client.get(f"session:{session_id}")
    if session_data:
        data = json.loads(session_data)
        # Create memory with the session_id
        memory = PostgresChatMemory(session_id)
        # Create graph with the memory
        graph = OnboardingGraph(memory)
        return memory, graph
    return None, None

def save_session(session_id: str, memory, graph):
    """Save session data to Redis"""
    # Just store the session_id itself since we'll reconstruct objects
    # from the session_id in get_session
    redis_client.set(f"session:{session_id}", json.dumps({
        "session_id": session_id
    }))
    # Set expiration (24 hours)
    redis_client.expire(f"session:{session_id}", 86400)


# Initialize voice handler
voice_handler = VoiceCallHandler(
    twilio_sid=os.getenv("TWILIO_SID"),
    twilio_token=os.getenv("TWILIO_TOKEN"),
    twilio_phone=os.getenv("TWILIO_PHONE")
)

# Setup templates directory for HTML templates
templates = Jinja2Templates(directory="templates")

router = APIRouter()

@router.get("/start-onboarding", response_class=HTMLResponse)
async def get_onboarding_page(request: Request):
    """Serve the onboarding HTML page"""
    return templates.TemplateResponse("onboarding.html", {"request": request})

@router.get("/start-onboarding-api")
async def start_onboarding_api(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Start a new onboarding session and return JSON response"""
    session_id = str(uuid.uuid4())
    
    # Create chat memory
    memory = PostgresChatMemory(session_id)
    
    # Create onboarding graph
    graph = OnboardingGraph(memory)
    
    # Save to Redis
    save_session(session_id, memory, graph)
    
    # Create record in database
    db_session = OnboardingSession(
        session_id=session_id,
        user_id=user_id,
        status="active"
        # started_at will be set by default in the model
    )
    db.add(db_session)
    db.commit()
    
    return {"session_id": session_id, "status": "started"}

@router.post("/start-onboarding")
async def start_onboarding(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Start a new onboarding session"""
    session_id = str(uuid.uuid4())
    
    # Create session in database
    db_session = OnboardingSession(
        user_id=user_id,
        session_id=session_id,
        status="active"
    )
    db.add(db_session)
    db.commit()
    
    # Initialize memory and graph
    memory = PostgresChatMemory(session_id)
    graph = OnboardingGraph(memory)
    
    # Store in active sessions
    save_session(session_id, memory, graph)
    
    return {"session_id": session_id, "status": "started"}

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    memory, graph = get_session(session_id)
    if not memory or not graph:
        await websocket.send_text(json.dumps({"type": "error", "message": "Invalid session"}))
        return
    
    # Initialize state
    state = OnboardingState(
        messages=[],
        current_step="greeting",  # Set initial step name
        user_data={},
        voice_call_scheduled=False,
        session_complete=False
    )
    
    try:
        # Send initial greeting
        state = await graph.graph.ainvoke(state)
        await websocket.send_text(json.dumps({
            "type": "message",
            "content": state["messages"][-1].content if state["messages"] else "Welcome to Deckoviz AI onboarding!",
            "step": state["current_step"]
        }))
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "message":
                # Add user message to memory
                await memory.add_message("human", message_data["content"])
                
                # Create a human message
                human_msg = HumanMessage(content=message_data["content"])
                
                # Update state with the new message
                current_messages = state.get("messages", [])
                state["messages"] = current_messages + [human_msg]
                
                # Process through graph
                state = await graph.graph.ainvoke(state)
                
                # Send AI response
                if state["messages"] and len(state["messages"]) > 0:
                    last_message = state["messages"][-1]
                    await websocket.send_text(json.dumps({
                        "type": "message",
                        "content": last_message.content,
                        "step": state["current_step"]
                    }))
                
                # Check if voice call should be initiated
                if state.get("voice_call_scheduled") and not state.get("voice_call_initiated"):
                    await websocket.send_text(json.dumps({
                        "type": "voice_call_ready",
                        "message": "Ready to schedule your voice call!"
                    }))
                
                # Check if session is complete
                if state.get("session_complete"):
                    await finalize_session(session_id)
                    await websocket.send_text(json.dumps({
                        "type": "session_complete",
                        "message": "Onboarding completed successfully!"
                    }))
                    break
            
            elif message_data["type"] == "request_voice_call":
                phone_number = message_data.get("phone")
                if phone_number:
                    call_sid = await voice_handler.initiate_call(phone_number, session_id)
                    if call_sid:
                        await websocket.send_text(json.dumps({
                            "type": "voice_call_initiated",
                            "call_id": call_sid
                        }))
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Failed to initiate voice call"
                        }))
    
    except WebSocketDisconnect:
        # Save session data when client disconnects
        await finalize_session(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_text(json.dumps({"error": str(e)}))

async def finalize_session(session_id: str):
    """Finalize session and save to database"""
    session = get_session(session_id)
    if session:
        memory, graph = session
        
        # Save messages to PostgreSQL
        await memory.save_to_postgres()
        
        # Update session status
        async with AsyncSession() as db:
            result = await db.execute(
                select(OnboardingSession).where(OnboardingSession.session_id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                session.status = "completed"
                session.completed_at = datetime.utcnow()
                await db.commit()
        
        # Remove from active sessions
        redis_client.delete(f"session:{session_id}")

@router.post("/voice/handle/{session_id}")
async def handle_voice_call(session_id: str):
    """Handle incoming voice call"""
    message = "Hello! Thank you for joining the onboarding call. Let's verify your information and complete your setup."
    return voice_handler.generate_twiml_response(message)

@router.post("/voice/process_speech")
async def process_speech():
    """Process speech input from voice call"""
    # This would handle the speech processing
    # Implementation depends on your specific requirements
    response_message = "Thank you for that information. Let me process that for you."
    return voice_handler.generate_twiml_response(response_message)

@router.get("/session/{session_id}/status")
async def get_session_status(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get session status"""
    session = db.query(OnboardingSession).filter(OnboardingSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "status": session.status,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
        "voice_call_completed": session.voice_call_completed
    }
