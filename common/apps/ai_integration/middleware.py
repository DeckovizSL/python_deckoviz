from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from common.apps.credits.services import CreditService
from .services import AIService
import logging
import json
import uuid

logger = logging.getLogger(__name__)

class AIOperationMiddleware(MiddlewareMixin):
    """
    Middleware to check and deduct credits for AI operations
    This can be used to intercept AI-related requests and handle credit deduction
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        # Required by Django middleware contract
        self.async_mode = False
        # AI operation endpoints that require credits
        self.ai_endpoints = {
            '/api/ai/transcribe/': {'operation_type': 'transcription', 'unit_field': 'duration_seconds'},
            '/api/ai/analyze/': {'operation_type': 'analysis', 'unit_field': None},
            '/api/ai/summarize/': {'operation_type': 'summarization', 'unit_field': 'text_length'},
            '/api/ai/generate-image/': {'operation_type': 'image_generation', 'unit_field': 'num_images'},
            '/api/ai/edit-image/': {'operation_type': 'image_editing', 'unit_field': None},
        }
    
    def process_request(self, request):
        """Process incoming requests to check for AI operations"""
        # Skip for non-authenticated users or non-AI endpoints
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
            
        path = request.path
        if path not in self.ai_endpoints:
            return None
            
        # Only process POST requests for AI operations
        if request.method != 'POST':
            return None
            
        try:
            # Get operation details
            operation_info = self.ai_endpoints[path]
            operation_type = operation_info['operation_type']
            unit_field = operation_info['unit_field']
            
            # Parse request body to get units if applicable
            try:
                body = json.loads(request.body)
                units = 1  # Default to 1 unit
                
                if unit_field and unit_field in body:
                    # Calculate units based on the field value
                    if unit_field == 'duration_seconds':
                        # For audio, charge per minute (rounded up)
                        duration = int(body[unit_field])
                        units = max(1, (duration + 59) // 60)  # Round up to nearest minute
                    elif unit_field == 'text_length':
                        # For text, charge per 1000 characters
                        text_length = len(body.get('text', ''))
                        units = max(1, (text_length + 999) // 1000)  # Round up to nearest 1000 chars
                    elif unit_field == 'num_images':
                        # For images, charge per image
                        units = max(1, int(body[unit_field]))
            except (json.JSONDecodeError, KeyError, ValueError):
                units = 1  # Default to 1 if we can't parse
                
            # Calculate credit cost
            cost = CreditService.get_operation_cost(operation_type, units)
            
            # Check if user has enough credits
            credit_account = CreditService.get_user_credits(request.user)
            if credit_account.balance < cost:
                return JsonResponse({
                    'error': 'Insufficient credits',
                    'required': cost,
                    'available': credit_account.balance
                }, status=402)  # 402 Payment Required
                
            # Store operation info in request for later use
            request.ai_operation_info = {
                'operation_type': operation_type,
                'units': units,
                'cost': cost,
                'input_data': body if 'body' in locals() else None
            }
            
            # Continue processing the request
            return None
            
        except Exception as e:
            logger.error(f"Error in AICreditMiddleware: {str(e)}")
            # Let the request through in case of errors
            return None
    
    def process_response(self, request, response):
        """Process outgoing responses to handle credit deduction for successful AI operations"""
        # Skip if not an AI operation or no operation info
        if not hasattr(request, 'ai_operation_info'):
            return response
            
        # Only deduct credits for successful responses
        if 200 <= response.status_code < 300:
            try:
                # Get operation info
                operation_info = request.ai_operation_info
                operation_type = operation_info['operation_type']
                cost = operation_info['cost']
                input_data = operation_info['input_data']
                
                # Create AI operation record first
                model = AIService.get_default_model(operation_type)
                
                # Create AI operation
                ai_operation = AIService.create_operation_record(
                    user=request.user,
                    operation_type=operation_type,
                    input_data=input_data,
                    model=model
                )
                
                # Deduct credits and link to AI operation
                success, credit_operation_id, message = CreditService.use_credits(
                    user=request.user,
                    amount=cost,
                    operation_type=operation_type,
                    input_data=input_data,
                    ai_operation_id=ai_operation.id if ai_operation else None
                )
                
                if success:
                    # Try to parse response data
                    try:
                        response_data = json.loads(response.content)
                        
                        # Update AI operation with results
                        if ai_operation:
                            ai_operation.status = 'completed'
                            ai_operation.result_data = response_data
                            ai_operation.credits_used = cost
                            ai_operation.save()
                        
                        # Complete the credit operation with result data
                        CreditService.complete_operation(credit_operation_id, response_data)
                        
                        # Add operation IDs to response
                        response_data['credit_operation_id'] = str(credit_operation_id)
                        if ai_operation:
                            response_data['ai_operation_id'] = str(ai_operation.id)
                        response_data['credits_used'] = cost
                        
                        # Update response content
                        response.content = json.dumps(response_data).encode('utf-8')
                    except json.JSONDecodeError:
                        # If we can't parse the response, just complete the operations
                        CreditService.complete_operation(credit_operation_id)
                        if ai_operation:
                            ai_operation.status = 'completed'
                            ai_operation.credits_used = cost
                            ai_operation.save()
                else:
                    # This shouldn't happen since we checked credits earlier
                    logger.error(f"Failed to deduct credits: {message}")
                    # If we created an AI operation but failed to deduct credits, mark it as failed
                    if ai_operation:
                        ai_operation.status = 'failed'
                        ai_operation.error_message = f"Failed to deduct credits: {message}"
                        ai_operation.save()
            except Exception as e:
                logger.error(f"Error processing AI operation response: {str(e)}")
                
        return response
