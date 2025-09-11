from django.db import models
from common.apps.authentication.models import BaseModel
from django.contrib.auth import get_user_model
from common.apps.utils.choices import INTERACTION_TYPES,VIEW_TYPES,TRANSCRIPTION_STATUS,COLLECTION_TYPES
from common.apps.utils.user_directory import user_image_path,user_music_path,user_audio_path
import uuid
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Audio(BaseModel):
    # Audio file and basic information
    audio = models.FileField(upload_to=user_audio_path, blank=True, null=True, max_length=500)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name='uploaded_audios')
    view = models.CharField(max_length=255, blank=True, null=True, choices=VIEW_TYPES, default='private')
    is_active = models.BooleanField(default=True)
    music_cover = models.ImageField(upload_to=user_image_path, blank=True, null=True, max_length=500, help_text="Optional cover photo for the audio")
    
    # New fields for audio metadata
    track_title = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    genre = models.CharField(max_length=100, blank=True, default="")
    
    # Transcription fields
    transcript = models.TextField(blank=True, null=True)
    transcript_url = models.URLField(blank=True, null=True)
    transcript_status = models.CharField(max_length=255, blank=True, null=True, choices=TRANSCRIPTION_STATUS, default='processing')
    
    # New transcript analysis fields
    transcript_insights = models.JSONField(blank=True, null=True, help_text="Full analysis results as JSON")
    transcript_summary = models.TextField(blank=True, null=True, help_text="Summary of the transcript")
    transcript_sentiment = models.CharField(max_length=50, blank=True, null=True, help_text="Overall sentiment of the transcript")
    
    # Processing metadata
    processed_at = models.DateTimeField(blank=True, null=True, help_text="When the audio was last processed")
    error_message = models.TextField(blank=True, null=True, help_text="Error message if processing failed")
    retry_count = models.PositiveSmallIntegerField(default=0, help_text="Number of retries for failed processing")
    
    class Meta:
        db_table = 'audios'
        verbose_name = 'Audio'
        verbose_name_plural = 'Audios'
        indexes = [
            models.Index(fields=['uploaded_by']),
        ]
    
    def __str__(self):
        return f"Audio {self.id}"

class Image(BaseModel):
    title = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    file = models.ImageField(upload_to=user_image_path, blank=True, null=True)
    image_id = models.CharField(max_length=255,unique=True)
    external_url = models.URLField(blank=True, null=True)
    music = models.FileField(upload_to=user_music_path, blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name='uploaded_images')
    metadata = models.JSONField(blank=True, null=True)
    view = models.CharField(max_length=255, blank=True, null=True,choices=VIEW_TYPES,default='private')
    embedding_id = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'images'
        verbose_name = 'Image'
        verbose_name_plural = 'Images'
        indexes = [
            models.Index(fields=['uploaded_by']),
        ]
    
    def __str__(self):
        return f"Image {self.id}"
    
    def save(self, *args, **kwargs):
        if not self.image_id:
            self.image_id = str(uuid.uuid4())
        super().save(*args, **kwargs)
    
class Collection(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=255)
    music = models.FileField(upload_to=user_music_path, blank=True, null=True, max_length=500)
    view = models.CharField(max_length=255, blank=True, null=True,choices=VIEW_TYPES,default='private')  
    display_time = models.IntegerField(default=10, help_text="Time in seconds to display each image")
    music_preference = models.CharField(max_length=255, blank=True)
    meta_notes = models.TextField(blank=True)
    metadata=models.JSONField(blank=True,null=True)
    is_active = models.BooleanField(default=True)
    type = models.CharField(max_length=255, blank=True, null=True,choices=COLLECTION_TYPES,default='personal')
    description = models.TextField(blank=True, default="")
    tags = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    music_title = models.CharField(max_length=255, blank=True, null=True, help_text="Optional title for the collection's music")
    
    class Meta:
        db_table = 'collections'
        verbose_name = 'Collection'
        verbose_name_plural = 'Collections'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.user.username}'s collection: {self.name}"  
    
class CollectionImage(BaseModel):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='collection_images')
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='image_collections')
    order = models.PositiveIntegerField(default=0)
    view = models.CharField(max_length=255, blank=True, null=True,choices=VIEW_TYPES,default='private')  
    class Meta:
        db_table = 'collection_images'
        verbose_name = 'Collection Image'
        verbose_name_plural = 'Collection Images'
        ordering = ['order']
        unique_together = ['collection', 'image']
        

