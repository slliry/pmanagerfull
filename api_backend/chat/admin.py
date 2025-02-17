# admin.py
from django.contrib import admin
from .models import Chat, Message, Participant

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'chat', 'content', 'created_at')
    search_fields = ('content', 'sender__email', 'chat__name')
    list_filter = ('chat', 'sender', 'created_at')
    date_hierarchy = 'created_at'

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat', 'joined_at')
    search_fields = ('user__email', 'chat__name')
    list_filter = ('chat', 'user', 'joined_at')
    date_hierarchy = 'joined_at'
    raw_id_fields = ('user', 'chat')

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
