from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import MetaCollection, SharedCollection
from .serializers import MetaCollectionSerializer, AddToFavouriteSerializer, AddToStarredSerializer, ShareCollectionSerializer, AddToLikedCollectionSerializer, MySharedCollectionsResponseSerializer, SharedCollectionsByUserResponseSerializer, UsersWhoSharedCollectionsListResponseSerializer
from common.apps.gallery.models import Collection
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse

@extend_schema(
    responses={200: MetaCollectionSerializer},
    description="Retrieve the current user's MetaCollection object, including favourite, starred, liked, and shared collections. Creates one if it does not exist.",
    tags=["MetaCollections"]
)
class MetaCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        meta_collection, created = MetaCollection.objects.prefetch_related(
            'favourite_collections__collection_images__image__uploaded_by',
            'starred_collections__collection_images__image__uploaded_by',
            'liked_collections__collection_images__image__uploaded_by'
        ).get_or_create(user=request.user)
        serializer = MetaCollectionSerializer(meta_collection)
        return Response(serializer.data)

@extend_schema(
    request=AddToFavouriteSerializer,
    responses={200: OpenApiResponse(description='Collection added to favourites.'), 403: OpenApiResponse(description='Permission denied.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Add a collection to the user's favourites. Only public or self-owned collections can be favourited."
)
class AddToFavouritesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToFavouriteSerializer(data=request.data)
        if serializer.is_valid():
            collection_id = serializer.validated_data['collection_id']
            collection = Collection.objects.get(id=collection_id)
            meta_collection, created = MetaCollection.objects.get_or_create(user=request.user)
            # Check if collection is public or owned by user
            if collection.view == 'public' or collection.user == request.user:
                meta_collection.favourite_collections.add(collection)
                return Response({'status': 'collection added to favourites'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'You do not have permission to add this collection to favourites'}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=AddToFavouriteSerializer,
    responses={200: OpenApiResponse(description='Collection removed from favourites.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Remove a collection from the user's favourites."
)
class RemoveFromFavouritesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToFavouriteSerializer(data=request.data)
        if serializer.is_valid():
            collection_id = serializer.validated_data['collection_id']
            collection = Collection.objects.get(id=collection_id)
            meta_collection, created = MetaCollection.objects.get_or_create(user=request.user)
            meta_collection.favourite_collections.remove(collection)
            return Response({'status': 'collection removed from favourites'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=AddToStarredSerializer,
    responses={200: OpenApiResponse(description='Collection added to starred.'), 403: OpenApiResponse(description='Permission denied.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Add a collection to the user's starred collections. Only public or self-owned collections can be starred."
)
class AddToStarredView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToStarredSerializer(data=request.data)
        if serializer.is_valid():
            collection_id = serializer.validated_data['collection_id']
            collection = Collection.objects.get(id=collection_id)
            meta_collection, created = MetaCollection.objects.get_or_create(user=request.user)
            # Check if collection is public or owned by user
            if collection.view == 'public' or collection.user == request.user:
                meta_collection.starred_collections.add(collection)
                return Response({'status': 'collection added to starred'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'You do not have permission to add this collection to starred'}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=AddToStarredSerializer,
    responses={200: OpenApiResponse(description='Collection removed from starred.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Remove a collection from the user's starred collections."
)
class RemoveFromStarredView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToStarredSerializer(data=request.data)
        if serializer.is_valid():
            collection_id = serializer.validated_data['collection_id']
            collection = Collection.objects.get(id=collection_id)
            meta_collection, created = MetaCollection.objects.get_or_create(user=request.user)
            meta_collection.starred_collections.remove(collection)
            return Response({'status': 'collection removed from starred'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=ShareCollectionSerializer,
    responses={200: OpenApiResponse(description='Collection shared with user.'), 403: OpenApiResponse(description='Only the owner can share this collection.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Share a collection with another user by email. Only the owner can share.",
    tags=["Collection Sharing"]
)
class ShareCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ShareCollectionSerializer(data=request.data)
        if serializer.is_valid():
            collection_id = serializer.validated_data['collection_id']
            email = serializer.validated_data['email']
            User = get_user_model()
            collection = Collection.objects.get(id=collection_id)
            user_to_share = User.objects.get(email=email)
            # Only owner can share
            if collection.user != request.user:
                return Response({'error': 'Only the owner can share this collection.'}, status=status.HTTP_403_FORBIDDEN)
            SharedCollection.objects.get_or_create(collection=collection, owner=request.user, shared_with=user_to_share)
            return Response({'status': f'Collection shared with {email}'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=ShareCollectionSerializer,
    responses={200: OpenApiResponse(description='User removed from shared collection.'), 403: OpenApiResponse(description='Only the owner can remove shared users.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Remove a user from a shared collection. Only the owner can remove.",
    tags=["Collection Sharing"]
)
class RemoveSharedUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ShareCollectionSerializer(data=request.data)
        if serializer.is_valid():
            collection_id = serializer.validated_data['collection_id']
            email = serializer.validated_data['email']
            User = get_user_model()
            collection = Collection.objects.get(id=collection_id)
            user_to_remove = User.objects.get(email=email)
            # Only owner can remove
            if collection.user != request.user:
                return Response({'error': 'Only the owner can remove shared users.'}, status=status.HTTP_403_FORBIDDEN)
            SharedCollection.objects.filter(collection=collection, owner=request.user, shared_with=user_to_remove).delete()
            return Response({'status': f'User {email} removed from shared collection'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=AddToLikedCollectionSerializer,
    responses={200: OpenApiResponse(description='Collection added to liked.'), 403: OpenApiResponse(description='Permission denied.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Add a collection to the user's liked collections. Only public or self-owned collections can be liked."
)
class AddToLikedCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToLikedCollectionSerializer(data=request.data)
        if serializer.is_valid():
            collection_id = serializer.validated_data['collection_id']
            collection = Collection.objects.get(id=collection_id)
            meta_collection, created = MetaCollection.objects.get_or_create(user=request.user)
            # Check if collection is public or owned by user
            if collection.view == 'public' or collection.user == request.user:
                meta_collection.liked_collections.add(collection)
                return Response({'status': 'collection added to liked'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'You do not have permission to like this collection'}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=AddToLikedCollectionSerializer,
    responses={200: OpenApiResponse(description='Collection removed from liked.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Remove a collection from the user's liked collections."
)
class RemoveFromLikedCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToLikedCollectionSerializer(data=request.data)
        if serializer.is_valid():
            collection_id = serializer.validated_data['collection_id']
            collection = Collection.objects.get(id=collection_id)
            meta_collection, created = MetaCollection.objects.get_or_create(user=request.user)
            meta_collection.liked_collections.remove(collection)
            return Response({'status': 'collection removed from liked'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    responses={200: MySharedCollectionsResponseSerializer},
    description="Get all collections that the current user has shared with others, including sharing details.",
    tags=["Collection Sharing"]
)
class MySharedCollectionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shared_by_me = SharedCollection.objects.filter(owner=request.user).select_related('collection', 'shared_with')
        
        # Group by collection and include sharing details
        shared_data = []
        for share in shared_by_me:
            from common.apps.gallery.serializers import CollectionSerializer
            collection_data = CollectionSerializer(share.collection).data
            # Add sharing metadata
            collection_data['shared_with_email'] = share.shared_with.email
            collection_data['shared_with_username'] = share.shared_with.username
            collection_data['shared_at'] = share.shared_at
            shared_data.append(collection_data)
        
        return Response({
            'collections_shared_by_me': shared_data,
            'total_count': len(shared_data)
        })

@extend_schema(
    responses={200: SharedCollectionsByUserResponseSerializer, 404: OpenApiResponse(description='User not found')},
    description="Get all collections that a specific user has shared with the current user. Useful for filtering shared content by sharer.",
    parameters=[
        {
            'name': 'user_id',
            'in': 'path',
            'required': True,
            'description': 'ID of the user who shared the collections',
            'schema': {'type': 'integer'}
        }
    ],
    tags=["Collection Sharing - User Filtering"]
)
class SharedCollectionsByUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            User = get_user_model()
            sharer_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get collections shared by the specific user with the current user
        shared_with_me = SharedCollection.objects.filter(
            owner=sharer_user, 
            shared_with=request.user
        ).select_related('collection', 'owner')
        
        # Format the response
        shared_data = []
        for share in shared_with_me:
            from common.apps.gallery.serializers import CollectionSerializer
            collection_data = CollectionSerializer(share.collection).data
            # Add sharer metadata
            collection_data['shared_by_email'] = share.owner.email
            collection_data['shared_by_username'] = share.owner.username
            collection_data['shared_at'] = share.shared_at
            shared_data.append(collection_data)
        
        return Response({
            'collections_shared_by_user': shared_data,
            'sharer_info': {
                'user_id': sharer_user.id,
                'username': sharer_user.username,
                'email': sharer_user.email
            },
            'total_count': len(shared_data)
        })

@extend_schema(
    responses={200: UsersWhoSharedCollectionsListResponseSerializer},
    description="Get all users who have shared collections with the current user. Useful for building a filter list in the frontend.",
    tags=["Collection Sharing - User Filtering"]
)
class UsersWhoSharedCollectionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get unique users who have shared collections with the current user
        shared_users = SharedCollection.objects.filter(
            shared_with=request.user
        ).values(
            'owner__id', 'owner__username', 'owner__email'
        ).distinct()
        
        users_data = []
        for user_data in shared_users:
            # Count how many collections this user has shared with me
            collection_count = SharedCollection.objects.filter(
                owner_id=user_data['owner__id'],
                shared_with=request.user
            ).count()
            
            users_data.append({
                'user_id': user_data['owner__id'],
                'username': user_data['owner__username'],
                'email': user_data['owner__email'],
                'shared_collections_count': collection_count
            })
        
        return Response({
            'users_who_shared': users_data,
            'total_users': len(users_data)
        }) 