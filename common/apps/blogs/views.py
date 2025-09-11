from django.shortcuts import render
from common.apps.blogs.models import Blog
from common.apps.blogs.serializers import BlogSerializer
from rest_framework import mixins,viewsets 
from rest_framework.permissions import  AllowAny

class BlogView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):  
    queryset = Blog.objects.filter(delete_status=0)
    serializer_class = BlogSerializer
    permission_classes = [ AllowAny,]   

 