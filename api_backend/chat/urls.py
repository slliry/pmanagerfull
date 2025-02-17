from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatViewSet, MessageViewSet, ParticipantViewSet,
    get_unread_messages, get_unread_count, mark_messages_read,
    MessageListView
)

router = DefaultRouter()
router.register(r'chats', ChatViewSet)
router.register(r'messages', MessageViewSet, basename='message')  
router.register(r'participants', ParticipantViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # URLs для непрочитанных сообщений
    path('unread/', get_unread_messages, name='get_unread_messages'),
    path('unread/count/', get_unread_count, name='get_unread_count'),
    path('chat/<int:chat_id>/read/', mark_messages_read, name='mark_messages_read'),
    
    path('chats/<int:chat_id>/messages/', MessageListView.as_view(), name='chat-messages'),
]
