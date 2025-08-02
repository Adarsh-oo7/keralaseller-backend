# models.py
from django.db import models
from django.conf import settings

class Conversation(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_conversations')
    buyer = models.ForeignKey('users.Buyer', on_delete=models.CASCADE, related_name='buyer_conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation between {self.seller} and {self.buyer}"

class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender_id = models.PositiveIntegerField()
    sender_type = models.CharField(max_length=10, choices=[('seller', 'Seller'), ('buyer', 'Buyer')])
    
    # Message content
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    video = models.FileField(upload_to='chat_videos/', blank=True, null=True)
    audio = models.FileField(upload_to='chat_audio/', blank=True, null=True)
    
    # File metadata
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)  # in bytes
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.message_type.title()} message from {self.sender_type} {self.sender_id} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        # Auto-detect message type based on uploaded content
        if self.image:
            self.message_type = 'image'
        elif self.video:
            self.message_type = 'video'
        elif self.audio:
            self.message_type = 'audio'
        else:
            self.message_type = 'text'
        
        # Set file metadata
        if self.image:
            self.file_name = self.image.name
            self.file_size = self.image.size
        elif self.video:
            self.file_name = self.video.name
            self.file_size = self.video.size
        elif self.audio:
            self.file_name = self.audio.name
            self.file_size = self.audio.size
            
        super().save(*args, **kwargs)

