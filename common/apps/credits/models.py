from django.db import models
from common.apps.authentication.models import User, BaseModel
from django.contrib.postgres.fields import ArrayField   

class CreditPackage(BaseModel):
    """Credit packages that users can purchase"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    features = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    credits = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.credits} credits"
    
    class Meta:
        db_table = 'credit_packages'
        verbose_name = 'Credit Package'
        verbose_name_plural = 'Credit Packages'
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['name']),
        ]

class UserCredit(BaseModel):
    """User's credit balance"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='credit_account')
    balance = models.PositiveIntegerField(default=0)
    lifetime_credits = models.PositiveIntegerField(default=0)  # Total credits ever received
    
    def __str__(self):
        return f"{self.user.username} - {self.balance} credits"
    
    class Meta:
        db_table = 'user_credits'
        verbose_name = 'User Credit'
        verbose_name_plural = 'User Credits'
        indexes = [
            models.Index(fields=['user']),
        ]

class CreditTransaction(BaseModel):
    """Record of all credit transactions"""
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('usage', 'Usage'),
        ('refund', 'Refund'),
        ('bonus', 'Bonus'),
        ('expiry', 'Expiry'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_transactions')
    amount = models.IntegerField()  # Positive for additions, negative for deductions
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    reference_id = models.UUIDField(null=True, blank=True)  # For linking to orders, AI operations, etc.
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount} credits"
    
    class Meta:
        db_table = 'credit_transactions'
        verbose_name = 'Credit Transaction'
        verbose_name_plural = 'Credit Transactions'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['created_at']),
        ]
 

class CreditAIOperation(BaseModel):
    """Record of credits used for AI operations"""
    OPERATION_TYPES = [
        ('transcription', 'Audio Transcription'),
        ('analysis', 'Transcript Analysis'),
        ('summarization', 'Text Summarization'),
        ('image_generation', 'Image Generation'),
        ('image_editing', 'Image Editing'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_ai_operations')
    operation_type = models.CharField(max_length=30, choices=OPERATION_TYPES)
    credits_used = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    input_data = models.JSONField(null=True, blank=True)  # Store input parameters
    result_data = models.JSONField(null=True, blank=True)  # Store operation results
    error_message = models.TextField(blank=True)
    # Reference to the actual AI operation in the ai_integration app
    # This is defined as a string to avoid circular import issues
    operation_id = models.UUIDField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.operation_type} - {self.credits_used} credits"
    
    class Meta:
        db_table = 'credit_ai_operations'
        verbose_name = 'Credit AI Operation'
        verbose_name_plural = 'Credit AI Operations'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['operation_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['operation_id']),
        ]

class CreditPricing(BaseModel):
    """Pricing configuration for different AI operations"""
    operation_type = models.CharField(max_length=30, choices=CreditAIOperation.OPERATION_TYPES, unique=True)
    base_credits = models.PositiveIntegerField()  # Base credit cost
    per_unit_credits = models.PositiveIntegerField(default=0)  # Additional credits per unit (e.g., per minute, per image)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.operation_type} - {self.base_credits} credits"
    
    class Meta:
        db_table = 'credit_pricing'
        verbose_name = 'Credit Pricing'
        verbose_name_plural = 'Credit Pricing'

class PlanFeature(BaseModel):
    """Features available in credit plans"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'plan_features'
        verbose_name = 'Plan Feature'
        verbose_name_plural = 'Plan Features'

class CreditPlan(BaseModel):
    """Subscription plans for credits with features and pricing tiers"""
    PLAN_TYPES = [
        ('starter', 'Starter'),
        ('premium', 'Premium'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    display_price = models.CharField(max_length=20, help_text="Display price like '$299'")
    price_suffix = models.CharField(max_length=20, default="/frame", help_text="Price suffix like '/month' or '/frame'")
    credits = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    tagline = models.CharField(max_length=200, blank=True, help_text="Short description like 'Perfect for your first smart art experience'")
    is_popular = models.BooleanField(default=False)
    is_custom = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0, help_text="Display order of plans")
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'credit_plans'
        verbose_name = 'Credit Plan'
        verbose_name_plural = 'Credit Plans'
        ordering = ['order']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['plan_type']),
            models.Index(fields=['is_popular']),
        ]

class PlanFeatureAssociation(BaseModel):
    """Association between plans and features"""
    plan = models.ForeignKey(CreditPlan, on_delete=models.CASCADE, related_name='feature_associations')
    feature = models.ForeignKey(PlanFeature, on_delete=models.CASCADE)
    custom_description = models.CharField(max_length=255, blank=True, help_text="Optional custom description for this feature in this plan")
    
    def __str__(self):
        return f"{self.plan.name} - {self.feature.name}"
    
    class Meta:
        db_table = 'plan_feature_associations'
        verbose_name = 'Plan Feature Association'
        verbose_name_plural = 'Plan Feature Associations'
        unique_together = ('plan', 'feature')
        indexes = [
            models.Index(fields=['plan']),
            models.Index(fields=['feature']),
        ]

class UserSubscription(BaseModel):
    """User subscriptions to credit plans"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('trial', 'Trial'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(CreditPlan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} - {self.status}"
    
    class Meta:
        db_table = 'user_subscriptions'
        verbose_name = 'User Subscription'
        verbose_name_plural = 'User Subscriptions'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['plan']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]
