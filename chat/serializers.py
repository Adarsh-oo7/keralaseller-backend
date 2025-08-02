# serializers.py
from rest_framework import serializers
from .models import Conversation, Message
from users.models import Buyer

class BuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = ['id', 'full_name', 'email']

class MessageSerializer(serializers.ModelSerializer):
    # Add URL fields for media files
    image_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    audio_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'sender_id', 'sender_type', 'message_type', 
            'text', 'image', 'video', 'audio',
            'image_url', 'video_url', 'audio_url',
            'file_name', 'file_size', 'file_size_mb',
            'timestamp'
        ]

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None

    def get_video_url(self, obj):
        if obj.video:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video.url)
        return None

    def get_audio_url(self, obj):
        if obj.audio:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.audio.url)
        return None

    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return None

class ConversationSerializer(serializers.ModelSerializer):
    buyer = BuyerSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'seller', 'buyer']