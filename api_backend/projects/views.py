from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import ProjectComplexity, Project, ProjectResponse, ProjectMember, ProjectTemplate
from .serializers import (
    ProjectComplexitySerializer,
    ProjectSerializer,
    ProjectResponseSerializer,
    ProjectMemberSerializer,
    ProjectTemplateSerializer
)
from chat.models import Chat, Participant
from django.db import transaction
import logging
from django.db import IntegrityError
from django.core import serializers

logger = logging.getLogger(__name__)

class IsGIPOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(request.user, 'physical_profile') and request.user.physical_profile.is_gip

class ProjectComplexityViewSet(viewsets.ModelViewSet):
    queryset = ProjectComplexity.objects.all()
    serializer_class = ProjectComplexitySerializer
    permission_classes = [permissions.IsAuthenticated, IsGIPOrReadOnly]
    
class ProjectTemplateViewSet(viewsets.ModelViewSet):
    queryset = ProjectTemplate.objects.all()
    serializer_class = ProjectTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsGIPOrReadOnly]

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'physical_profile'):
            if user.physical_profile.is_gip:
                # ГИП видит все свои проекты
                return Project.objects.filter(gip=user.physical_profile)
            else:
                # Обычные пользователи видят проекты на аукционе, соответствующие их специальности
                return Project.objects.filter(
                    status='auction', 
                    required_specialties=user.physical_profile.specialty
                )
        return Project.objects.none()

    def perform_create(self, serializer):
        serializer.save(
            gip=self.request.user.physical_profile,
            project_office=self.request.user.physical_profile.project_office
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        if 'status' in serializer.validated_data:
            if instance.status == 'draft' and serializer.validated_data['status'] == 'auction':
                # Создание чатов при переводе в аукцион
                group_chat = Chat.objects.create(
                    chat_type='group',
                    name=f'Проект: {instance.name}'
                )
                instance.chat = group_chat
                
                Participant.objects.create(chat=group_chat, user=instance.gip.user)
                
                po_chat = Chat.objects.create(
                    chat_type='private',
                    name=f'ГИП - ПО: {instance.name}'
                )
                Participant.objects.create(chat=po_chat, user=instance.gip.user)
                Participant.objects.create(chat=po_chat, user=instance.project_office.user)
                
                client_chat = Chat.objects.create(
                    chat_type='private',
                    name=f'Заказчик - ПО: {instance.name}'
                )
                Participant.objects.create(chat=client_chat, user=instance.project_office.user)
                Participant.objects.create(chat=client_chat, user=instance.client.user)

            elif instance.status == 'auction' and serializer.validated_data['status'] == 'in_progress':
                 if not hasattr(request.user, 'physical_profile') or instance.gip != request.user.physical_profile:
                    raise permissions.PermissionDenied("Только ГИП проекта может начать проект")
        
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_to_auction(self, request, uuid=None):
        project = self.get_object()
        if project.status != 'draft':
            return Response(
                {"error": "Только проект в статусе 'draft' может быть отправлен на аукцион"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        project.status = 'auction'
        project.save()
        
        # Создание чатов при переводе в аукцион
        group_chat = Chat.objects.create(
            chat_type='group',
            name=f'Проект: {project.name}'
        )
        project.chat = group_chat
        project.save()
        
        Participant.objects.create(chat=group_chat, user=project.gip.user)
        
        po_chat = Chat.objects.create(
            chat_type='private',
            name=f'ГИП - ПО: {project.name}'
        )
        Participant.objects.create(chat=po_chat, user=project.gip.user)
        Participant.objects.create(chat=po_chat, user=project.project_office.user)
        
        client_chat = Chat.objects.create(
            chat_type='private',
            name=f'Заказчик - ПО: {project.name}'
        )
        Participant.objects.create(chat=client_chat, user=project.project_office.user)
        Participant.objects.create(chat=client_chat, user=project.client.user)

        serializer = self.get_serializer(project)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def start_project(self, request, uuid=None):
        project = self.get_object()
        
        if project.status != 'auction':
            return Response(
                {"error": "Только проект в статусе 'auction' может быть запущен"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not hasattr(request.user, 'physical_profile') or project.gip != request.user.physical_profile:
            raise permissions.PermissionDenied("Только ГИП проекта может начать проект")
        
        project.status = 'in_progress'
        project.save()
        
        serializer = self.get_serializer(project)
        return Response(serializer.data)

class ProjectResponseViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectResponseSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'physical_profile'):
            if user.physical_profile.is_gip:
                return ProjectResponse.objects.filter(project__gip=user.physical_profile)
            else:
                return ProjectResponse.objects.filter(specialist=user.physical_profile)
        return ProjectResponse.objects.none()

    def create(self, request, *args, **kwargs):
        project_uuid = request.query_params.get('project_uuid')
        if not project_uuid:
            return Response(
                {"error": "project_uuid is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(
            data=request.data,
            context={'project_uuid': project_uuid}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        specialist = user.physical_profile
        
        try:
            project = Project.objects.get(uuid=project_uuid)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверки перед созданием
        if project.status != 'auction':
            return Response(
                {"error": "Нельзя откликнуться на проект не на аукционе"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if specialist.specialty not in project.required_specialties.all():
            return Response(
                {"error": "Ваша специальность не соответствует требуемой для проекта"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем существование отклика
        existing_response = ProjectResponse.objects.filter(
            project=project,
            specialist=specialist
        ).first()

        if existing_response:
            logger.info(f"Found existing response: {existing_response.id} with status {existing_response.status}")
            return Response({
                'error': 'Вы уже откликались на этот проект',
                'response_status': existing_response.status
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Создаем новый чат
                chat = Chat.objects.create(
                    chat_type='private',
                    name=f"Чат по проекту {project.name}",
                )

                # Создаем участников чата одним запросом
                participants_to_create = [
                    Participant(chat=chat, user=specialist.user),
                    Participant(chat=chat, user=project.gip.user)
                ]
                
                try:
                    # Используем bulk_create с ignore_conflicts=True
                    Participant.objects.bulk_create(
                        participants_to_create,
                        ignore_conflicts=True
                    )
                except Exception as e:
                    logger.error(f"Error creating participants: {str(e)}")
                    # Если не удалось создать участников, удаляем чат
                    chat.delete()
                    raise

                # Создаем отклик
                response = serializer.save(
                    specialist=specialist,
                    status='pending',
                    chat=chat,
                    project=project
                )

                logger.info(f"Successfully created response {response.id} for project {project.uuid}")
                return Response({
                    'project_uuid': project.uuid,
                    'chat_id': chat.id,
                    'redirect_url': f'/chats/{chat.id}/'
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating response: {str(e)}")
            return Response(
                {"error": "Ошибка при создании отклика. Пожалуйста, попробуйте еще раз."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='accept')
    def accept_response(self, request, uuid=None):
        response = self.get_object()
        if not request.user.physical_profile.is_gip or response.project.gip != request.user.physical_profile:
            raise permissions.PermissionDenied("Только ГИП может принимать отклики")
        
        try:
            with transaction.atomic():
                # Меняем статус отклика
                response.status = 'accepted'
                response.save()
                
                # Создаем участника проекта
                ProjectMember.objects.create(
                    project=response.project,
                    member=response.specialist,
                    role=response.specialist.specialty.name
                )

                # Получаем групповой чат проекта
                project_chat = Chat.objects.get(
                    chat_type='group',
                    project=response.project
                )

                # Добавляем специалиста в групповой чат
                Participant.objects.get_or_create(
                    chat=project_chat,
                    user=response.specialist.user
                )

                return Response({
                    "status": "Отклик принят",
                    "project_chat_id": project_chat.id,
                    "redirect_url": f'/chats/{project_chat.id}/'
                })

        except Chat.DoesNotExist:
            logger.error(f"Group chat not found for project {response.project.id}")
            return Response(
                {"error": "Ошибка: не найден групповой чат проекта"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error accepting response: {str(e)}")
            return Response(
                {"error": "Ошибка при принятии отклика"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_response(self, request, uuid=None):
        response = self.get_object()
        if not request.user.physical_profile.is_gip or response.project.gip != request.user.physical_profile:
            raise permissions.PermissionDenied("Только ГИП может отклонять отклики")
        
        response.status = 'rejected'
        response.save()
        return Response({"status": "Отклик отклонен"})

    @action(detail=True, methods=['delete'])
    def block_chat(self, request, uuid=None):
        response = self.get_object()
        if not request.user.physical_profile.is_gip or response.project.gip != request.user.physical_profile:
            raise permissions.PermissionDenied("Только ГИП может блокировать чаты")
        
        if response.chat:
            response.chat.delete()
            response.chat = None
            response.save()
        
        return Response({"status": "Чат заблокирован"})

class ProjectMemberViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectMemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsGIPOrReadOnly]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'physical_profile'):
            if user.physical_profile.is_gip:
                return ProjectMember.objects.filter(project__gip=user.physical_profile)
            return ProjectMember.objects.filter(
                Q(member=user.physical_profile) | 
                Q(project__members__member=user.physical_profile)
            ).distinct()
        return ProjectMember.objects.none()