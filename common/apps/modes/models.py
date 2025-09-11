from django.db import models
from django.contrib.auth import get_user_model
from common.apps.authentication.models import BaseModel
from common.apps.gallery.models import Collection, Audio

User = get_user_model()

class Music(BaseModel):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='music/')

    def __str__(self):
        return self.name

class Mode(BaseModel):
    MODES = [
        ('serenity', 'Serenity'),
        ('romantic', 'Romantic'),
        ('inspiration', 'Inspiration'),
        ('dance', 'Dance'),
        ('meditation', 'Meditation'),
        ('creative', 'Creative'),
    ]
    name = models.CharField(max_length=20, choices=MODES, unique=True)
    admin_collections = models.ManyToManyField(Collection, related_name='admin_modes', blank=True)
    admin_curations = models.ManyToManyField(Collection, related_name='curated_modes', blank=True)
    admin_music = models.ManyToManyField(Music, related_name='admin_modes', blank=True)

    def __str__(self):
        return self.get_name_display()

class UserMode(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_modes')
    mode = models.ForeignKey(Mode, on_delete=models.CASCADE, related_name='user_customizations')
    user_collections = models.ManyToManyField(Collection, related_name='user_modes', blank=True)
    user_music = models.ManyToManyField(Audio, related_name='user_modes', blank=True)

    class Meta:
        unique_together = ('user', 'mode')

    def __str__(self):
        return f"{self.user.username}'s {self.mode.get_name_display()} mode"

class Session(BaseModel):
    PURPOSES = [
        ('focus', 'Focus'),
        ('sleep', 'Sleep'),
        ('calm', 'Calm'),
        ('mindfulness', 'Mindfulness'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    mode = models.ForeignKey(Mode, on_delete=models.CASCADE, related_name='sessions')
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    purpose = models.CharField(max_length=20, choices=PURPOSES)
    intention = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"Session for {self.user.username} in {self.mode.get_name_display()} mode"
