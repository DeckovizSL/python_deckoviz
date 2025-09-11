from rest_framework import serializers
from .models import Mode, UserMode, Session, Music
from common.apps.gallery.models import Collection, Audio
from common.apps.gallery.serializers import CollectionSerializer, AudioSerializer

class MusicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Music
        fields = '__all__'

class ModeSerializer(serializers.ModelSerializer):
    admin_collections = CollectionSerializer(many=True, read_only=True)
    admin_curations = CollectionSerializer(many=True, read_only=True)
    admin_music = MusicSerializer(many=True, read_only=True)

    class Meta:
        model = Mode
        fields = ('id', 'name', 'admin_collections', 'admin_curations', 'admin_music')

class UserModeSerializer(serializers.ModelSerializer):
    user_collections = CollectionSerializer(many=True, read_only=True)
    user_music = AudioSerializer(many=True, read_only=True)
    mode = ModeSerializer(read_only=True)

    class Meta:
        model = UserMode
        fields = ('id', 'user', 'mode', 'user_collections', 'user_music')

class UserModeUpdateSerializer(serializers.ModelSerializer):
    user_collections = serializers.PrimaryKeyRelatedField(
        queryset=Collection.objects.all(),
        many=True,
        required=False
    )
    user_music = serializers.PrimaryKeyRelatedField(
        queryset=Audio.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = UserMode
        fields = ('user_collections', 'user_music')

    def update(self, instance, validated_data):
        user_collections = validated_data.pop('user_collections', None)
        user_music = validated_data.pop('user_music', None)

        # Add collections instead of replacing
        if user_collections is not None:
            for collection in user_collections:
                instance.user_collections.add(collection)

        # Add music instead of replacing
        if user_music is not None:
            for music in user_music:
                instance.user_music.add(music)

        instance.save()
        return instance

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'
