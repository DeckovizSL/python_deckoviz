from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import MetaImage, SharedImage
from .serializers import MetaImageSerializer, AddToLikedSerializer, AddToStarredSerializer, ShareImageSerializer, MySharedImagesResponseSerializer, SharedImagesByUserResponseSerializer, UsersWhoSharedListResponseSerializer
from common.apps.gallery.models import Image
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse

@extend_schema(
    responses={200: MetaImageSerializer},
    description="Retrieve the current user's MetaImage object, including liked, starred, and shared images. Creates one if it does not exist.",
    tags=["MetaImages"]
)
class MetaImageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        meta_image, created = MetaImage.objects.prefetch_related(
            'liked_images__uploaded_by',
            'starred_images__uploaded_by'
        ).get_or_create(user=request.user)
        serializer = MetaImageSerializer(meta_image)
        return Response(serializer.data)

@extend_schema(
    request=AddToLikedSerializer,
    responses={200: OpenApiResponse(description='Image added to liked.'), 403: OpenApiResponse(description='Permission denied.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Add an image to the user's liked images. Only public or self-owned images can be liked."
)
class AddToLikedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToLikedSerializer(data=request.data)
        if serializer.is_valid():
            image_id = serializer.validated_data['image_id']
            image = Image.objects.get(id=image_id)
            meta_image, created = MetaImage.objects.get_or_create(user=request.user)
            if image.view == 'public' or image.uploaded_by == request.user:
                meta_image.liked_images.add(image)
                return Response({'status': 'image added to liked'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'You do not have permission to like this image'}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=AddToLikedSerializer,
    responses={200: OpenApiResponse(description='Image removed from liked.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Remove an image from the user's liked images."
)
class RemoveFromLikedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToLikedSerializer(data=request.data)
        if serializer.is_valid():
            image_id = serializer.validated_data['image_id']
            image = Image.objects.get(id=image_id)
            meta_image, created = MetaImage.objects.get_or_create(user=request.user)
            meta_image.liked_images.remove(image)
            return Response({'status': 'image removed from liked'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=AddToStarredSerializer,
    responses={200: OpenApiResponse(description='Image added to starred.'), 403: OpenApiResponse(description='Permission denied.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Add an image to the user's starred images. Only public or self-owned images can be starred."
)
class AddToStarredView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToStarredSerializer(data=request.data)
        if serializer.is_valid():
            image_id = serializer.validated_data['image_id']
            image = Image.objects.get(id=image_id)
            meta_image, created = MetaImage.objects.get_or_create(user=request.user)
            if image.view == 'public' or image.uploaded_by == request.user:
                meta_image.starred_images.add(image)
                return Response({'status': 'image added to starred'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'You do not have permission to star this image'}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=AddToStarredSerializer,
    responses={200: OpenApiResponse(description='Image removed from starred.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Remove an image from the user's starred images."
)
class RemoveFromStarredView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToStarredSerializer(data=request.data)
        if serializer.is_valid():
            image_id = serializer.validated_data['image_id']
            image = Image.objects.get(id=image_id)
            meta_image, created = MetaImage.objects.get_or_create(user=request.user)
            meta_image.starred_images.remove(image)
            return Response({'status': 'image removed from starred'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=ShareImageSerializer,
    responses={200: OpenApiResponse(description='Image shared with user.'), 403: OpenApiResponse(description='Only the owner can share this image.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Share an image with another user by email. Only the owner can share.",
    tags=["Image Sharing"]
)
class ShareImageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ShareImageSerializer(data=request.data)
        if serializer.is_valid():
            image_id = serializer.validated_data['image_id']
            email = serializer.validated_data['email']
            User = get_user_model()
            image = Image.objects.get(id=image_id)
            user_to_share = User.objects.get(email=email)
            # Only owner can share
            if image.uploaded_by != request.user:
                return Response({'error': 'Only the owner can share this image.'}, status=status.HTTP_403_FORBIDDEN)
            SharedImage.objects.get_or_create(image=image, owner=request.user, shared_with=user_to_share)
            return Response({'status': f'Image shared with {email}'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=ShareImageSerializer,
    responses={200: OpenApiResponse(description='User removed from shared image.'), 403: OpenApiResponse(description='Only the owner can remove shared users.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Remove a user from a shared image. Only the owner can remove.",
    tags=["Image Sharing"]
)
class RemoveSharedUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ShareImageSerializer(data=request.data)
        if serializer.is_valid():
            image_id = serializer.validated_data['image_id']
            email = serializer.validated_data['email']
            User = get_user_model()
            image = Image.objects.get(id=image_id)
            user_to_remove = User.objects.get(email=email)
            # Only owner can remove
            if image.uploaded_by != request.user:
                return Response({'error': 'Only the owner can remove shared users.'}, status=status.HTTP_403_FORBIDDEN)
            SharedImage.objects.filter(image=image, owner=request.user, shared_with=user_to_remove).delete()
            return Response({'status': f'User {email} removed from shared image'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    responses={200: MySharedImagesResponseSerializer},
    description="Get all images that the current user has shared with others, including sharing details.",
    tags=["Image Sharing"]
)
class MySharedImagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shared_by_me = SharedImage.objects.filter(owner=request.user).select_related('image', 'shared_with')
        
        # Group by image and include sharing details
        shared_data = []
        for share in shared_by_me:
            from common.apps.gallery.serializers import ImageSerializer
            image_data = ImageSerializer(share.image).data
            # Add sharing metadata
            image_data['shared_with_email'] = share.shared_with.email
            image_data['shared_with_username'] = share.shared_with.username
            image_data['shared_at'] = share.shared_at
            shared_data.append(image_data)
        
        return Response({
            'images_shared_by_me': shared_data,
            'total_count': len(shared_data)
        })

@extend_schema(
    responses={200: SharedImagesByUserResponseSerializer, 404: OpenApiResponse(description='User not found')},
    description="Get all images that a specific user has shared with the current user. Useful for filtering shared content by sharer.",
    parameters=[
        {
            'name': 'user_id',
            'in': 'path',
            'required': True,
            'description': 'ID of the user who shared the images',
            'schema': {'type': 'integer'}
        }
    ],
    tags=["Image Sharing - User Filtering"]
)
class SharedImagesByUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            User = get_user_model()
            sharer_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get images shared by the specific user with the current user
        shared_with_me = SharedImage.objects.filter(
            owner=sharer_user, 
            shared_with=request.user
        ).select_related('image', 'owner')
        
        # Format the response
        shared_data = []
        for share in shared_with_me:
            from common.apps.gallery.serializers import ImageSerializer
            image_data = ImageSerializer(share.image).data
            # Add sharer metadata
            image_data['shared_by_email'] = share.owner.email
            image_data['shared_by_username'] = share.owner.username
            image_data['shared_at'] = share.shared_at
            shared_data.append(image_data)
        
        return Response({
            'images_shared_by_user': shared_data,
            'sharer_info': {
                'user_id': sharer_user.id,
                'username': sharer_user.username,
                'email': sharer_user.email
            },
            'total_count': len(shared_data)
        })

@extend_schema(
    responses={200: UsersWhoSharedListResponseSerializer},
    description="Get all users who have shared images with the current user. Useful for building a filter list in the frontend.",
    tags=["Image Sharing - User Filtering"]
)
class UsersWhoSharedImagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get unique users who have shared images with the current user
        shared_users = SharedImage.objects.filter(
            shared_with=request.user
        ).values(
            'owner__id', 'owner__username', 'owner__email'
        ).distinct()
        
        users_data = []
        for user_data in shared_users:
            # Count how many images this user has shared with me
            image_count = SharedImage.objects.filter(
                owner_id=user_data['owner__id'],
                shared_with=request.user
            ).count()
            
            users_data.append({
                'user_id': user_data['owner__id'],
                'username': user_data['owner__username'],
                'email': user_data['owner__email'],
                'shared_images_count': image_count
            })
        
        return Response({
            'users_who_shared': users_data,
            'total_users': len(users_data)
        }) 