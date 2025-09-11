from rest_framework import serializers
from .models import MetaImage
from common.apps.gallery.serializers import ImageSerializer

class MetaImageSerializer(serializers.ModelSerializer):
    liked_images = ImageSerializer(many=True, read_only=True)
    starred_images = ImageSerializer(many=True, read_only=True)
    shared_images = serializers.SerializerMethodField()
    images_shared_by_me = serializers.SerializerMethodField()

    class Meta:
        model = MetaImage
        fields = ['id', 'user', 'liked_images', 'starred_images', 'shared_images', 'images_shared_by_me']

    def get_shared_images(self, obj):
        """Images that have been shared with this user"""
        from .models import SharedImage
        shared = SharedImage.objects.filter(shared_with=obj.user)
        return ImageSerializer([s.image for s in shared], many=True).data
    
    def get_images_shared_by_me(self, obj):
        """Images that this user has shared with others"""
        from .models import SharedImage
        shared_by_me = SharedImage.objects.filter(owner=obj.user).select_related('image', 'shared_with')
        
        # Group by image and include sharing details
        shared_data = []
        for share in shared_by_me:
            image_data = ImageSerializer(share.image).data
            # Add sharing metadata
            image_data['shared_with_email'] = share.shared_with.email
            image_data['shared_with_username'] = share.shared_with.username
            image_data['shared_at'] = share.shared_at
            shared_data.append(image_data)
        
        return shared_data

class AddToLikedSerializer(serializers.Serializer):
    image_id = serializers.UUIDField()

    def validate_image_id(self, value):
        from common.apps.gallery.models import Image
        if not Image.objects.filter(id=value).exists():
            raise serializers.ValidationError("Image does not exist.")
        return value

class AddToStarredSerializer(serializers.Serializer):
    image_id = serializers.UUIDField()

    def validate_image_id(self, value):
        from common.apps.gallery.models import Image
        if not Image.objects.filter(id=value).exists():
            raise serializers.ValidationError("Image does not exist.")
        return value

class ShareImageSerializer(serializers.Serializer):
    image_id = serializers.UUIDField()
    email = serializers.EmailField()

    def validate(self, data):
        from common.apps.gallery.models import Image
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not Image.objects.filter(id=data['image_id']).exists():
            raise serializers.ValidationError("Image does not exist.")
        if not User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return data

class SharedImageResponseSerializer(serializers.Serializer):
    """Response serializer for shared images with metadata"""
    id = serializers.UUIDField()
    title = serializers.CharField()
    image = serializers.URLField()
    thumbnail = serializers.URLField()
    shared_with_email = serializers.EmailField()
    shared_with_username = serializers.CharField()
    shared_at = serializers.DateTimeField()

class SharedImagesByUserResponseSerializer(serializers.Serializer):
    """Response serializer for images shared by a specific user"""
    images_shared_by_user = SharedImageResponseSerializer(many=True)
    sharer_info = serializers.DictField()
    total_count = serializers.IntegerField()

class UsersWhoSharedResponseSerializer(serializers.Serializer):
    """Response serializer for users who shared images"""
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    shared_images_count = serializers.IntegerField()

class UsersWhoSharedListResponseSerializer(serializers.Serializer):
    """Response serializer for list of users who shared images"""
    users_who_shared = UsersWhoSharedResponseSerializer(many=True)
    total_users = serializers.IntegerField()

class MySharedImagesResponseSerializer(serializers.Serializer):
    """Response serializer for images shared by current user"""
    images_shared_by_me = SharedImageResponseSerializer(many=True)
    total_count = serializers.IntegerField()