from django.db import models
from ckeditor.fields import RichTextField
from django.contrib.postgres.fields import ArrayField
from common.apps.authentication.models import BaseModel
import uuid

class Asset(models.Model):
    id = models.CharField(max_length=256,primary_key=True,default=uuid.uuid4)
    file = models.FileField(upload_to='assets',null=False,blank=False) 

class Blog(BaseModel):
    title = models.TextField(max_length=256)
    description = description =  RichTextField()
    tags = ArrayField(models.CharField(max_length=100), blank=True, default=list) 
    images = models.ManyToManyField(Asset, related_name='blogs_images', blank=True)
    videos = models.ManyToManyField(Asset, related_name='blogs_videos', blank=True)
    delete_status = models.IntegerField(default=0,null=False,blank=False)
    
    class Meta:
        db_table = 'blogs'
        managed = True
        verbose_name = 'Blog'
        verbose_name_plural = 'Blogs'
        indexes = [
            models.Index(fields=['created_at'], name='idx_blog_created_at'),  # Index on created_at
        ]
        
    def __str__(self):
        return self.title

 