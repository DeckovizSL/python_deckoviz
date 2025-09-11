from django.db import models
from django.contrib.auth import get_user_model
from common.apps.authentication.models import BaseModel
from common.apps.gallery.models import Image

User = get_user_model()

class MetaImage(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='meta_image')
    liked_images = models.ManyToManyField(Image, related_name='liked_by_meta_images', blank=True)
    starred_images = models.ManyToManyField(Image, related_name='starred_by_meta_images', blank=True)

    class Meta:
        db_table = 'meta_images'
        verbose_name = 'Meta Image'
        verbose_name_plural = 'Meta Images'
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username}'s Meta Images"


class SharedImage(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='shared_with')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_images')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='images_shared_to_me')
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('image', 'shared_with')

    def __str__(self):
        return f"{self.owner.email} shared {self.image} with {self.shared_with.email}" 