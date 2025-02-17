import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.apps import apps
from django.utils import timezone

logger = logging.getLogger(__name__)

def get_models():
    User = get_user_model()
    Chat = apps.get_model('chat', 'Chat')
    Message = apps.get_model('chat', 'Message')
    Participant = apps.get_model('chat', 'Participant')
    return User, Chat, Message, Participant

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.chat_id = self.scope['url_route']['kwargs']['chat_id']
            self.chat_group_name = f'chat_{self.chat_id}'
            self.user = self.scope['user']

            if not self.user.is_authenticated:
                logger.warning(f"Unauthenticated user tried to connect to chat {self.chat_id}")
                await self.close()
                return

            User, Chat, Message, Participant = get_models()
            
            # Проверяем существование чата
            try:
                chat = await database_sync_to_async(Chat.objects.get)(id=self.chat_id)
            except Chat.DoesNotExist:
                logger.error(f"Chat {self.chat_id} does not exist")
                await self.close()
                return
            
            is_participant = await self.check_participant(Participant)
            if not is_participant:
                logger.warning(f"User {self.user.email} is not a participant of chat {self.chat_id}")
                await self.close()
                return

            await self.channel_layer.group_add(
                self.chat_group_name,
                self.channel_name
            )

            # При подключении отмечаем все сообщения как прочитанные
            from .cache import MessageCache
            await database_sync_to_async(MessageCache.mark_messages_as_read)(self.chat_id, self.user.id)

            await self.accept()
            logger.info(f"User {self.user.email} connected to chat {self.chat_id}")
            
        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")
            await self.close()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get('message')
        message_type = data.get('type', 'message')

        logger.debug(f"Received {message_type} from {self.user.email}: {message_content}")

        if message_type == 'read_messages':
            # Отмечаем сообщения как прочитанные
            from .cache import MessageCache
            await database_sync_to_async(MessageCache.mark_messages_as_read)(self.chat_id, self.user.id)
            
            # Отправляем уведомление о прочтении всем участникам
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'messages_read',
                    'user_id': self.user.id,
                    'chat_id': self.chat_id
                }
            )
        elif message_content:
            User, Chat, Message, Participant = get_models()
            message_data = await self.save_message(Chat, Message, message_content)
            
            # Преобразуем timestamp в datetime для форматирования
            from django.utils.timezone import datetime
            created_at = datetime.fromisoformat(message_data['timestamp'])
            
            # Отправляем сообщение через групповую рассылку
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender_id': self.user.id,
                    'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'sender_email': self.user.email
                }
            )
        else:
            logger.warning(f"Empty message received from {self.user.email}")

    async def chat_message(self, event):
        # Определяем, является ли текущий пользователь отправителем
        is_sender = str(event['sender_id']) == str(self.user.id)
        
        # Если это не отправитель, отмечаем сообщение как прочитанное
        if not is_sender:
            from .cache import MessageCache
            await database_sync_to_async(MessageCache.mark_messages_as_read)(self.chat_id, self.user.id)
        
        # Отправляем сообщение с соответствующим флагом is_own
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'created_at': event['created_at'],
            'is_own': is_sender
        }, ensure_ascii=False))

    async def messages_read(self, event):
        """Обработчик события о прочтении сообщений"""
        await self.send(text_data=json.dumps({
            'type': 'messages_read',
            'user_id': event['user_id'],
            'chat_id': event['chat_id']
        }))

    @database_sync_to_async
    def check_participant(self, Participant):
        return Participant.objects.filter(
            chat_id=self.chat_id,
            user=self.user
        ).exists()

    async def save_message(self, Chat, Message, message_content):
        """Save message to cache and database"""
        try:
            # Проверяем существование чата
            try:
                chat = await database_sync_to_async(Chat.objects.get)(id=self.chat_id)
            except Chat.DoesNotExist:
                logger.error(f"Chat {self.chat_id} does not exist")
                raise
            
            # Получаем список участников чата асинхронно
            from .cache import MessageCache
            from django.core.cache import cache
            
            # Обновляем кэш участников чата
            participants_key = MessageCache.get_participants_key(self.chat_id)
            participant_ids = await database_sync_to_async(
                lambda: list(chat.participants.exclude(user_id=self.user.id).values_list('user_id', flat=True))
            )()
            await database_sync_to_async(cache.set)(
                participants_key, 
                participant_ids, 
                MessageCache.CACHE_TIMEOUT
            )
            
            # Сохраняем сообщение в кэш
            message_data = await database_sync_to_async(MessageCache.cache_message)(
                chat_id=self.chat_id,
                user_id=self.user.id,
                message_text=message_content
            )
            
            logger.info(f"Message cached for chat {self.chat_id}")
            return message_data
            
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            raise

    @database_sync_to_async
    def get_message_data(self, message_data):
        return {
            'message': message_data['content'],
            'sender': message_data['sender'].email,
            'sender_id': message_data['sender'].id,
            'timestamp': message_data['created_at'].isoformat()
        }

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )
        logger.info(f"User {self.user.email if self.user.is_authenticated else 'Anonymous'} disconnected from chat {self.chat_id}")
