from common.apps.authentication.models import BaseModel
from django.db import models
from django.contrib.auth import get_user_model 


User = get_user_model()

        
class Review(BaseModel): 
    '''
    Review model for reviews
    '''
    customer = models.ForeignKey(User,on_delete=models.PROTECT,related_name='customer_reviews')
    customer_rating = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)   
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True,blank=False,null=False)
    comment = models.TextField(null=False,blank=False)
            
    def __str__(self) -> str:
        return f"{self.customer.username} left review"    
    
    class Meta:
        db_table = 'reviews'
        managed = True
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'