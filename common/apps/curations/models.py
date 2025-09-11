from django.db import models
from django.contrib.auth import get_user_model
from common.apps.authentication.models import BaseModel
from common.apps.gallery.models import Image, Collection

User = get_user_model()


class CuratedImages(BaseModel):
    """
    Single curation list for images managed by admin
    """
    images = models.ManyToManyField(Image, related_name='curated_images', blank=True)
    is_active = models.BooleanField(default=True, help_text="Whether this curation is active")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_image_curations')
    
    class Meta:
        db_table = 'curated_images'
        verbose_name = 'Curated Images'
        verbose_name_plural = 'Curated Images'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Image Curation ({self.images.count()} images)"


class CuratedCollections(BaseModel):
    """
    Single curation list for collections managed by admin
    """
    collections = models.ManyToManyField(Collection, related_name='curated_collections', blank=True)
    is_active = models.BooleanField(default=True, help_text="Whether this curation is active")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_collection_curations')
    
    class Meta:
        db_table = 'curated_collections'
        verbose_name = 'Curated Collections'
        verbose_name_plural = 'Curated Collections'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Collection Curation ({self.collections.count()} collections)"
