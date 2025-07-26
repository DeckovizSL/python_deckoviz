import time
import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse, Response as FastAPIResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import httpx
import logging
from urllib.parse import urlparse
from utils.token import decode_token

logger = logging.getLogger(__name__)


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track AI feature usage and integrate with Django backend"""
    
    def __init__(self, app, django_backend_url: str = "http://localhost:8000"):
        super().__init__(app)
        self.django_backend_url = django_backend_url.rstrip('/')
        self.feature_mapping = self._create_feature_mapping()
        self.timeout_mapping = self._create_timeout_mapping()
    
    def _create_timeout_mapping(self) -> Dict[str, float]:
        """Map feature names to appropriate timeout values"""
        return {
            # Video generation features need longer timeouts
            'image_to_video': 120.0,
            'runware_image_to_video': 120.0,
            'runware_text_to_video': 120.0,
            
            # Complex AI processing features
            'style_transfer': 60.0,
            'replicate_style_transfer': 60.0,
            'replicate_iconic_art': 60.0,
            'runware_flux_tools': 60.0,
            'reimagine_art': 60.0,
            'dream_visualizer': 60.0,
            'text_visualization': 60.0,
            'story_visualizer': 60.0,
            
            # Image generation features
            'personal_painter': 45.0,
            'brand_asset': 45.0,
            'poster': 45.0,
            'image_meta_gen': 45.0,
            'book_to_frames': 45.0,
            'moodboard': 45.0,
            'mindscape': 45.0,
            
            # Chat and lighter features
            'painter_chat': 30.0,
            'dream_visualizer_chat': 30.0,
            'vizzy': 30.0,
            'storyboard': 30.0,
            'visual_journal': 30.0,
            
            # Fast processing features
            'embedding': 30.0,
            'audio_processing': 30.0,
            'onboard': 30.0,
        }
    
    def _get_timeout_for_feature(self, feature_name: str) -> float:
        """Get appropriate timeout for a specific feature"""
        return self.timeout_mapping.get(feature_name, 30.0)  # Default 30 seconds
    
    def _create_feature_mapping(self) -> Dict[str, str]:
        """Map API endpoints to feature names"""
        return {
            '/style_transfer/': 'style_transfer',
            '/generate_art/': 'personal_painter',
            '/onboard/': 'onboard',
            '/painter_chat/': 'painter_chat',
            '/embedding/': 'embedding',
            '/moodboard/': 'moodboard',
            '/poster/': 'poster',
            '/mindscape/': 'mindscape',
            '/image/': 'personal_painter',
            '/dream-visualizer/': 'dream_visualizer',
            '/brand-asset/': 'brand_asset',
            '/image-meta-gen/': 'image_meta_gen',
            '/book_to_frames/': 'book_to_frames',
            '/dream-visualizer-chat/': 'dream_visualizer_chat',
            '/audio/': 'audio_processing',
            '/vizzy/': 'vizzy',
            '/replicate_style_transfer/': 'replicate_style_transfer',
            '/replicate_iconic_art/': 'replicate_iconic_art',
            '/image-to-video/': 'image_to_video',
            '/visual-journal/': 'visual_journal',
            '/runware-image-to-video/': 'runware_image_to_video',
            '/story-visualizer/': 'story_visualizer',
            '/runware-flux-tools/': 'runware_flux_tools',
            '/reimagine-art/': 'reimagine_art',
            '/runware-text-to-video/': 'runware_text_to_video',
            '/text-visualization/': 'text_visualization',
            '/storyboards/': 'storyboard',
        }
    
    def _get_feature_name(self, path: str) -> Optional[str]:
        """Extract feature name from request path"""
        for endpoint, feature in self.feature_mapping.items():
            if path.startswith(endpoint):
                return feature
        return None
    
    def _extract_session_id(self, request: Request) -> Optional[str]:
        """Extract session ID from request (path, headers, or query params)"""
        # Check path for session ID patterns
        path_parts = request.url.path.split('/')
        for i, part in enumerate(path_parts):
            if part in ['session', 'sessions'] and i + 1 < len(path_parts):
                return path_parts[i + 1]
        
        # Check headers
        session_id = request.headers.get('X-Session-ID')
        if session_id:
            return session_id
        
        # Check query parameters
        return request.query_params.get('session_id')
    
    def _should_track_request(self, path: str, method: str) -> bool:
        """Determine if this request should be tracked"""
        # Skip health checks and non-AI endpoints
        skip_paths = ['/', '/docs', '/openapi.json', '/redoc', '/health']
        if path in skip_paths:
            return False
        
        # Only track POST requests for AI features (and some GETs for sessions)
        if method not in ['POST', 'GET']:
            return False
        
        # Must match a known AI feature
        return self._get_feature_name(path) is not None
    
    async def _extract_request_data(self, request: Request) -> Dict[str, Any]:
        """Safely extract request data for logging"""
        try:
            # Get basic request info
            data = {
                'method': request.method,
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'headers': dict(request.headers),
                'content_type': request.headers.get('content-type', ''),
            }
            
            # For POST requests, try to get body data
            if request.method == 'POST':
                content_type = request.headers.get('content-type', '').lower()
                
                if 'application/json' in content_type:
                    # Create a new request with the same body for processing
                    body = await request.body()
                    if body:
                        try:
                            json_data = json.loads(body.decode('utf-8'))
                            # Remove sensitive data but keep structure
                            data['body'] = self._sanitize_request_body(json_data)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            data['body'] = {'_note': 'Unable to parse JSON body'}
                
                elif 'multipart/form-data' in content_type:
                    data['body'] = {'_note': 'Multipart form data - not logged for privacy'}
                
                elif 'application/x-www-form-urlencoded' in content_type:
                    data['body'] = {'_note': 'Form data - not logged for privacy'}
            
            return data
            
        except Exception as e:
            logger.warning(f"Error extracting request data: {str(e)}")
            return {'error': 'Unable to extract request data'}
    
    def _sanitize_response_body(self, data: Any) -> Any:
        """Remove sensitive information from response body"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Keep most response data but sanitize large base64 content
                if key.lower() in ['imagebase64data', 'image_base64', 'base64']:
                    if isinstance(value, str) and len(value) > 100:
                        sanitized[key] = f'[BASE64_DATA_{len(value)}_CHARS]'
                    else:
                        sanitized[key] = value
                elif isinstance(value, str) and len(value) > 5000:
                    sanitized[key] = f'[LARGE_TEXT_{len(value)}_CHARS]'
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self._sanitize_response_body(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_response_body(item) for item in data[:20]]  # Limit list size
        else:
            return data

    def _sanitize_request_body(self, data: Any) -> Any:
        """Remove sensitive information from request body"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Skip binary data, passwords, tokens, etc.
                if key.lower() in ['password', 'token', 'api_key', 'secret', 'image_base64']:
                    sanitized[key] = '[REDACTED]'
                elif isinstance(value, str) and len(value) > 1000:
                    sanitized[key] = f'[LARGE_TEXT_{len(value)}_CHARS]'
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self._sanitize_request_body(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_request_body(item) for item in data[:10]]  # Limit list size
        else:
            return data
    
    async def _start_usage_tracking(
        self,
        user_id: str,
        feature_name: str,
        request_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Optional[str]:
        """Start usage tracking via Django backend"""
        timeout_duration = self._get_timeout_for_feature(feature_name)
        try:
            async with httpx.AsyncClient(timeout=timeout_duration) as client:
                # Extract IP address with fallbacks
                ip_address = request_data.get('headers', {}).get('x-forwarded-for', '').split(',')[0].strip()
                if not ip_address:
                    ip_address = request_data.get('headers', {}).get('x-real-ip', '').strip()
                if not ip_address:
                    ip_address = '127.0.0.1'  # Default for local development
                
                payload = {
                    'user_id': user_id,
                    'feature_name': feature_name,
                    'input_data': request_data,
                    'session_id': session_id,
                    'endpoint_path': request_data.get('path', ''),
                    'user_agent': request_data.get('headers', {}).get('user-agent', ''),
                    'ip_address': ip_address
                }
                
                response = await client.post(
                    f"{self.django_backend_url}/api/analytics/internal/start-usage/",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        logger.info(f"Usage tracking started successfully for user {user_id}, feature {feature_name}")
                        return result.get('usage_id')
                    else:
                        logger.warning(f"Usage tracking failed: {result.get('message')}")
                        return None
                else:
                    logger.warning(f"Usage tracking API error: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.warning(f"Usage tracking timeout - Django backend not reachable at {self.django_backend_url}")
            return None
        except Exception as e:
            logger.warning(f"Usage tracking error: {str(e)} - proceeding without tracking")
            return None
    
    async def _complete_usage_tracking(
        self,
        usage_id: str,
        response_data: Dict[str, Any],
        processing_time: float,
        status: str = 'completed',
        response_body: Dict[str, Any] = None
    ):
        """Complete usage tracking via Django backend"""
        try:
            # Use a longer timeout for completion since it includes response data
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    'usage_id': usage_id,
                    'output_data': response_data,  # Metadata about the response
                    'response_body': response_body,  # Actual API response content
                    'processing_time': processing_time,
                    'status': status
                }
                
                response = await client.post(
                    f"{self.django_backend_url}/api/analytics/internal/complete-usage/",
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Usage tracking completed successfully: usage_id={usage_id}")
                else:
                    logger.warning(f"Failed to complete usage tracking: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error completing usage tracking: {str(e)}")
    
    async def _fail_usage_tracking(
        self,
        usage_id: str,
        error_message: str,
        error_code: str = 'API_ERROR'
    ):
        """Mark usage as failed via Django backend"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    'usage_id': usage_id,
                    'error_message': error_message,
                    'error_code': error_code,
                    'refund_credits': True
                }
                
                await client.post(
                    f"{self.django_backend_url}/api/analytics/internal/fail-usage/",
                    json=payload,
                    timeout=30.0
                )
                
        except Exception as e:
            logger.error(f"Error failing usage tracking: {str(e)}")
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from JWT token in Authorization header"""
        try:
            auth_header = request.headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove 'Bearer ' prefix
                try:
                    payload = decode_token(token)
                    # Get user_id from token payload
                    user_id = payload.get("sub") or payload.get("user_id") or payload.get("id")
                    if user_id:
                        return str(user_id)
                except Exception as e:
                    logger.warning(f"Error decoding JWT token: {str(e)}")
                    return None
            
            # Fallback: check for X-User-ID header (for testing)
            return request.headers.get('X-User-ID')
            
        except Exception as e:
            logger.warning(f"Error extracting user ID: {str(e)}")
            return None
    
    async def dispatch(self, request: Request, call_next):
        """Main middleware logic"""
        start_time = time.time()
        path = request.url.path
        method = request.method
        
        # Check if we should track this request
        if not self._should_track_request(path, method):
            return await call_next(request)
        
        # Extract user information
        user_id = self._extract_user_id(request)
        if not user_id:
            # If no user ID, still process but don't track
            return await call_next(request)
        
        # Get feature name and session info
        feature_name = self._get_feature_name(path)
        session_id = self._extract_session_id(request)
        
        # Extract request data
        request_data = await self._extract_request_data(request)
        
        # Start usage tracking
        usage_id = await self._start_usage_tracking(
            user_id=user_id,
            feature_name=feature_name,
            request_data=request_data,
            session_id=session_id
        )
        
        # If usage tracking failed (e.g., insufficient credits), return error
        if usage_id is None and method == 'POST':
            return JSONResponse(
                status_code=402,
                content={
                    "error": "Insufficient credits or unable to process request",
                    "code": "PAYMENT_REQUIRED"
                }
            )
        
        try:
            # Process the request
            response = await call_next(request)
            processing_time = time.time() - start_time
            
            # Extract basic response metadata
            response_data = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'processing_time': processing_time
            }
            
            # Capture actual response content for successful JSON responses
            actual_response_content = None
            if (response.status_code < 400 and 
                response.headers.get('content-type', '').startswith('application/json')):
                try:
                    # Get the response body
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk
                    
                    # Parse JSON content
                    if body:
                        actual_response_content = json.loads(body.decode('utf-8'))
                        # Sanitize the response content
                        response_data['api_response'] = self._sanitize_response_body(actual_response_content)
                    
                    # Create new response with the same body
                    response = StarletteResponse(
                        content=body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.headers.get('content-type')
                    )
                except Exception as e:
                    logger.warning(f"Error capturing response body: {str(e)}")
                    response_data['api_response'] = {'_error': f'Unable to capture response: {str(e)}'}
            
            # For now, we'll capture detailed response content in a future iteration
            # The current approach focuses on ensuring the middleware doesn't break the response flow
            
            # Complete usage tracking
            if usage_id:
                status = 'completed' if response.status_code < 400 else 'failed'
                
                # Prepare output_data with metadata only
                output_data = {
                    'status_code': response_data['status_code'],
                    'headers': response_data['headers'],
                    'processing_time': processing_time
                }
                
                # Extract actual API response for response_body (don't duplicate in output_data)
                response_body = None
                if 'api_response' in response_data:
                    response_body = response_data['api_response']
                    # Don't add api_response to output_data to avoid duplication
                
                # Run completion tracking in background
                asyncio.create_task(
                    self._complete_usage_tracking(
                        usage_id=usage_id,
                        response_data=output_data,
                        processing_time=processing_time,
                        status=status,
                        response_body=response_body
                    )
                )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Fail usage tracking
            if usage_id:
                asyncio.create_task(
                    self._fail_usage_tracking(
                        usage_id=usage_id,
                        error_message=str(e),
                        error_code='PROCESSING_ERROR'
                    )
                )
            
            # Re-raise the exception
            raise e


def add_usage_tracking_middleware(app, django_backend_url: str = "http://localhost:8000"):
    """Add usage tracking middleware to FastAPI app"""
    app.add_middleware(UsageTrackingMiddleware, django_backend_url=django_backend_url)
