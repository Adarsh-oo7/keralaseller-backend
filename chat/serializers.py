from rest_framework import serializers
from .models import Conversation, Message
from users.models import Buyer, Seller

class BuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = ['id', 'full_name', 'email']

# A simple serializer to represent the sender (either a Seller or a Buyer)
class SenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller # We can use Seller as a base, or create a more generic one
        fields = ['id', 'name'] # Assuming Seller has a 'name' field

    def to_representation(self, instance):
        # Override to handle both Seller and Buyer types
        if isinstance(instance, Seller):
            return {'id': instance.id, 'name': instance.name, 'type': 'seller'}
        elif isinstance(instance, Buyer):
            return {'id': instance.id, 'name': instance.full_name, 'type': 'buyer'}
        return super().to_representation(instance)

class MessageSerializer(serializers.ModelSerializer):
    # Use the new SenderSerializer to represent the generic sender
    sender = SenderSerializer(read_only=True)
    
    # These methods are a great way to provide full URLs
    image_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        # The fields list should only contain what's on the model or defined here
        fields = [
            'id', 'sender', 'text', 'image', 'video', 
            'image_url', 'video_url', 'timestamp'
        ]
        # Make the upload fields write-only
        extra_kwargs = {
            'image': {'write_only': True, 'required': False},
            'video': {'write_only': True, 'required': False},
        }

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_video_url(self, obj):
        request = self.context.get('request')
        if obj.video and hasattr(obj.video, 'url'):
            return request.build_absolute_uri(obj.video.url)
        return None

class ConversationSerializer(serializers.ModelSerializer):
    buyer = BuyerSerializer(read_only=True)
    # You could also add 'last_message' here if needed
    # last_message = MessageSerializer(read_only=True) 

    class Meta:
        model = Conversation
        fields = ['id', 'seller', 'buyer']