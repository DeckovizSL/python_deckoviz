from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import MetaAudio
from .serializers import MetaAudioSerializer, AddToLikedAudioSerializer, AddToStarredAudioSerializer
from common.apps.gallery.models import Audio
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse

@extend_schema(
    responses={200: MetaAudioSerializer},
    description="Retrieve the current user's MetaAudio object, including liked and starred audios. Creates one if it does not exist."
)
class MetaAudioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        meta_audio, created = MetaAudio.objects.get_or_create(user=request.user)
        serializer = MetaAudioSerializer(meta_audio)
        return Response(serializer.data)

@extend_schema(
    request=AddToLikedAudioSerializer,
    responses={200: OpenApiResponse(description='Audio added to liked.'), 403: OpenApiResponse(description='Permission denied.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Add an audio to the user's liked audios. Only public or self-uploaded audios can be liked."
)
class AddToLikedAudioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToLikedAudioSerializer(data=request.data)
        if serializer.is_valid():
            audio_id = serializer.validated_data['audio_id']
            audio = Audio.objects.get(id=audio_id)
            meta_audio, created = MetaAudio.objects.get_or_create(user=request.user)
            if audio.view == 'public' or audio.uploaded_by == request.user:
                meta_audio.liked_audios.add(audio)
                return Response({'status': 'audio added to liked'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'You do not have permission to like this audio'}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=AddToLikedAudioSerializer,
    responses={200: OpenApiResponse(description='Audio removed from liked.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Remove an audio from the user's liked audios."
)
class RemoveFromLikedAudioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToLikedAudioSerializer(data=request.data)
        if serializer.is_valid():
            audio_id = serializer.validated_data['audio_id']
            audio = Audio.objects.get(id=audio_id)
            meta_audio, created = MetaAudio.objects.get_or_create(user=request.user)
            meta_audio.liked_audios.remove(audio)
            return Response({'status': 'audio removed from liked'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=AddToStarredAudioSerializer,
    responses={200: OpenApiResponse(description='Audio added to starred.'), 403: OpenApiResponse(description='Permission denied.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Add an audio to the user's starred audios. Only public or self-uploaded audios can be starred."
)
class AddToStarredAudioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToStarredAudioSerializer(data=request.data)
        if serializer.is_valid():
            audio_id = serializer.validated_data['audio_id']
            audio = Audio.objects.get(id=audio_id)
            meta_audio, created = MetaAudio.objects.get_or_create(user=request.user)
            if audio.view == 'public' or audio.uploaded_by == request.user:
                meta_audio.starred_audios.add(audio)
                return Response({'status': 'audio added to starred'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'You do not have permission to star this audio'}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=AddToStarredAudioSerializer,
    responses={200: OpenApiResponse(description='Audio removed from starred.'), 400: OpenApiResponse(description='Invalid input.')},
    description="Remove an audio from the user's starred audios."
)
class RemoveFromStarredAudioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToStarredAudioSerializer(data=request.data)
        if serializer.is_valid():
            audio_id = serializer.validated_data['audio_id']
            audio = Audio.objects.get(id=audio_id)
            meta_audio, created = MetaAudio.objects.get_or_create(user=request.user)
            meta_audio.starred_audios.remove(audio)
            return Response({'status': 'audio removed from starred'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 