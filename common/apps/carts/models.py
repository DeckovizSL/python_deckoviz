from django.db import models
from common.apps.authentication.models import BaseModel
from django.contrib.auth import get_user_model

User = get_user_model()


class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ForeignKey('gallery.Image', on_delete=models.PROTECT, related_name='carts', null=False, blank=False)
    price = models.ForeignKey('marketplace.Price', on_delete=models.PROTECT, related_name='carts', null=False, blank=False)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Cart for {self.user.username}"
    
    class Meta:
        unique_together = ['user', 'image']
        db_table = 'carts'
        verbose_name = 'Cart'
        ordering = ['-created_at']
        verbose_name_plural = 'Carts'
        indexes = [
            models.Index(fields=['user']),
        ]