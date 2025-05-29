from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class TranscriptionRequest(BaseModel):
    audio_url: str
    id: Optional[str] = None
    analyze: bool = False

class TranscriptionResponse(BaseModel):
    transcript: str
    status: str
    id: Optional[str] = None
    audio_file_path: Optional[str] = None
    insights: Optional[Dict[str, Any]] = None

class SentimentAnalysis(BaseModel):
    sentiment: str
    score: float

class TranscriptInsights(BaseModel):
    summary: str = Field(..., description="A concise summary of the transcript")
    sentiment: SentimentAnalysis = Field(..., description="Sentiment analysis of the transcript")
    topics: List[str] = Field(default_factory=list, description="Key topics extracted from the transcript")
    word_count: int = Field(..., description="Number of words in the transcript")

class AnalysisRequest(BaseModel):
    transcript: str
    id: Optional[str] = None

class AnalysisResponse(BaseModel):
    insights: TranscriptInsights
    id: Optional[str] = None
