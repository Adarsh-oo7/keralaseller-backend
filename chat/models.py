from django.db import models
from django.conf import settings

class Conversation(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_conversations')
    buyer = models.ForeignKey('users.Buyer', on_delete=models.CASCADE, related_name='buyer_conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation between {self.seller} and {self.buyer}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    
    # ✅ Simplified sender field - just store the ID and type
    sender_id = models.PositiveIntegerField()  # Store the actual ID
    sender_type = models.CharField(max_length=10, choices=[('seller', 'Seller'), ('buyer', 'Buyer')])
    
    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    video = models.FileField(upload_to='chat_videos/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender_type} {self.sender_id} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
