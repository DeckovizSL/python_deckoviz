from django.db import models
from common.apps.authentication.models import TimeStampedModel
from django.contrib.auth import get_user_model


User = get_user_model()


class ChatBookmark(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    chat_url = models.URLField()
    title = models.CharField(max_length=255, blank=True) 

    def __str__(self):
        return f"{self.user.username}'s bookmark: {self.title or self.chat_url}"

