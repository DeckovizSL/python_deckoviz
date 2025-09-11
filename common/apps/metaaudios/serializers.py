from rest_framework import serializers
from .models import MetaAudio
from common.apps.gallery.serializers import AudioSerializer

class MetaAudioSerializer(serializers.ModelSerializer):
    liked_audios = AudioSerializer(many=True, read_only=True)
    starred_audios = AudioSerializer(many=True, read_only=True)

    class Meta:
        model = MetaAudio
        fields = ['id', 'user', 'liked_audios', 'starred_audios']

class AddToLikedAudioSerializer(serializers.Serializer):
    audio_id = serializers.UUIDField()

    def validate_audio_id(self, value):
        from common.apps.gallery.models import Audio
        if not Audio.objects.filter(id=value).exists():
            raise serializers.ValidationError("Audio does not exist.")
        return value

class AddToStarredAudioSerializer(serializers.Serializer):
    audio_id = serializers.UUIDField()

    def validate_audio_id(self, value):
        from common.gallery.models import Audio
        if not Audio.objects.filter(id=value).exists():
            raise serializers.ValidationError("Audio does not exist.")
        return value 