from rest_framework import viewsets, generics, permissions, pagination
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.db import IntegrityError
from .models import Chat, Message, Participant
from .serializers import ChatSerializer, MessageSerializer, ParticipantSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .cache import MessageCache
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Получаем только те чаты, в которых пользователь является участником
        return Chat.objects.filter(participants__user=self.request.user).distinct()

    def perform_create(self, serializer):
        chat = serializer.save()
        user = self.request.user

        # Проверяем, является ли пользователь уже участником чата
        if not Participant.objects.filter(chat=chat, user=user).exists():
            try:
                Participant.objects.create(chat=chat, user=user)
            except IntegrityError:
                raise ValidationError("Участник уже добавлен в чат.")

class MessagePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MessagePagination

    def get_queryset(self):
        chat_id = self.request.query_params.get('chat_id')
        if not chat_id:
            return Message.objects.none()

        # Проверяем, является ли пользователь участником чата
        if not Participant.objects.filter(chat_id=chat_id, user=self.request.user).exists():
            return Message.objects.none()

        return Message.objects.filter(
            chat_id=chat_id
        ).select_related('sender').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class MessageListView(ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MessagePagination

    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        
        # 1. Получаем сообщения из базы данных
        messages_from_db = Message.objects.filter(
            chat_id=chat_id
        ).order_by('-created_at')
        
        # 2. Получаем сообщения из кэша
        from .cache import MessageCache
        cached_messages = MessageCache.get_cached_messages(chat_id)
        
        # 3. Отмечаем все сообщения как прочитанные для текущего пользователя
        MessageCache.mark_messages_as_read(chat_id, self.request.user.id)
        
        # 4. Конвертируем кэшированные сообщения в формат, совместимый с сообщениями из БД
        from django.utils.timezone import datetime, make_aware
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        cached_message_objects = []
        for msg in cached_messages:
            if not msg.get('is_persisted'):  # Берем только те, которых еще нет в БД
                # Преобразуем naive datetime в aware datetime
                created_at = datetime.fromisoformat(msg['timestamp'])
                if created_at.tzinfo is None:
                    created_at = make_aware(created_at)
                    
                cached_message_objects.append(Message(
                    chat_id=chat_id,
                    sender=User.objects.get(id=msg['user_id']),
                    content=msg['message'],  # В базе это content, но в API будет message
                    created_at=created_at
                ))
        
        # 5. Объединяем сообщения из БД и кэша
        from itertools import chain
        all_messages = list(chain(messages_from_db, cached_message_objects))
        # Сортируем по дате создания (от новых к старым)
        all_messages.sort(key=lambda x: x.created_at, reverse=True)
        
        return all_messages

class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_messages(request):
    """
    Получить список непрочитанных сообщений для текущего пользователя
    """
    unread_messages = MessageCache.get_unread_messages(request.user.id)
    return Response({
        'unread_messages': unread_messages,
        'total_count': len(unread_messages)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_messages_read(request, chat_id):
    """
    Отметить все сообщения в чате как прочитанные
    """
    MessageCache.mark_messages_as_read(chat_id, request.user.id)
    return Response({'status': 'success'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    """
    Получить общее количество непрочитанных сообщений
    """
    count = MessageCache.get_unread_count(request.user.id)
    return Response({'unread_count': count})
