from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Mode, UserMode, Session, Music
from common.apps.gallery.models import Collection, Audio
from .serializers import ModeSerializer, UserModeSerializer, SessionSerializer, UserModeUpdateSerializer
from django.shortcuts import get_object_or_404

class ModeListView(generics.ListAPIView):
    queryset = Mode.objects.all()
    serializer_class = ModeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Eager load related fields to optimize performance
        return Mode.objects.prefetch_related('admin_collections', 'admin_music').all()

class UserModeDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserModeUpdateSerializer
        return UserModeSerializer

    def get_object(self):
        mode_id = self.kwargs.get('mode_id')
        mode = get_object_or_404(Mode, id=mode_id)
        # Get or create a UserMode instance for the current user and the specified mode
        obj, created = UserMode.objects.get_or_create(user=self.request.user, mode=mode)
        return obj

class UserModeCollectionRemoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, mode_id, collection_id):
        # Get the user's specific settings for the given mode
        user_mode = get_object_or_404(UserMode, user=request.user, mode_id=mode_id)
        
        # Get the collection to be removed
        collection = get_object_or_404(Collection, id=collection_id)
        
        # Check if the collection is in the user's list
        if collection in user_mode.user_collections.all():
            user_mode.user_collections.remove(collection)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"detail": "Collection not found in this mode for the user."}, status=status.HTTP_404_NOT_FOUND)

class UserModeMusicRemoveView(APIView):
    """
    Delete specific audio/music from a user's mode.
    Note: This view handles Audio objects, not Music objects, since the UserMode.user_music 
    field references Audio from the gallery app, which is what gets added via PUT requests.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, mode_id, audio_id=None, music_id=None):
        user_mode = get_object_or_404(UserMode, user=request.user, mode_id=mode_id)
        # Support both audio_id and music_id for backward compatibility
        item_id = audio_id or music_id
        audio = get_object_or_404(Audio, id=item_id)
        if audio in user_mode.user_music.all():
            user_mode.user_music.remove(audio)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"detail": "Music not found in this mode for the user."}, status=status.HTTP_404_NOT_FOUND)

class SessionCreateView(generics.CreateAPIView):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Associate the session with the authenticated user
        serializer.save(user=self.request.user)
