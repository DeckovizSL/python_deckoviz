from django.urls import include,path 
from rest_framework.routers import DefaultRouter
from common.apps.blogs import views


router = DefaultRouter()

router.register('', views.BlogView, basename='blogs')

urlpatterns = [
    path('',include(router.urls))
]
