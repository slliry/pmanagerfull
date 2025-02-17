from django.core.cache import cache
from django.conf import settings
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MessageCache:
    CACHE_PREFIX = "chat_messages:"
    UNREAD_PREFIX = "unread_messages:"
    PARTICIPANTS_PREFIX = "chat_participants:"
    CACHE_TIMEOUT = 900  # 15 минут = 900 секунд

    @classmethod
    def get_cache_key(cls, chat_id):
        key = f"{cls.CACHE_PREFIX}{chat_id}"
        logger.debug(f"Generated cache key: {key}")
        return key
    
    @classmethod
    def get_unread_key(cls, user_id):
        return f"{cls.UNREAD_PREFIX}{user_id}"

    @classmethod
    def get_participants_key(cls, chat_id):
        return f"{cls.PARTICIPANTS_PREFIX}{chat_id}"

    @classmethod
    def cache_message(cls, chat_id, user_id, message_text):
        """Cache a new message"""
        try:
            cache_key = cls.get_cache_key(chat_id)
            message_data = {
                'user_id': user_id,
                'message': message_text,
                'timestamp': datetime.now().isoformat(),
                'is_persisted': False,
                'read_by': []
            }
            
            # Get existing messages or initialize new list
            cached_messages = cache.get(cache_key) or []
            cached_messages.append(message_data)
            cache.set(cache_key, cached_messages, cls.CACHE_TIMEOUT)
            
            # Получаем список участников из кэша
            participants_key = cls.get_participants_key(chat_id)
            participant_ids = cache.get(participants_key) or []
            
            # Добавляем сообщение в список непрочитанных для всех участников
            for participant_id in participant_ids:
                if participant_id != user_id:  # Не добавляем для отправителя
                    unread_key = cls.get_unread_key(participant_id)
                    unread_messages = cache.get(unread_key) or {}
                    
                    if str(chat_id) not in unread_messages:
                        unread_messages[str(chat_id)] = []
                    
                    unread_messages[str(chat_id)].append({
                        'message_id': len(cached_messages) - 1,
                        'sender_id': user_id,
                        'chat_id': chat_id,
                        'message': message_text,
                        'timestamp': message_data['timestamp']
                    })
                    
                    cache.set(unread_key, unread_messages, cls.CACHE_TIMEOUT)
            
            logger.info(f"Successfully cached message for chat {chat_id}")
            return message_data
            
        except Exception as e:
            logger.error(f"Error caching message: {str(e)}")
            raise

    @classmethod
    def get_cached_messages(cls, chat_id):
        """Get all cached messages for a chat"""
        try:
            cache_key = cls.get_cache_key(chat_id)
            messages = cache.get(cache_key) or []
            logger.info(f"Retrieved {len(messages)} messages from cache for chat {chat_id}")
            return messages
        except Exception as e:
            logger.error(f"Error retrieving cached messages: {str(e)}")
            return []

    @classmethod
    def persist_messages(cls, chat_id):
        """Move cached messages to PostgreSQL"""
        from .models import Message, Chat
        from django.db import transaction
        
        try:
            cache_key = cls.get_cache_key(chat_id)
            messages = cls.get_cached_messages(chat_id)
            
            if not messages:
                logger.info(f"No messages to persist for chat {chat_id}")
                return []
            
            logger.info(f"Starting persistence of {len(messages)} messages for chat {chat_id}")
            
            # Создаем сообщения в базе данных в одной транзакции
            with transaction.atomic():
                chat = Chat.objects.get(id=chat_id)
                persisted_messages = []
                
                for msg_data in messages:
                    if not msg_data.get('is_persisted'):
                        try:
                            message = Message.objects.create(
                                chat=chat,
                                sender_id=msg_data['user_id'],
                                content=msg_data['message'],
                                created_at=datetime.fromisoformat(msg_data['timestamp'])
                            )
                            msg_data['is_persisted'] = True
                            persisted_messages.append(message)
                            logger.info(f"Successfully persisted message {message.id} for chat {chat_id}")
                        except Exception as e:
                            logger.error(f"Error persisting individual message: {str(e)}")
                            continue
                
                # Обновляем кэш с отметками о сохранении
                if persisted_messages:
                    cache.set(cache_key, messages, cls.CACHE_TIMEOUT)
                    logger.info(f"Successfully persisted {len(persisted_messages)} messages for chat {chat_id}")
                
                return persisted_messages
            
        except Exception as e:
            logger.error(f"Error in persist_messages: {str(e)}")
            return []

    @classmethod
    def clear_chat_cache(cls, chat_id):
        """Clear cached messages for a chat"""
        try:
            cache_key = cls.get_cache_key(chat_id)
            cache.delete(cache_key)
            logger.info(f"Cleared cache for chat {chat_id}")
        except Exception as e:
            logger.error(f"Error clearing chat cache: {str(e)}")

    @classmethod
    def mark_messages_as_read(cls, chat_id, user_id):
        """Отметить все сообщения в чате как прочитанные для пользователя"""
        try:
            unread_key = cls.get_unread_key(user_id)
            unread_messages = cache.get(unread_key) or {}
            
            if str(chat_id) in unread_messages:
                del unread_messages[str(chat_id)]
                cache.set(unread_key, unread_messages, cls.CACHE_TIMEOUT)
                logger.info(f"Marked all messages as read in chat {chat_id} for user {user_id}")
            
            # Также отмечаем сообщения как прочитанные в кэше чата
            cache_key = cls.get_cache_key(chat_id)
            cached_messages = cache.get(cache_key) or []
            
            for message in cached_messages:
                if user_id not in message.get('read_by', []):
                    message.setdefault('read_by', []).append(user_id)
            
            cache.set(cache_key, cached_messages, cls.CACHE_TIMEOUT)
            
        except Exception as e:
            logger.error(f"Error marking messages as read: {str(e)}")
            raise

    @classmethod
    def get_unread_messages(cls, user_id):
        """Получить все непрочитанные сообщения для пользователя"""
        try:
            unread_key = cls.get_unread_key(user_id)
            unread_messages = cache.get(unread_key) or {}
            
            # Форматируем для удобного использования в уведомлениях
            result = []
            for chat_id, messages in unread_messages.items():
                for message in messages:
                    result.append({
                        'chat_id': chat_id,
                        'message': message['message'],
                        'sender_id': message['sender_id'],
                        'timestamp': message['timestamp']
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting unread messages: {str(e)}")
            return []

    @classmethod
    def get_unread_count(cls, user_id):
        """Получить количество непрочитанных сообщений для пользователя"""
        try:
            unread_messages = cls.get_unread_messages(user_id)
            return len(unread_messages)
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0
