# views.py
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from users.models import Seller, Buyer

class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Get conversations where user is the seller
        seller_conversations = Conversation.objects.filter(seller=user)
        
        # Check if the current user is a Buyer instance
        if isinstance(user, Buyer):
            buyer_conversations = Conversation.objects.filter(buyer=user)
            return seller_conversations.union(buyer_conversations).order_by('-created_at')
        else:
            return seller_conversations.order_by('-created_at')

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        user = self.request.user

        conversation = None
        
        try:
            if isinstance(user, Buyer):
                conversation = Conversation.objects.get(
                    Q(id=conversation_id),
                    Q(seller=user) | Q(buyer=user)
                )
            else:
                conversation = Conversation.objects.get(
                    id=conversation_id, 
                    seller=user
                )
        except Conversation.DoesNotExist:
            return Message.objects.none()

        if conversation:
            return Message.objects.filter(conversation=conversation).order_by('timestamp')
        
        return Message.objects.none()

class SendMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Enable file upload

    def post(self, request, conversation_id):
        user = request.user
        
        # Check if user has access to this conversation
        conversation = None
        sender_type = None
        sender_id = None
        
        try:
            if isinstance(user, Buyer):
                conversation = Conversation.objects.get(
                    Q(id=conversation_id),
                    Q(seller=user) | Q(buyer=user)
                )
                if conversation.seller == user:
                    sender_type = 'seller'
                    sender_id = user.id
                else:
                    sender_type = 'buyer'
                    sender_id = user.id
            else:
                conversation = Conversation.objects.get(
                    id=conversation_id, 
                    seller=user
                )
                sender_type = 'seller'
                sender_id = user.id
        except Conversation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        # Get message content
        text = request.data.get('text', '')
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        audio = request.FILES.get('audio')
        
        # Validate that at least one type of content is provided
        if not text and not image and not video and not audio:
            return Response({
                'error': 'At least one of text, image, video, or audio is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate file sizes (adjust limits as needed)
        max_file_size = 50 * 1024 * 1024  # 50MB
        
        for file_field, file_obj in [('image', image), ('video', video), ('audio', audio)]:
            if file_obj and file_obj.size > max_file_size:
                return Response({
                    'error': f'{file_field.title()} file size must be less than 50MB.'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender_id=sender_id,
            sender_type=sender_type,
            text=text,
            image=image,
            video=video,
            audio=audio
        )
        
        # Return the created message
        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)