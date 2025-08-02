from rest_framework import serializers
from .models import Conversation, Message
from users.models import Buyer

class BuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = ['id', 'full_name', 'email']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender', 'text', 'image', 'video', 'timestamp']

class ConversationSerializer(serializers.ModelSerializer):
    buyer = BuyerSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'seller', 'buyer']