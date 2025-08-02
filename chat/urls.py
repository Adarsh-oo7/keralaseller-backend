# In chat/urls.py
from django.urls import path
from .views import ConversationListView, MessageListView, SendMessageView

urlpatterns = [
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:conversation_id>/messages/', MessageListView.as_view(), name='message-list'),
    path('conversations/<int:conversation_id>/send/', SendMessageView.as_view(), name='send-message'),
]