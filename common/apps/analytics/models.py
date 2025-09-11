from django.db import models
from django.contrib.auth import get_user_model
from common.apps.authentication.models import BaseModel

User = get_user_model()


class FeatureUsage(BaseModel):
    """Comprehensive tracking of AI feature usage"""
    
    FEATURE_CATEGORIES = [
        ('image_generation', 'Image Generation'),
        ('style_transfer', 'Style Transfer'),
        ('image_editing', 'Image Editing'),
        ('video_generation', 'Video Generation'),
        ('text_processing', 'Text Processing'),
        ('chat_ai', 'AI Chat'),
        ('audio_processing', 'Audio Processing'),
        ('visualization', 'Data Visualization'),
        ('creative_tools', 'Creative Tools'),
    ]
    
    AI_FEATURES = [
        # Image Generation & Editing
        ('personal_painter', 'Personal Painter'),
        ('style_transfer', 'Style Transfer'),
        ('dream_visualizer', 'Dream Visualizer'),
        ('image_meta_gen', 'Image Metadata Generation'),
        ('replicate_style_transfer', 'Replicate Style Transfer'),
        ('replicate_iconic_art', 'Replicate Iconic Art'),
        ('reimagine_art', 'Reimagine Art'),
        ('runware_flux_tools', 'Runware FLUX Tools'),
        
        # Video
        ('image_to_video', 'Image to Video'),
        ('runware_image_to_video', 'Runware Image to Video'),
        ('runware_text_to_video', 'Runware Text to Video'),
        
        # Chat & Conversation
        ('painter_chat', 'Painter Chat'),
        ('dream_visualizer_chat', 'Dream Visualizer Chat'),
        ('vizzy', 'Vizzy Voice Assistant'),
        
        # Creative Tools
        ('moodboard', 'Moodboard Creation'),
        ('poster', 'Poster Generation'),
        ('brand_asset', 'Brand Asset Creation'),
        ('mindscape', 'Mindscape'),
        ('book_to_frames', 'Book to Frames'),
        ('visual_journal', 'Visual Journal'),
        ('story_visualizer', 'Story Visualizer'),
        ('text_visualization', 'Text Visualization'),
        
        # Audio
        ('audio_processing', 'Audio Processing'),
        
        # Others
        ('embedding', 'Embedding Generation'),
        ('onboard', 'AI Onboarding'),
        ('storyboard', 'Storyboard Creation'),
    ]
    
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feature_usage')
    feature_name = models.CharField(max_length=50, choices=AI_FEATURES)
    feature_category = models.CharField(max_length=30, choices=FEATURE_CATEGORIES)
    session_id = models.CharField(max_length=255, null=True, blank=True)  # For session-based features
    
    # Usage Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    credits_used = models.PositiveIntegerField(default=0)
    
    # Request/Response Data
    input_data = models.JSONField(null=True, blank=True)  # User inputs (prompts, images, etc.)
    output_data = models.JSONField(null=True, blank=True)  # Generated results metadata
    processing_time = models.FloatField(null=True, blank=True)  # Time in seconds
    
    # Context Information
    endpoint_path = models.CharField(max_length=255, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Error Information
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    
    # Billing Integration
    credit_operation = models.ForeignKey(
        'credits.CreditAIOperation', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='feature_usage_records'
    )
    
    class Meta:
        db_table = 'feature_usage'
        verbose_name = 'Feature Usage'
        verbose_name_plural = 'Feature Usage Records'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['feature_name', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['user', 'feature_name']),
            models.Index(fields=['session_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.feature_name} - {self.status}"


class UserSession(BaseModel):
    """Track user sessions across platforms"""
    
    PLATFORM_CHOICES = [
        ('web', 'Web Application'),
        ('mobile', 'Mobile App'),
        ('api', 'Direct API'),
        ('desktop', 'Desktop App'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_sessions')
    session_id = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='web')
    
    # Session Details
    start_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_info = models.JSONField(null=True, blank=True)
    
    # Usage Statistics
    total_ai_features_used = models.PositiveIntegerField(default=0)
    total_credits_spent = models.PositiveIntegerField(default=0)
    total_requests = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['session_id']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.session_id} - {self.platform}"


class DailyUserStats(BaseModel):
    """Daily aggregated user statistics"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField()
    
    # Usage Counts
    total_ai_requests = models.PositiveIntegerField(default=0)
    unique_features_used = models.PositiveIntegerField(default=0)
    total_credits_spent = models.PositiveIntegerField(default=0)
    total_session_time = models.DurationField(null=True, blank=True)
    
    # Feature Usage Breakdown
    feature_usage_breakdown = models.JSONField(default=dict)  # {feature_name: count}
    category_usage_breakdown = models.JSONField(default=dict)  # {category: count}
    
    # Success/Failure Rates
    successful_requests = models.PositiveIntegerField(default=0)
    failed_requests = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'daily_user_stats'
        verbose_name = 'Daily User Statistics'
        verbose_name_plural = 'Daily User Statistics'
        unique_together = ('user', 'date')
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"


class FeaturePricing(BaseModel):
    """Dynamic pricing for AI features"""
    
    feature_name = models.CharField(max_length=50, choices=FeatureUsage.AI_FEATURES, unique=True)
    base_credits = models.PositiveIntegerField()
    per_unit_credits = models.PositiveIntegerField(default=0)  # Additional cost per unit
    description = models.TextField(blank=True)
    
    # Usage-based pricing
    tier_1_limit = models.PositiveIntegerField(default=0)  # Free tier limit
    tier_1_price = models.PositiveIntegerField(default=0)
    tier_2_price = models.PositiveIntegerField(default=0)
    tier_3_price = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'feature_pricing'
        verbose_name = 'Feature Pricing'
        verbose_name_plural = 'Feature Pricing'
    
    def calculate_cost(self, usage_count=1, user_tier=1):
        """Calculate cost based on usage and user tier"""
        if user_tier == 1 and usage_count <= self.tier_1_limit:
            return 0  # Free tier
        
        base_cost = self.base_credits
        if user_tier == 2:
            base_cost = self.tier_2_price or base_cost
        elif user_tier == 3:
            base_cost = self.tier_3_price or base_cost
        
        total_cost = base_cost + (self.per_unit_credits * max(0, usage_count - 1))
        return total_cost
    
    def __str__(self):
        return f"{self.feature_name} - {self.base_credits} credits"
