from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'text', 'timestamp')
    can_delete = False

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'buyer', 'created_at')
    search_fields = ('seller__name', 'buyer__full_name')
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    # ✅ Use the new 'get_sender' method in the display list
    list_display = ('id', 'conversation', 'get_sender', 'text', 'timestamp')
    list_filter = ('timestamp', 'sender_content_type')
    search_fields = ('text',)

    @admin.display(description='Sender') # Sets the column header title
    def get_sender(self, obj):
        """
        This method returns the string representation of the sender object.
        """
        return obj.sender