from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AIModel, AIOperation, AICallback
from .serializers import (
    AIModelSerializer, AIOperationSerializer, AICallbackSerializer,
    TranscriptionRequestSerializer, AnalysisRequestSerializer,
    SummarizationRequestSerializer, ImageGenerationRequestSerializer,
    ImageEditingRequestSerializer, AICallbackRequestSerializer
)
from .services import AIService
import logging

logger = logging.getLogger(__name__)

class AIModelViewSet(viewsets.ModelViewSet):
    """
    API endpoint for AI models
    """
    queryset = AIModel.objects.all()
    serializer_class = AIModelSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

class AIOperationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for AI operations
    """
    serializer_class = AIOperationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return AIOperation.objects.all().order_by('-created_at')
        return AIOperation.objects.filter(user=user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an operation"""
        operation = self.get_object()
        
        # Only the owner or staff can cancel operations
        if operation.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only pending or processing operations can be cancelled
        if operation.status not in ['pending', 'processing']:
            return Response(
                {'error': f'Cannot cancel operation with status: {operation.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update operation status
        operation.status = 'cancelled'
        operation.save()
        
        # Refund credits
        from common.apps.credits.services import CreditService
        CreditService.refund_credits(operation.id)
        
        return Response({'status': 'cancelled', 'message': 'Operation cancelled successfully'})

class TranscriptionViewSet(viewsets.ViewSet):
    """
    API endpoint for audio transcription
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request):
        """Transcribe audio"""
        serializer = TranscriptionRequestSerializer(data=request.data)
        if serializer.is_valid():
            audio_url = serializer.validated_data['audio_url']
            analyze = serializer.validated_data.get('analyze', False)
            
            success, result, message = AIService.transcribe_audio(
                user=request.user,
                audio_url=audio_url,
                analyze=analyze
            )
            
            if success:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AnalysisViewSet(viewsets.ViewSet):
    """
    API endpoint for transcript analysis
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request):
        """Analyze transcript"""
        serializer = AnalysisRequestSerializer(data=request.data)
        if serializer.is_valid():
            transcript = serializer.validated_data['transcript']
            
            success, result, message = AIService.analyze_transcript(
                user=request.user,
                transcript=transcript
            )
            
            if success:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SummarizationViewSet(viewsets.ViewSet):
    """
    API endpoint for text summarization
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request):
        """Summarize text"""
        serializer = SummarizationRequestSerializer(data=request.data)
        if serializer.is_valid():
            text = serializer.validated_data['text']
            max_length = serializer.validated_data.get('max_length', 150)
            min_length = serializer.validated_data.get('min_length', 40)
            
            success, result, message = AIService.summarize_text(
                user=request.user,
                text=text,
                max_length=max_length,
                min_length=min_length
            )
            
            if success:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ImageGenerationViewSet(viewsets.ViewSet):
    """
    API endpoint for image generation
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request):
        """Generate images"""
        serializer = ImageGenerationRequestSerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data['prompt']
            num_images = serializer.validated_data.get('num_images', 1)
            size = serializer.validated_data.get('size', "1024x1024")
            
            success, result, message = AIService.generate_image(
                user=request.user,
                prompt=prompt,
                num_images=num_images,
                size=size
            )
            
            if success:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AICallbackViewSet(viewsets.ModelViewSet):
    """
    API endpoint for AI callbacks
    """
    queryset = AICallback.objects.all().order_by('-created_at')
    serializer_class = AICallbackSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def webhook(self, request):
        """Webhook for external AI service callbacks"""
        serializer = AICallbackRequestSerializer(data=request.data)
        if serializer.is_valid():
            success, message = AIService.handle_callback(serializer.validated_data)
            
            if success:
                return Response({'message': message}, status=status.HTTP_200_OK)
            else:
                return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
