import requests
import time
import uuid
import logging
from django.conf import settings
from django.utils import timezone
from .models import AIModel, AIOperation, AICallback
from common.apps.credits.services import CreditService

logger = logging.getLogger(__name__)

class AIService:
    """
    Service class for AI operations
    Handles interactions with external AI services and integrates with credit system
    """
    
    @staticmethod
    def get_ai_service_url():
        """Get the base URL for the AI service"""
        return settings.DECKOVIZ_AI_URL
    
    @classmethod
    def get_default_model(cls, operation_type):
        """Get the default model for a specific operation type"""
        try:
            return AIModel.objects.filter(
                model_type=operation_type,
                is_active=True
            ).order_by('-created_at').first()
        except Exception as e:
            logger.error(f"Error getting default model for {operation_type}: {str(e)}")
            return None
    
    @classmethod
    def calculate_credits(cls, operation_type, units=1, model=None):
        """
        Calculate the credits required for an operation
        
        Args:
            operation_type: Type of AI operation
            units: Number of units (e.g., minutes of audio, number of images)
            model: Optional specific AI model that might have different pricing
            
        Returns:
            int: Number of credits required
        """
        # Use the credit service to get the cost based on operation type and units
        return CreditService.get_operation_cost(operation_type, units)
    
    @classmethod
    def create_operation_record(cls, user, operation_type, input_data=None, model=None):
        """
        Create an AI operation record without handling credits
        
        Args:
            user: The user requesting the operation
            operation_type: Type of AI operation
            input_data: Input data for the operation
            model: Optional specific AI model to use
            
        Returns:
            AIOperation: The created operation record or None if failed
        """
        try:
            # Get default model if not specified
            if not model:
                model = cls.get_default_model(operation_type)
            
            # Create AI operation record
            operation = AIOperation.objects.create(
                user=user,
                operation_type=operation_type,
                model=model,
                status='pending',
                input_data=input_data
            )
            
            return operation
            
        except Exception as e:
            error_msg = f"Error creating AI operation record: {str(e)}"
            logger.error(error_msg)
            return None
    
    @classmethod
    def create_operation(cls, user, operation_type, input_data=None, model=None, units=1):
        """
        Create an AI operation and handle credit deduction
        
        Args:
            user: The user requesting the operation
            operation_type: Type of AI operation
            input_data: Input data for the operation
            model: Optional specific AI model to use
            units: Number of units for credit calculation
            
        Returns:
            tuple: (success, operation, message)
        """
        try:
            # Get default model if not specified
            if not model:
                model = cls.get_default_model(operation_type)
            
            # Calculate required credits
            credits_required = cls.calculate_credits(operation_type, units, model)
            
            # Create AI operation record first
            operation = cls.create_operation_record(
                user=user,
                operation_type=operation_type,
                input_data=input_data,
                model=model
            )
            
            if not operation:
                return False, None, "Failed to create operation record"
            
            # Use credit service to deduct credits
            success, credit_operation_id, message = CreditService.use_credits(
                user=user,
                amount=credits_required,
                operation_type=operation_type,
                input_data=input_data,
                operation_id=operation.id
            )
            
            if not success:
                # If credit deduction fails, mark the operation as failed
                operation.status = 'failed'
                operation.error_message = message
                operation.save()
                return False, None, message
            
            # Update operation with credit info
            operation.credits_used = credits_required
            operation.save()
            
            return True, operation, "Operation created successfully"
            
        except Exception as e:
            error_msg = f"Error creating AI operation: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    @classmethod
    def process_operation(cls, operation):
        """
        Process an AI operation by calling the appropriate service
        
        Args:
            operation: The AIOperation object to process
            
        Returns:
            tuple: (success, result, message)
        """
        try:
            # Update status to processing
            operation.status = 'processing'
            operation.save()
            
            start_time = time.time()
            
            # Call the appropriate method based on operation type
            if operation.operation_type == 'transcription':
                success, result, message = cls._process_transcription(operation)
            elif operation.operation_type == 'analysis':
                success, result, message = cls._process_analysis(operation)
            elif operation.operation_type == 'summarization':
                success, result, message = cls._process_summarization(operation)
            elif operation.operation_type == 'image_generation':
                success, result, message = cls._process_image_generation(operation)
            elif operation.operation_type == 'image_editing':
                success, result, message = cls._process_image_editing(operation)
            else:
                success, result, message = False, None, f"Unsupported operation type: {operation.operation_type}"
            
            # Calculate processing time
            processing_time = time.time() - start_time
            operation.processing_time = processing_time
            
            if success:
                # Update operation with results
                operation.status = 'completed'
                operation.result_data = result
                operation.save()
                
                return True, result, message
            else:
                # Mark operation as failed and refund credits
                operation.status = 'failed'
                operation.error_message = message
                operation.save()
                
                # Refund credits
                CreditService.refund_credits(operation.id)
                
                return False, None, message
                
        except Exception as e:
            error_msg = f"Error processing AI operation: {str(e)}"
            logger.error(error_msg)
            
            # Mark operation as failed and refund credits
            operation.status = 'failed'
            operation.error_message = error_msg
            operation.save()
            
            # Refund credits
            CreditService.refund_credits(operation.id)
            
            return False, None, error_msg
    
    @classmethod
    def _process_transcription(cls, operation):
        """Process audio transcription operation"""
        try:
            input_data = operation.input_data or {}
            audio_url = input_data.get('audio_url')
            
            if not audio_url:
                return False, None, "Missing audio URL"
            
            # Call AI service
            request_id = str(uuid.uuid4())
            url = f"{cls.get_ai_service_url()}/audio/transcribe"
            payload = {
                "audio_url": audio_url,
                "analyze": input_data.get('analyze', False),
                "id": request_id
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                operation.external_id = result.get('id', request_id)
                return True, result, "Transcription successful"
            else:
                error_msg = f"AI service error: {response.status_code} - {response.text}"
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Error processing transcription: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    @classmethod
    def _process_analysis(cls, operation):
        """Process transcript analysis operation"""
        try:
            input_data = operation.input_data or {}
            transcript = input_data.get('transcript')
            
            if not transcript:
                return False, None, "Missing transcript"
            
            # Call AI service
            request_id = str(uuid.uuid4())
            url = f"{cls.get_ai_service_url()}/audio/analyze"
            payload = {
                "transcript": transcript,
                "id": request_id
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                operation.external_id = result.get('id', request_id)
                return True, result, "Analysis successful"
            else:
                error_msg = f"AI service error: {response.status_code} - {response.text}"
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Error processing analysis: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    @classmethod
    def _process_summarization(cls, operation):
        """Process text summarization operation"""
        try:
            input_data = operation.input_data or {}
            text = input_data.get('text')
            
            if not text:
                return False, None, "Missing text"
            
            max_length = input_data.get('max_length', 150)
            min_length = input_data.get('min_length', 40)
            
            # Call AI service
            url = f"{cls.get_ai_service_url()}/audio/summarize"
            payload = {
                "text": text,
                "max_length": max_length,
                "min_length": min_length
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return True, result, "Summarization successful"
            else:
                error_msg = f"AI service error: {response.status_code} - {response.text}"
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Error processing summarization: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    @classmethod
    def _process_image_generation(cls, operation):
        """Process image generation operation"""
        try:
            input_data = operation.input_data or {}
            prompt = input_data.get('prompt')
            
            if not prompt:
                return False, None, "Missing prompt"
            
            num_images = input_data.get('num_images', 1)
            size = input_data.get('size', "1024x1024")
            
            # This is a placeholder - in a real implementation, you would make the actual API call
            # url = f"{cls.get_ai_service_url()}/image/generate"
            # payload = {
            #     "prompt": prompt,
            #     "num_images": num_images,
            #     "size": size
            # }
            # response = requests.post(url, json=payload)
            
            # For now, simulate a successful response
            result = {
                "images": [f"https://example.com/generated_image_{i}.jpg" for i in range(num_images)],
                "prompt": prompt
            }
            
            return True, result, "Image generation successful"
                
        except Exception as e:
            error_msg = f"Error processing image generation: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    @classmethod
    def _process_image_editing(cls, operation):
        """Process image editing operation"""
        try:
            input_data = operation.input_data or {}
            image_url = input_data.get('image_url')
            prompt = input_data.get('prompt')
            
            if not image_url or not prompt:
                return False, None, "Missing image URL or prompt"
            
            # This is a placeholder - in a real implementation, you would make the actual API call
            # url = f"{cls.get_ai_service_url()}/image/edit"
            # payload = {
            #     "image_url": image_url,
            #     "prompt": prompt
            # }
            # response = requests.post(url, json=payload)
            
            # For now, simulate a successful response
            result = {
                "edited_image": "https://example.com/edited_image.jpg",
                "original_image": image_url,
                "prompt": prompt
            }
            
            return True, result, "Image editing successful"
                
        except Exception as e:
            error_msg = f"Error processing image editing: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    @classmethod
    def handle_callback(cls, callback_data):
        """
        Handle callbacks from asynchronous AI operations
        
        Args:
            callback_data: Data from the callback
            
        Returns:
            tuple: (success, message)
        """
        try:
            operation_id = callback_data.get('operation_id')
            external_id = callback_data.get('id')
            status = callback_data.get('status')
            
            if not operation_id and not external_id:
                return False, "Missing operation ID or external ID"
            
            # Find the operation
            if operation_id:
                try:
                    operation = AIOperation.objects.get(id=operation_id)
                except AIOperation.DoesNotExist:
                    return False, f"Operation not found with ID: {operation_id}"
            else:
                try:
                    operation = AIOperation.objects.get(external_id=external_id)
                except AIOperation.DoesNotExist:
                    return False, f"Operation not found with external ID: {external_id}"
            
            # Create callback record
            AICallback.objects.create(
                operation=operation,
                callback_data=callback_data,
                processed=False
            )
            
            # Update operation based on callback
            if status == 'completed':
                operation.status = 'completed'
                operation.result_data = callback_data.get('result')
                operation.save()
                return True, "Callback processed successfully"
            elif status == 'failed':
                operation.status = 'failed'
                operation.error_message = callback_data.get('error', 'Operation failed')
                operation.save()
                
                # Refund credits
                CreditService.refund_credits(operation.id)
                
                return True, "Callback processed successfully - operation failed"
            else:
                # Just update the operation with the callback data
                operation.save()
                return True, "Callback recorded"
                
        except Exception as e:
            error_msg = f"Error handling callback: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    # Convenience methods for common operations
    
    @classmethod
    def transcribe_audio(cls, user, audio_url, analyze=False):
        """
        Transcribe audio with credit tracking
        
        Args:
            user: The user requesting the transcription
            audio_url: URL of the audio file to transcribe
            analyze: Whether to also analyze the transcript
            
        Returns:
            tuple: (success, result, message)
        """
        # Estimate audio length - in a real implementation, you might 
        # want to get the actual duration from the file metadata
        estimated_minutes = 5  # Default to 5 minutes if unknown
        
        # Create operation
        success, operation, message = cls.create_operation(
            user=user,
            operation_type='transcription',
            input_data={'audio_url': audio_url, 'analyze': analyze},
            units=estimated_minutes
        )
        
        if not success:
            return False, None, message
        
        # Process operation
        return cls.process_operation(operation)
    
    @classmethod
    def analyze_transcript(cls, user, transcript):
        """
        Analyze a transcript with credit tracking
        
        Args:
            user: The user requesting the analysis
            transcript: The transcript text to analyze
            
        Returns:
            tuple: (success, result, message)
        """
        # Create operation
        success, operation, message = cls.create_operation(
            user=user,
            operation_type='analysis',
            input_data={'transcript': transcript}
        )
        
        if not success:
            return False, None, message
        
        # Process operation
        return cls.process_operation(operation)
    
    @classmethod
    def summarize_text(cls, user, text, max_length=150, min_length=40):
        """
        Summarize text with credit tracking
        
        Args:
            user: The user requesting the summarization
            text: The text to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            
        Returns:
            tuple: (success, result, message)
        """
        # Calculate units based on text length (per 1000 chars)
        text_length = len(text)
        units = max(1, (text_length + 999) // 1000)
        
        # Create operation
        success, operation, message = cls.create_operation(
            user=user,
            operation_type='summarization',
            input_data={
                'text': text,
                'max_length': max_length,
                'min_length': min_length,
                'text_length': text_length
            },
            units=units
        )
        
        if not success:
            return False, None, message
        
        # Process operation
        return cls.process_operation(operation)
    
    @classmethod
    def generate_image(cls, user, prompt, num_images=1, size="1024x1024"):
        """
        Generate images with credit tracking
        
        Args:
            user: The user requesting image generation
            prompt: The text prompt for image generation
            num_images: Number of images to generate
            size: Size of the images
            
        Returns:
            tuple: (success, result, message)
        """
        # Create operation
        success, operation, message = cls.create_operation(
            user=user,
            operation_type='image_generation',
            input_data={
                'prompt': prompt,
                'num_images': num_images,
                'size': size
            },
            units=num_images
        )
        
        if not success:
            return False, None, message
        
        # Process operation
        return cls.process_operation(operation)
