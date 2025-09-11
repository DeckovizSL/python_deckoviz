from rest_framework import serializers
from .models import CuratedImages, CuratedCollections
from common.apps.gallery.serializers import ImageSerializer, CollectionSerializer


class CuratedImagesSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    created_by = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = CuratedImages
        fields = [
            'id',
            'images',
            'is_active',
            'created_by',
            'created_at',
            'updated_at'
        ]


class CuratedCollectionsSerializer(serializers.ModelSerializer):
    collections = CollectionSerializer(many=True, read_only=True)
    created_by = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = CuratedCollections
        fields = [
            'id',
            'collections',
            'is_active',
            'created_by',
            'created_at',
            'updated_at'
        ]
