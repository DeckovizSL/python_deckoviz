from django.db import models
from common.apps.authentication.models import BaseModel
from .managers import PriceManager
from common.apps.utils.choices import SIZE_CHOICES,CANVAS_RATIO



class Price(BaseModel):
    image = models.OneToOneField('gallery.Image', on_delete=models.CASCADE, related_name='prices',unique=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=255,default='S', choices=SIZE_CHOICES)
    canvas_ratio = models.CharField(max_length=255,default='16:9', blank=True, null=True,choices=CANVAS_RATIO)
    is_active = models.BooleanField(default=True)
    
    objects = PriceManager()
    
    def __str__(self):
        return f"Price {self.id}"
    
    class Meta:
        db_table = 'prices'
        verbose_name = 'Price'
        verbose_name_plural = 'Prices'
        indexes = [
            models.Index(fields=['final_price']),
        ]
        

    
    