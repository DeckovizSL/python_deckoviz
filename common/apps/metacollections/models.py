from django.db import models
from django.contrib.auth import get_user_model
from common.apps.authentication.models import BaseModel
from common.apps.gallery.models import Collection

User = get_user_model()

class MetaCollection(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='meta_collection')
    favourite_collections = models.ManyToManyField(Collection, related_name='favourited_by_meta_collections', blank=True)
    starred_collections = models.ManyToManyField(Collection, related_name='starred_by_meta_collections', blank=True)
    liked_collections = models.ManyToManyField(Collection, related_name='liked_by_meta_collections', blank=True)

    class Meta:
        db_table = 'meta_collections'
        verbose_name = 'Meta Collection'
        verbose_name_plural = 'Meta Collections'
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username}'s Meta Collection"

class SharedCollection(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='shared_with')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_collections')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections_shared_to_me')
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('collection', 'shared_with')

    def __str__(self):
        return f"{self.owner.email} shared {self.collection} with {self.shared_with.email}" 