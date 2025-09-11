from django.db import models
from django.contrib.auth import get_user_model
from common.apps.authentication.models import BaseModel
from common.apps.gallery.models import Audio

User = get_user_model()

class MetaAudio(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='meta_audio')
    liked_audios = models.ManyToManyField(Audio, related_name='liked_by_meta_audios', blank=True)
    starred_audios = models.ManyToManyField(Audio, related_name='starred_by_meta_audios', blank=True)

    class Meta:
        db_table = 'meta_audios'
        verbose_name = 'Meta Audio'
        verbose_name_plural = 'Meta Audios'
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username}'s Meta Audios" 