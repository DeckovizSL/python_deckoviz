"""
URL configuration for deckoviz project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path,include,re_path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView,SpectacularRedocView,SpectacularSwaggerView


# Set dynamic admin title based on the environment
if settings.DEBUG:
    admin.site.site_header = 'Decoviz Admin (Development)'
    admin.site.site_title = 'Decoviz Admin Portal (Dev)'
else:
    admin.site.site_header = 'Decoviz Admin'
    admin.site.site_title = 'Decoviz Admin Portal'
admin.site.site_url = 'https://deckoviz.com/'


router = DefaultRouter()


urlpatterns = [
    path('admin/', admin.site.urls), 
    
    #authentication api
    path('auth/',include('common.apps.authentication.urls')),
    
    # gallery api
    path('gallery/', include('common.apps.gallery.urls')), 
    
    #cart api
    path('carts/', include('common.apps.carts.urls')),
    
    #marketplace api
    path('marketplace/', include('common.apps.marketplace.urls')),
    
    #orders api
    path('order/', include('common.apps.orders.urls')),
    
    #payments api
    path('payment/', include('common.apps.payments.urls')),

    #credits api
    path('credits/', include('common.apps.credits.urls')),

    # ai integration api
    path('ai/', include('common.apps.ai_integration.urls')),

    #blogs api
    path('blogs/',include('common.apps.blogs.urls')),
    
    # metacollections api
    path('metacollections/', include('common.apps.metacollections.urls')),

    # modes api
    path('modes/', include('common.apps.modes.urls')),

    # dashboard app
    path('dashboard/', include('common.apps.dashboard.urls')),

    # metaimages api
    path('metaimages/', include('common.apps.metaimages.urls')),

    # metaaudios api
    path('metaaudios/', include('common.apps.metaaudios.urls')),

    # curations api
    path('curations/', include('common.apps.curations.urls')),

    # analytics api
    path('api/analytics/', include('common.apps.analytics.urls')),
     
    #api documentation view
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/',
         SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/',
         SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
