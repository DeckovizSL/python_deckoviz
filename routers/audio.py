from genai.assembly_ai import AudioProcessor
from genai.audio_analysis import TranscriptAnalyzer
from fastapi import APIRouter, HTTPException, BackgroundTasks
from schemas.audio import (
    TranscriptionRequest, TranscriptionResponse,
    AnalysisRequest, AnalysisResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize transcript analyzer
transcript_analyzer = TranscriptAnalyzer()

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(request: TranscriptionRequest, background_tasks: BackgroundTasks):
    """Transcribe audio from a URL with optional analysis"""
    try:
        logger.info(f"Transcribing audio from URL: {request.audio_url}")
        processor = AudioProcessor()
        transcript = processor.get_transcript(request.audio_url)
        
        response = {
            "transcript": transcript,
            "status": "completed",
            "id": request.id,
            "audio_file_path": request.audio_url,
            "insights": None
        }
        
        # If analysis is requested, generate insights
        if request.analyze and transcript:
            try:
                insights = transcript_analyzer.generate_insights(transcript)
                response["insights"] = insights
            except Exception as analysis_error:
                logger.error(f"Error analyzing transcript: {str(analysis_error)}")
                # Continue with transcription only
        
        return response
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_transcript(request: AnalysisRequest):
    """Analyze a transcript to generate insights"""
    try:
        if not request.transcript or len(request.transcript.strip()) < 10:
            raise HTTPException(status_code=400, detail="Transcript too short for analysis")
        
        logger.info(f"Analyzing transcript: {request.transcript[:100]}...")
        insights = transcript_analyzer.generate_insights(request.transcript)
        
        return {
            "insights": insights,
            "id": request.id
        }
    except Exception as e:
        logger.error(f"Error analyzing transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize", response_model=dict)
async def summarize_transcript(request: dict):
    """Generate a summary of a transcript"""
    try:
        if not request.get("text") or len(request["text"].strip()) < 50:
            raise HTTPException(status_code=400, detail="Text too short for summarization")
        
        max_length = request.get("max_length", 150)
        min_length = request.get("min_length", 40)
        
        logger.info(f"Summarizing text: {request['text'][:100]}...")
        summary = transcript_analyzer.generate_summary(
            request["text"], max_length=max_length, min_length=min_length
        )
        
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Error summarizing text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
