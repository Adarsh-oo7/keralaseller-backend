from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from users.models import Seller, Buyer

class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if isinstance(user, Seller):
            return Conversation.objects.filter(seller=user).order_by('-created_at')
        elif isinstance(user, Buyer):
            return Conversation.objects.filter(buyer=user).order_by('-created_at')
        return Conversation.objects.none()

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        user = self.request.user

        # Build query to find conversations where user participates
        conversations = Conversation.objects.filter(id=conversation_id)
        
        # Filter based on user type
        user_conversations = conversations.filter(
            Q(seller=user) |  # User is seller
            Q(buyer__user=user)  # User is related to buyer (adjust based on your model)
        )
        
        # Alternative if your Buyer model structure is different:
        # user_conversations = conversations.filter(seller=user)
        # if hasattr(user, 'buyer_profile'):  # or whatever the relationship is
        #     user_conversations = user_conversations.union(
        #         conversations.filter(buyer=user.buyer_profile)
        #     )

        if user_conversations.exists():
            conversation = user_conversations.first()
            return Message.objects.filter(conversation=conversation).order_by('timestamp')
        
        return Message.objects.none()

class SendMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        user = request.user
        try:
            conversation = Conversation.objects.get(
                Q(id=conversation_id),
                Q(seller=user) | Q(buyer=user)
            )
        except Conversation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        text = request.data.get('text')
        if not text:
            return Response({'error': 'Message text is required.'}, status=status.HTTP_400_BAD_REQUEST)

        Message.objects.create(
            conversation=conversation,
            sender=user,
            text=text
        )
        return Response(status=status.HTTP_201_CREATED)