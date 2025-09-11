from rest_framework import serializers
from .models import MetaCollection
from common.apps.gallery.serializers import CollectionSerializer

class MetaCollectionSerializer(serializers.ModelSerializer):
    favourite_collections = CollectionSerializer(many=True, read_only=True)
    starred_collections = CollectionSerializer(many=True, read_only=True)
    liked_collections = CollectionSerializer(many=True, read_only=True)
    shared_collections = serializers.SerializerMethodField()
    collections_shared_by_me = serializers.SerializerMethodField()

    class Meta:
        model = MetaCollection
        fields = ['id', 'user', 'favourite_collections', 'starred_collections', 'liked_collections', 'shared_collections', 'collections_shared_by_me']

    def get_shared_collections(self, obj):
        """Collections that have been shared with this user"""
        from .models import SharedCollection
        shared = SharedCollection.objects.filter(shared_with=obj.user)
        return CollectionSerializer([s.collection for s in shared], many=True).data
    
    def get_collections_shared_by_me(self, obj):
        """Collections that this user has shared with others"""
        from .models import SharedCollection
        shared_by_me = SharedCollection.objects.filter(owner=obj.user).select_related('collection', 'shared_with')
        
        # Group by collection and include sharing details
        shared_data = []
        for share in shared_by_me:
            collection_data = CollectionSerializer(share.collection).data
            # Add sharing metadata
            collection_data['shared_with_email'] = share.shared_with.email
            collection_data['shared_with_username'] = share.shared_with.username
            collection_data['shared_at'] = share.shared_at
            shared_data.append(collection_data)
        
        return shared_data

class AddToFavouriteSerializer(serializers.Serializer):
    collection_id = serializers.UUIDField()

    def validate_collection_id(self, value):
        from common.apps.gallery.models import Collection
        if not Collection.objects.filter(id=value).exists():
            raise serializers.ValidationError("Collection does not exist.")
        return value

class AddToStarredSerializer(serializers.Serializer):
    collection_id = serializers.UUIDField()

    def validate_collection_id(self, value):
        from common.apps.gallery.models import Collection
        if not Collection.objects.filter(id=value).exists():
            raise serializers.ValidationError("Collection does not exist.")
        return value

class ShareCollectionSerializer(serializers.Serializer):
    collection_id = serializers.UUIDField()
    email = serializers.EmailField()

    def validate(self, data):
        from common.apps.gallery.models import Collection
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not Collection.objects.filter(id=data['collection_id']).exists():
            raise serializers.ValidationError("Collection does not exist.")
        if not User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return data

class AddToLikedCollectionSerializer(serializers.Serializer):
    collection_id = serializers.UUIDField()

    def validate_collection_id(self, value):
        from common.apps.gallery.models import Collection
        if not Collection.objects.filter(id=value).exists():
            raise serializers.ValidationError("Collection does not exist.")
        return value

class SharedCollectionResponseSerializer(serializers.Serializer):
    """Response serializer for shared collections with metadata"""
    id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField()
    shared_with_email = serializers.EmailField()
    shared_with_username = serializers.CharField()
    shared_at = serializers.DateTimeField()

class SharedCollectionsByUserResponseSerializer(serializers.Serializer):
    """Response serializer for collections shared by a specific user"""
    collections_shared_by_user = SharedCollectionResponseSerializer(many=True)
    sharer_info = serializers.DictField()
    total_count = serializers.IntegerField()

class UsersWhoSharedCollectionsResponseSerializer(serializers.Serializer):
    """Response serializer for users who shared collections"""
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    shared_collections_count = serializers.IntegerField()

class UsersWhoSharedCollectionsListResponseSerializer(serializers.Serializer):
    """Response serializer for list of users who shared collections"""
    users_who_shared = UsersWhoSharedCollectionsResponseSerializer(many=True)
    total_users = serializers.IntegerField()

class MySharedCollectionsResponseSerializer(serializers.Serializer):
    """Response serializer for collections shared by current user"""
    collections_shared_by_me = SharedCollectionResponseSerializer(many=True)
    total_count = serializers.IntegerField()