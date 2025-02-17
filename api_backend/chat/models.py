from django.db import models
from django.conf import settings
from django.utils import timezone

class Chat(models.Model):
    CHAT_TYPE_CHOICES = [
        ('private', 'Личный чат'),
        ('group', 'Групповой чат')
    ]
    chat_type = models.CharField(max_length=10, choices=CHAT_TYPE_CHOICES, verbose_name='Тип чата')
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Название чата')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name or f"Чат {self.id}"

class Participant(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='participants', verbose_name='Чат')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    joined_at = models.DateTimeField(default=timezone.now, verbose_name='Дата присоединения')
    last_read_at = models.DateTimeField(null=True, blank=True, verbose_name='Последнее прочтение')

    class Meta:
        verbose_name = 'Участник чата'
        verbose_name_plural = 'Участники чатов'
        unique_together = ('chat', 'user')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user} в чате {self.chat}"

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages', verbose_name='Чат')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Отправитель')
    content = models.TextField(verbose_name='Содержание')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата отправки')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['-created_at']

    def __str__(self):
        return f"Сообщение от {self.sender} в чате {self.chat}"
