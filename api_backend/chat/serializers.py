from rest_framework import serializers
from .models import Chat, Participant, Message
from accounts.models import User

class UserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id')
    profile_type = serializers.CharField(read_only=True)
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    photo_company = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['user_id', 'email', 'profile_type', 'first_name', 'last_name', 'company_name', 'photo', 'photo_company']

    def get_first_name(self, obj):
        if hasattr(obj, 'physical_profile') and obj.physical_profile:
            return obj.physical_profile.first_name
        return None

    def get_last_name(self, obj):
        if hasattr(obj, 'physical_profile') and obj.physical_profile:
            return obj.physical_profile.last_name
        return None

    def get_company_name(self, obj):
        if hasattr(obj, 'legal_profile') and obj.legal_profile:
            return obj.legal_profile.company_name
        return None

    def get_photo(self, obj):
        request = self.context.get('request')
        if not request:
            return None

        if obj.profile_type == 'physical' and hasattr(obj, 'physical_profile'):
            if obj.physical_profile.photo:
                return request.build_absolute_uri(obj.physical_profile.photo.url)
        return None

    def get_photo_company(self, obj):
        request = self.context.get('request')
        if not request:
            return None

        if obj.profile_type == 'legal' and hasattr(obj, 'legal_profile'):
            if obj.legal_profile.photo_company:
                return request.build_absolute_uri(obj.legal_profile.photo_company.url)
        return None

class ParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(source='user', queryset=User.objects.all(), write_only=True)

    class Meta:
        model = Participant
        fields = ['id', 'user', 'user_id', 'joined_at']

class ChatSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    ordered_participants = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    companion = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'chat_type', 'name', 'participants', 'ordered_participants', 
                 'created_at', 'last_message', 'unread_count', 'companion']

    def get_last_message(self, obj):
        last_message = obj.messages.first()  # Используем ordering из Meta класса модели Message
        if last_message:
            return {
                'content': last_message.content,
                'sender': last_message.sender.email,
                'sender_id': last_message.sender.id,
                'created_at': last_message.created_at
            }
        return None

    def get_unread_count(self, obj):
        user = self.context['request'].user
        # В будущем здесь можно добавить подсчет непрочитанных сообщений
        return 0

    def get_ordered_participants(self, obj):
        request = self.context.get('request')
        if not request or obj.chat_type != 'private':
            return None

        current_user = request.user
        participants = list(obj.participants.all())
        
        # Сортируем участников так, чтобы текущий пользователь был первым (id: 0)
        participants.sort(key=lambda x: x.user.id != current_user.id)
        
        return ParticipantSerializer(
            participants, 
            many=True, 
            context=self.context
        ).data

    def get_companion(self, obj):
        """Получаем данные собеседника для приватного чата"""
        request = self.context.get('request')
        if not request or obj.chat_type != 'private':
            return None

        current_user = request.user
        companion = obj.participants.exclude(user=current_user).first()
        
        if not companion:
            return None

        companion_user = companion.user
        
        # Формируем данные о собеседнике в зависимости от типа профиля
        if companion_user.profile_type == 'physical':
            if hasattr(companion_user, 'physical_profile'):
                profile = companion_user.physical_profile
                return {
                    'id': companion_user.id,
                    'full_name': f"{profile.last_name} {profile.first_name}",
                    'photo': self.get_photo_url(request, profile.photo) if profile.photo else None,
                    'profile_type': 'physical'
                }
        else:
            if hasattr(companion_user, 'legal_profile'):
                profile = companion_user.legal_profile
                return {
                    'id': companion_user.id,
                    'full_name': profile.company_name,
                    'photo': self.get_photo_url(request, profile.photo_company) if profile.photo_company else None,
                    'profile_type': 'legal'
                }
        return None

    def get_photo_url(self, request, photo):
        if photo:
            return request.build_absolute_uri(photo.url)
        return None

    def create(self, validated_data):
        chat = Chat.objects.create(**validated_data)
        user = self.context['request'].user

        # Проверяем существование участника перед созданием
        if not Participant.objects.filter(chat=chat, user=user).exists():
            Participant.objects.create(chat=chat, user=user)

        return chat

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    message = serializers.CharField(source='content')  # Переименовываем content в message
    created_at = serializers.SerializerMethodField()
    is_own = serializers.SerializerMethodField()  # Добавляем поле is_own

    class Meta:
        model = Message
        fields = ['sender', 'sender_id', 'message', 'created_at', 'is_own']
        read_only_fields = ['sender', 'sender_id', 'created_at', 'is_own']

    def get_created_at(self, obj):
        # Форматируем время в удобный вид
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')

    def get_is_own(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.sender_id == request.user.id
        return False
