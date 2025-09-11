from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxLengthValidator
from apps.utils.choices import ADDRESS_TYPES
from .managers import AddressManager
from django.utils import timezone
import secrets

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class BaseModel(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True



class User(AbstractUser,BaseModel):
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    profile_visible = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    banner_pictures = models.JSONField(default=list, blank=True)
    bio = models.TextField(validators=[MaxLengthValidator(500)], blank=True) 
    room = models.UUIDField(default=uuid.uuid4, blank=False, null=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username'] 

    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email', 'username', 'first_name', 'last_name', 'is_active', 'room']),
        ]

# --- DeviceLink model for device-user pairing and refresh token management ---
class DeviceLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="device_links")
    device_type = models.CharField(max_length=50, default="tv")
    refresh_token_hash = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
        
class Address(BaseModel):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=255, choices=ADDRESS_TYPES, default='billing')
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.address}, {self.city}, {self.state}, {self.country}, {self.zip_code}"
    
    objects = AddressManager()
    class Meta:
        db_table = 'addresses'
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        indexes = [
            models.Index(fields=['user']),
        ]


class NewsLetterSubscriber(BaseModel):
    name = models.CharField(max_length=255,null=True,blank=True)
    email = models.EmailField(unique=True)

    def __str__(self) -> str:
        return f'{self.email} subscribed to newsletter.'

    class Meta:
        db_table = 'newsletters'
        verbose_name = 'Newsletter'
        verbose_name_plural = 'Newsletters'
        indexes = [
            models.Index(fields=['email']),
        ]

class UserProfile(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=255, blank=True)
    vocation = models.CharField(max_length=255, blank=True)
    hobbies = models.TextField(blank=True)
    passions = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    desired_states = models.TextField(blank=True)
    personal_beliefs = models.TextField(blank=True)
    life_principles = models.TextField(blank=True)
    core_values = models.TextField(blank=True)
    secondary_values = models.TextField(blank=True)
    hopes_and_dreams = models.TextField(blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)

    def is_expired(self):
        # Token valid for 1 hour
        return timezone.now() > self.created_at + timezone.timedelta(hours=1)

    def __str__(self):
        return f"Password reset token for {self.user.email} ({'used' if self.is_used else 'active'})" 

class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verification_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)

    def is_expired(self):
        # Token valid for 24 hours
        return timezone.now() > self.created_at + timezone.timedelta(hours=24)

    def __str__(self):
        return f"Email verification token for {self.user.email} ({'used' if self.is_used else 'active'})" 