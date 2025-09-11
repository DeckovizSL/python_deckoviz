from celery import shared_task
import json
import logging
from common.apps.gallery.models import Audio
from django.utils import timezone
from common.apps.utils.decoviz_ai import AIClient
from common.apps.utils.storage import Storage
from common.apps.utils.unsplash_client import UnsplashClient
from .models import Image

search_queries=['nature', 'people', 'food', 'travel', 'architecture', 'animals']

logger = logging.getLogger(__name__)


@shared_task
def process_audio():
    """Process audio files for transcription and analysis"""
    logger.info("Fetching audios to process")
    audios = Audio.objects.filter(transcript_status='processing', is_active=True)
    
    if not audios.exists():
        logger.info("No audio files to process")
        return
    
    logger.info(f"Found {audios.count()} audio file(s) to process")
    
    for audio in audios:
        try:
            logger.info(f"Processing audio file: {audio.id}")
            client = AIClient()
            # Request transcription with analysis
            result = client.transcribe_audio(audio.audio.url, analyze=True)
            
            # Upload transcript to GCS
            storage = Storage()
            transcript_url = storage.upload_transcript(result['transcript'], audio.id)
            
            # Update audio model with transcript and metadata
            if result['success']:
                audio.transcript = result['transcript']
                audio.transcript_url = transcript_url
                audio.transcript_status = 'completed'
                
                # Store insights if available
                if 'insights' in result and result['insights']:
                    # Serialize insights to JSON string for storage
                    audio.transcript_insights = json.dumps(result['insights'])
                    
                    # Store summary separately if available
                    if 'summary' in result['insights']:
                        audio.transcript_summary = result['insights']['summary']
                    
                    # Store sentiment if available
                    if 'sentiment' in result['insights']:
                        audio.transcript_sentiment = result['insights']['sentiment']['sentiment']
                
                audio.processed_at = timezone.now()
                audio.save()
                
                logger.info(f"Successfully processed audio {audio.id}")
            else:
                logger.error(f"Failed to transcribe audio: {audio.id}")
                audio.transcript_status = 'failed'
                audio.error_message = result.get('error', 'Unknown error during transcription')
                audio.save()
        except Exception as e:
            logger.error(f"Error processing audio {audio.id}: {str(e)}")
            audio.transcript_status = 'failed'
            audio.error_message = str(e)
            audio.save()


@shared_task
def retry_failed_transcriptions():
    """Retry transcriptions that previously failed"""
    logger.info("Looking for failed transcriptions to retry")
    # Find audios that failed but haven't been retried too many times
    audios = Audio.objects.filter(
        transcript_status='failed',
        is_active=True,
        retry_count__lt=3  # Limit retries to avoid infinite loops
    )
    
    if not audios.exists():
        logger.info("No failed transcriptions to retry")
        return
    
    logger.info(f"Found {audios.count()} failed transcription(s) to retry")
    
    for audio in audios:
        # Increment retry count and set back to processing
        audio.retry_count = (audio.retry_count or 0) + 1
        audio.transcript_status = 'processing'
        audio.save()
        
        logger.info(f"Queued audio {audio.id} for retry (attempt {audio.retry_count})")


@shared_task
def analyze_existing_transcripts():
    """Analyze existing transcripts that don't have insights yet"""
    logger.info("Finding transcripts that need analysis")
    # Find completed transcripts without insights
    audios = Audio.objects.filter(
        transcript_status='completed',
        is_active=True,
        transcript__isnull=False,
        transcript_insights__isnull=True  # No insights yet
    )
    
    if not audios.exists():
        logger.info("No transcripts need analysis")
        return
    
    logger.info(f"Found {audios.count()} transcript(s) that need analysis")
    
    for audio in audios:
        try:
            if not audio.transcript or len(audio.transcript.strip()) < 50:
                logger.warning(f"Transcript for audio {audio.id} is too short for analysis")
                continue
                
            logger.info(f"Analyzing transcript for audio {audio.id}")
            
            # Use AI client to analyze transcript
            client = AIClient()
            result = client.analyze_transcript(audio.transcript)
            
            if result['success'] and 'insights' in result:
                # Store insights
                audio.transcript_insights = json.dumps(result['insights'])
                
                # Store summary separately if available
                if 'summary' in result['insights']:
                    audio.transcript_summary = result['insights']['summary']
                
                # Store sentiment if available
                if 'sentiment' in result['insights']:
                    audio.transcript_sentiment = result['insights']['sentiment']['sentiment']
                
                audio.save()
                logger.info(f"Successfully analyzed transcript for audio {audio.id}")
            else:
                logger.error(f"Failed to analyze transcript for audio {audio.id}")
        except Exception as e:
            logger.error(f"Error analyzing transcript for audio {audio.id}: {str(e)}")



@shared_task
def populate_unsplash_images():
    client = UnsplashClient(search_queries=search_queries)
    logger.info("Fetching unsplash images to process")
    client.run()  



