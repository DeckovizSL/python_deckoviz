from common.apps.authentication.models import BaseModel
from django.db import models
from common.apps.utils.choices import PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES
from .managers import TransactionManager

class Transaction(BaseModel):
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE, related_name='transactions')
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='transactions',null=True,blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=255,choices=PAYMENT_METHOD_CHOICES,default='stripe')
    ref_id = models.CharField(max_length=255,blank=True,null=True)
    signature = models.CharField(max_length=255,blank=True,null=True)
    status = models.CharField(max_length=255,default='pending',choices=PAYMENT_STATUS_CHOICES)
    
    def __str__(self):
        return f"{self.user.username} - {self.id}"
    
    objects = TransactionManager()
    
    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['order']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
        ]
        