class ImageInteraction(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='image_interactions')
    # Support both internal and external images
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='interactions', null=True, blank=True)
    external_image_id = models.CharField(max_length=255, null=True, blank=True)  # For external images
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)

    class Meta:
        db_table = 'image_interactions'
        verbose_name = 'Image Interaction'
        verbose_name_plural = 'Image Interactions'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['image']),
            models.Index(fields=['external_image_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'image', 'interaction_type'],
                condition=models.Q(image__isnull=False),
                name='unique_internal_image_interaction'
            ),
            models.UniqueConstraint(
                fields=['user', 'external_image_id', 'interaction_type'],
                condition=models.Q(external_image_id__isnull=False),
                name='unique_external_image_interaction'
            ),
            models.CheckConstraint(
                check=(
                    models.Q(image__isnull=False, external_image_id__isnull=True) | 
                    models.Q(image__isnull=True, external_image_id__isnull=False)
                ),
                name='either_internal_or_external_image'
            )
        ]
        
    def __str__(self):
        image_identifier = self.image.id if self.image else self.external_image_id
        return f"{self.user.username} - {self.interaction_type} - {image_identifier}"

 
class MetaComment(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    # Support both internal and external images
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    external_image_id = models.CharField(max_length=255, null=True, blank=True)  # For external images
    content = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'meta_comments'
        verbose_name = 'Meta Comment'
        verbose_name_plural = 'Meta Comments'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['image']),
            models.Index(fields=['external_image_id']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(image__isnull=False, external_image_id__isnull=True) | 
                    models.Q(image__isnull=True, external_image_id__isnull=False)
                ),
                name='comment_either_internal_or_external_image'
            )
        ]

    def __str__(self):
        image_identifier = self.image.id if self.image else self.external_image_id
        return f"Comment by {self.user.username} on {image_identifier}"

class DailyCuration(models.Model):
    date = models.DateField(default=timezone.now, unique=True)
    collections = models.ManyToManyField(Collection, related_name='daily_curations')

    class Meta:
        verbose_name = 'Daily Curation'
        verbose_name_plural = 'Daily Curations'
        ordering = ['-date']

    def __str__(self):
        return f"Daily Curation for {self.date}"

class DailyImageCuration(models.Model):
    date = models.DateField(default=timezone.now, unique=True)
    images = models.ManyToManyField(Image, related_name='daily_image_curations')

    class Meta:
        verbose_name = 'Daily Image Curation'
        verbose_name_plural = 'Daily Image Curations'
        ordering = ['-date']

    def __str__(self):
        return f"Daily Image Curation for {self.date}"

class Ritual(BaseModel):
    name = models.CharField(max_length=100)
    time_of_day = models.TimeField(help_text="Time of day when the ritual is triggered")
    collections = models.ManyToManyField(Collection, related_name='rituals')
    is_active = models.BooleanField(default=True)
    is_global = models.BooleanField(default=False, help_text="True for admin/global rituals, False for user-defined rituals")
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, help_text="Null for global rituals, set for user-defined rituals")
    repeat_type = models.CharField(
        max_length=10,
        choices=[('none', 'None'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
        default='none',
        help_text="How often the ritual repeats."
    )
    repeat_details = models.JSONField(
        blank=True, null=True,
        help_text="Details for repeat: For weekly, provide 'weekdays' (list of 0-6); for monthly, 'monthday' (1-31); for yearly, 'month' (1-12) and 'day' (1-31). Leave empty for daily. Edge cases: If a day does not exist (e.g., Feb 30), skip or trigger on last valid day."
    )
    description_and_meta_notes = models.TextField(
        blank=True, null=True,
        help_text="Description and meta notes for the ritual."
    )
    
    class Meta:
        db_table = 'rituals'
        verbose_name = 'Ritual'
        verbose_name_plural = 'Rituals'
        indexes = [
            models.Index(fields=['is_global', 'created_by', 'time_of_day']),
        ]

    def __str__(self):
        return f"{'Global' if self.is_global else 'User'} Ritual: {self.name} at {self.time_of_day}"

    def should_run_on_date(self, date):
        """
        Returns True if the ritual should run on the given date (a datetime.date object),
        based on repeat_type and repeat_details. Handles edge cases.
        """
        if not self.is_active:
            return False
        if self.repeat_type == 'none':
            return False
        if self.repeat_type == 'daily':
            return True
        if self.repeat_type == 'weekly':
            weekdays = (self.repeat_details or {}).get('weekdays', [])
            return date.weekday() in weekdays
        if self.repeat_type == 'monthly':
            monthday = (self.repeat_details or {}).get('monthday')
            if not monthday:
                return False
            # Handle months with fewer days (e.g., Feb 30)
            last_day = (date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            if monthday > last_day.day:
                return date.day == last_day.day
            return date.day == monthday
        if self.repeat_type == 'yearly':
            month = (self.repeat_details or {}).get('month')
            day = (self.repeat_details or {}).get('day')
            if not month or not day:
                return False
            if date.month != month:
                return False
            # Handle invalid days (e.g., Feb 30)
            try:
                return date.day == day
            except ValueError:
                # If the day doesn't exist, trigger on the last valid day of the month
                last_day = (date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                return date.day == last_day.day
        return False