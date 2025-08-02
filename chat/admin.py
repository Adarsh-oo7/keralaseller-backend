# admin.py
from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    # ✅ Updated to use the new fields
    readonly_fields = ('sender_id', 'sender_type', 'text', 'timestamp')
    can_delete = False

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'buyer', 'created_at')
    search_fields = ('seller__username', 'buyer__full_name')  # Adjust field names as needed
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    # ✅ Updated to use the new fields and method
    list_display = ('id', 'conversation', 'get_sender_display', 'text', 'timestamp')
    list_filter = ('timestamp', 'sender_type')  # Use sender_type instead of sender_content_type
    search_fields = ('text',)

    @admin.display(description='Sender')
    def get_sender_display(self, obj):
        """
        This method returns a readable representation of the sender.
        """
        return f"{obj.sender_type.title()} (ID: {obj.sender_id})"