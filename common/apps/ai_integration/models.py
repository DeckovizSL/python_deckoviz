from django.db import models
from common.apps.authentication.models import User, BaseModel

class AIModel(BaseModel):
    """AI models available for different operations"""
    MODEL_TYPES = [
        ('transcription', 'Transcription'),
        ('analysis', 'Analysis'),
        ('summarization', 'Summarization'),
        ('image_generation', 'Image Generation'),
        ('image_editing', 'Image Editing'),
    ]
    
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=30, choices=MODEL_TYPES)
    provider = models.CharField(max_length=100)  # e.g., OpenAI, AssemblyAI, etc.
    model_id = models.CharField(max_length=100)  # Provider-specific model ID
    version = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)  # Model-specific configuration
    
    def __str__(self):
        return f"{self.name} ({self.provider})"
    
    class Meta:
        db_table = 'ai_models'
        verbose_name = 'AI Model'
        verbose_name_plural = 'AI Models'
        indexes = [
            models.Index(fields=['model_type']),
            models.Index(fields=['provider']),
            models.Index(fields=['is_active']),
        ]

class AIOperation(BaseModel):
    """Record of AI operations performed"""
    OPERATION_TYPES = [
        ('transcription', 'Audio Transcription'),
        ('analysis', 'Transcript Analysis'),
        ('summarization', 'Text Summarization'),
        ('image_generation', 'Image Generation'),
        ('image_editing', 'Image Editing'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_operations')
    operation_type = models.CharField(max_length=30, choices=OPERATION_TYPES)
    model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    input_data = models.JSONField(null=True, blank=True)  # Store input parameters
    result_data = models.JSONField(null=True, blank=True)  # Store operation results
    error_message = models.TextField(blank=True)
    credits_used = models.PositiveIntegerField(default=0)
    processing_time = models.FloatField(null=True, blank=True)  # Time taken in seconds
    external_id = models.CharField(max_length=255, blank=True)  # ID from external service
    
    def __str__(self):
        return f"{self.user.username} - {self.operation_type} - {self.status}"
    
    class Meta:
        db_table = 'ai_operations'
        verbose_name = 'AI Operation'
        verbose_name_plural = 'AI Operations'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['operation_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

class AICallback(BaseModel):
    """Callbacks from asynchronous AI operations"""
    operation = models.ForeignKey(AIOperation, on_delete=models.CASCADE, related_name='callbacks')
    callback_data = models.JSONField()
    processed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Callback for {self.operation.operation_type} - {self.operation.id}"
    
    class Meta:
        db_table = 'ai_callbacks'
        verbose_name = 'AI Callback'
        verbose_name_plural = 'AI Callbacks'
        indexes = [
            models.Index(fields=['operation']),
            models.Index(fields=['processed']),
            models.Index(fields=['created_at']),
        ]
