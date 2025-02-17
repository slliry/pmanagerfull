from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Folder, File, FolderAccess, FolderActionLog
from projects.models import Project, ProjectMember
from .serializers import FolderSerializer, FileSerializer, FolderAccessSerializer, FolderActionLogSerializer
from django.db.models import Q
from rest_framework.exceptions import ValidationError, PermissionDenied
import logging
import os
from functools import wraps
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings

logger = logging.getLogger(__name__)

def log_folder_action(action_type):
    def decorator(func):
        @wraps(func)
        def wrapper(view_instance, request, *args, **kwargs):
            # Для DELETE получаем и сохраняем информацию об объекте до удаления
            pre_instance = None
            pre_instance_name = None
            pre_instance_type = None
            
            if action_type == 'DELETE':
                try:
                    pre_instance = view_instance.get_object()
                    pre_instance_name = pre_instance.name
                    pre_instance_type = 'папку' if isinstance(pre_instance, Folder) else 'файл'
                except:
                    pass

            # Выполняем действие
            response = func(view_instance, request, *args, **kwargs)
            
            try:
                user = request.user
                project_uuid = kwargs.get('project_uuid')
                project = Project.objects.get(uuid=project_uuid) if project_uuid else None

                # Определяем объект в зависимости от типа действия
                instance = None
                instance_name = None
                
                if action_type == 'DELETE':
                    instance = None  # Объект уже удален
                    instance_name = pre_instance_name
                    object_type = pre_instance_type
                else:
                    if action_type == 'CREATE':
                        if hasattr(response, 'data') and response.data.get('id'):
                            instance = Folder.objects.filter(id=response.data['id']).first()
                    elif action_type == 'UPLOAD':
                        if hasattr(response, 'data') and response.data.get('id'):
                            instance = File.objects.filter(id=response.data['id']).first()
                    elif hasattr(response, 'data') and response.data.get('id'):
                        model = Folder if view_instance.__class__.__name__ == 'FolderViewSet' else File
                        instance = model.objects.filter(id=response.data['id']).first()
                    
                    if instance:
                        instance_name = instance.name
                        object_type = 'папку' if isinstance(instance, Folder) else 'файл'

                # Получаем имя пользователя
                if user.profile_type == 'physical':
                    try:
                        profile = user.physical_profile
                        user_name = f"{profile.last_name} {profile.first_name}"
                        if profile.middle_name:
                            user_name += f" {profile.middle_name}"
                        user_name = user_name.strip()
                    except:
                        user_name = user.email
                elif user.profile_type == 'legal':
                    try:
                        user_name = user.legal_profile.company_name
                    except:
                        user_name = user.email
                else:
                    user_name = user.email

                # Формируем описание действия
                action_types = {
                    'CREATE': 'создал(а)',
                    'UPDATE': 'изменил(а) название',
                    'DELETE': 'удалил(а)',
                    'MOVE': 'переместил(а)',
                    'UPLOAD': 'загрузил(а)',
                    'DOWNLOAD': 'скачал(а)'
                }
                
                action_text = action_types.get(action_type, action_type)
                
                if instance_name:
                    # Для подпапок добавляем информацию о родительской папке
                    if action_type == 'CREATE' and isinstance(instance, Folder) and instance.parent:
                        description = f"{user_name} {action_text} папку '{instance_name}' в папке '{instance.parent.name}'"
                    # Для файлов добавляем информацию о папке
                    elif isinstance(instance, File):
                        description = f"{user_name} {action_text} файл '{instance_name}' в папке '{instance.folder.name}'"
                    else:
                        description = f"{user_name} {action_text} {object_type} '{instance_name}'"
                else:
                    description = f"{user_name} выполнил(а) действие {action_text}"

                # Создаем запись в логе
                log_entry = FolderActionLog.objects.create(
                    user=user,
                    project=project,
                    folder=instance if isinstance(instance, Folder) else None,
                    file=instance if isinstance(instance, File) else None,
                    folder_name=instance_name if pre_instance_type == 'папку' else None,
                    file_name=instance_name if pre_instance_type == 'файл' else None,
                    action_type=action_type,
                    description=description
                )
                logger.info(f"Created log entry: {log_entry}")

            except Exception as e:
                logger.error(f"Ошибка при логировании действия: {str(e)}")
                logger.exception(e)

            return response
        return wrapper
    return decorator

# Create your views here.

class FolderViewSet(viewsets.ModelViewSet):
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Получение списка папок с учетом прав доступа"""
        user = self.request.user
        logger.info(f"Getting folders for user: {user.email}")
        
        queryset = Folder.objects.all()

        # Фильтрация по проекту
        project_uuid = self.request.query_params.get('project', None)
        if project_uuid:
            try:
                project = Project.objects.get(uuid=project_uuid)
                logger.info(f"Found project: {project.name} (UUID: {project.uuid})")
                
                # Проверяем членство в команде через ProjectMember
                is_team_member = ProjectMember.objects.filter(
                    project=project,
                    member__user=user
                ).exists()
                logger.info(f"User is team member: {is_team_member}")
                
                # Проверяем, является ли пользователь ГИПом проекта
                is_gip = project.gip.user == user
                logger.info(f"User is GIP: {is_gip}")
                
                queryset = queryset.filter(project=project)
            except Project.DoesNotExist:
                logger.error(f"Project with UUID {project_uuid} not found")
                raise ValidationError(f"Project with UUID {project_uuid} not found")

        # Проверяем прямые права доступа
        direct_access = FolderAccess.objects.filter(user=user).exists()
        logger.info(f"User has direct folder access: {direct_access}")

        # Проверяем созданные пользователем папки
        created_folders = Folder.objects.filter(created_by=user).exists()
        logger.info(f"User has created folders: {created_folders}")

        # Фильтрация по правам доступа
        queryset = queryset.filter(
            Q(access_rights__user=user) |
            Q(project__members__member__user=user) |  # Проверка через ProjectMember
            Q(project__gip__user=user) |             # Проверка ГИПа
            Q(created_by=user)
        ).distinct()

        return queryset

    def perform_create(self, serializer):
        """Создание новой папки"""
        project_uuid = self.request.data.get('project')
        try:
            project = Project.objects.get(uuid=project_uuid)
        except Project.DoesNotExist:
            raise ValidationError(f"Project with UUID {project_uuid} not found")
        
        # Проверяем, что проект в статусе "в работе"
        if project.status != 'in_progress':
            raise ValidationError("Folders can only be created for projects with 'In Progress' status")
        
        folder = serializer.save(created_by=self.request.user, project=project)
        
        # Автоматически даем полный доступ ГИПу
        if project.gip and project.gip.user:
            FolderAccess.objects.create(
                folder=folder,
                user=project.gip.user,
                access_level='ADMIN',
                granted_by=self.request.user
            )

    @action(detail=False, methods=['get'], url_path='projects/(?P<project_uuid>[^/.]+)/folders')
    def list_project_folders(self, request, project_uuid=None):
        """Получение списка папок для конкретного проекта"""
        try:
            project = Project.objects.get(uuid=project_uuid)
            queryset = self.get_queryset().filter(project=project)
            
            # Фильтрация по названию папки, если указано
            folder_name = request.query_params.get('name')
            if folder_name:
                queryset = queryset.filter(name=folder_name)
                if not queryset.exists():
                    raise ValidationError(f"Folder with name '{folder_name}' not found in project")
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
            
        except Project.DoesNotExist:
            raise ValidationError(f"Project with UUID {project_uuid} not found")

    @action(detail=False, methods=['get'])
    def by_name(self, request):
        """Получение папки по названию"""
        name = request.query_params.get('name')
        project_uuid = request.query_params.get('project')
        
        if not name or not project_uuid:
            raise ValidationError("Both 'name' and 'project' parameters are required")
            
        try:
            project = Project.objects.get(uuid=project_uuid)
            folder = self.get_queryset().filter(
                project=project,
                name=name
            ).first()
            
            if not folder:
                raise ValidationError(f"Folder with name '{name}' not found in project")
                
            serializer = self.get_serializer(folder)
            return Response(serializer.data)
            
        except Project.DoesNotExist:
            raise ValidationError(f"Project with UUID {project_uuid} not found")

    @action(detail=True, methods=['post'])
    def create_subfolder(self, request, pk=None, project_uuid=None):
        """Создание подпапки"""
        try:
            parent_folder = self.get_object()
            name = request.data.get('name')
            
            if not name:
                raise ValidationError("Name is required")
                
            # Проверка длины имени
            if len(name) > 50:
                raise ValidationError("Название папки не может быть длиннее 50 символов")

            # Проверяем права доступа
            if not FolderAccess.objects.filter(
                folder=parent_folder,
                user=request.user,
                access_level__in=['WRITE', 'ADMIN']
            ).exists():
                raise PermissionDenied("У вас нет прав на создание подпапок")

            # Проверка максимальной глубины вложенности
            nesting_level = 1
            current = parent_folder
            while current.parent:
                nesting_level += 1
                current = current.parent
                if nesting_level > 5:
                    raise ValidationError("Превышена максимальная глубина вложенности папок (5)")

            # Проверка уникальности имени
            if Folder.objects.filter(
                name=name,
                parent=parent_folder,
                project=parent_folder.project
            ).exists():
                raise ValidationError("Папка с таким именем уже существует")

            new_folder = Folder.objects.create(
                name=name,
                parent=parent_folder,
                project=parent_folder.project,
                created_by=request.user
            )
            
            # Наследуем права доступа от родительской папки
            parent_accesses = FolderAccess.objects.filter(folder=parent_folder)
            for access in parent_accesses:
                FolderAccess.objects.create(
                    folder=new_folder,
                    user=access.user,
                    access_level=access.access_level,
                    granted_by=request.user
                )
            
            serializer = self.get_serializer(new_folder)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating subfolder: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request, *args, **kwargs):
        """
        Создание новой папки с дополнительными проверками
        """
        try:
            # Проверка длины имени
            name = request.data.get('name')
            if len(name) > 50:
                raise ValidationError("Название папки не может быть длиннее 50 символов")

            # Проверка максимального количества вложенных папок
            parent_id = request.data.get('parent')
            if parent_id:
                parent = Folder.objects.get(id=parent_id)
                nesting_level = 1
                current = parent
                while current.parent:
                    nesting_level += 1
                    current = current.parent
                    if nesting_level > 5:  # Максимальная глубина вложенности
                        raise ValidationError("Превышена максимальная глубина вложенности папок (5)")

            # Проверка уникальности имени папки в пределах родительской папки и проекта
            name = request.data.get('name')
            project_uuid = request.data.get('project')
            if Folder.objects.filter(
                name=name,
                parent_id=parent_id,
                project__uuid=project_uuid
            ).exists():
                raise ValidationError("Папка с таким именем уже существует в данном месте")

            return super().create(request, *args, **kwargs)

        except Exception as e:
            logger.error(f"Error creating folder: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        """Обновление существующей папки"""
        try:
            instance = self.get_object()
            
            # Проверка длины нового имени
            new_name = request.data.get('name')
            if new_name and len(new_name) > 50:
                raise ValidationError("Название папки не может быть длиннее 50 символов")

            # Проверка прав доступа
            if not FolderAccess.objects.filter(
                folder=instance,
                user=request.user,
                access_level='ADMIN'
            ).exists():
                raise PermissionDenied("У вас нет прав на изменение этой папки")

            # Проверка уникальности нового имени
            new_name = request.data.get('name')
            if new_name and new_name != instance.name:
                if Folder.objects.filter(
                    name=new_name,
                    parent=instance.parent,
                    project=instance.project
                ).exists():
                    raise ValidationError("Папка с таким именем уже существует")

            return super().update(request, *args, **kwargs)

        except Exception as e:
            logger.error(f"Error updating folder: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        """Удаление папки"""
        try:
            instance = self.get_object()
            
            # Проверка прав доступа
            if not FolderAccess.objects.filter(
                folder=instance,
                user=request.user,
                access_level='ADMIN'
            ).exists():
                raise PermissionDenied("У вас нет прав на удаление этой папки")

            # Проверка наличия подпапок и файлов
            if instance.children.exists() or instance.files.exists():
                raise ValidationError("Нельзя удалить папку, содержащую подпапки или файлы")

            # Проверка типа папки
            if instance.folder_type in ['LIBRARY', 'SOURCE', 'PROCESS']:
                raise ValidationError("Нельзя удалить системную папку")

            return super().destroy(request, *args, **kwargs)

        except Exception as e:
            logger.error(f"Error deleting folder: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """
        Перемещение папки в другую папку
        """
        try:
            folder = self.get_object()
            new_parent_id = request.data.get('new_parent')
            
            # Проверка прав доступа
            if not FolderAccess.objects.filter(
                folder=folder,
                user=request.user,
                access_level='ADMIN'
            ).exists():
                raise PermissionDenied("У вас нет прав на перемещение этой папки")

            if new_parent_id:
                new_parent = get_object_or_404(Folder, id=new_parent_id)
                
                # Проверка, что новая родительская папка находится в том же проекте
                if new_parent.project != folder.project:
                    raise ValidationError("Нельзя переместить папку в другой проект")
                
                # Проверка циклических ссылок
                current = new_parent
                while current:
                    if current == folder:
                        raise ValidationError("Нельзя переместить папку внутрь её подпапки")
                    current = current.parent

                folder.parent = new_parent
            else:
                folder.parent = None

            folder.save()
            return Response(self.get_serializer(folder).data)

        except Exception as e:
            logger.error(f"Error moving folder: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create_project_folder(self, request, project_uuid=None):
        """Создание папки в проекте"""
        try:
            project = Project.objects.get(uuid=project_uuid)
            
            # Проверяем, что проект в статусе "в работе"
            if project.status != 'in_progress':
                raise ValidationError("Folders can only be created for projects with 'In Progress' status")
            
            # Добавляем проект к данным запроса
            data = request.data.copy()
            data['project'] = project.uuid
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            
            folder = serializer.save(created_by=request.user, project=project)
            
            # Автоматически даем полный доступ ГИПу
            if project.gip and project.gip.user:
                FolderAccess.objects.create(
                    folder=folder,
                    user=project.gip.user,
                    access_level='ADMIN',
                    granted_by=request.user
                )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Project.DoesNotExist:
            raise ValidationError(f"Project with UUID {project_uuid} not found")
        except Exception as e:
            logger.error(f"Error creating folder: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_project_or_404(self, project_uuid):
        """Получение проекта или 404"""
        try:
            return Project.objects.get(uuid=project_uuid)
        except Project.DoesNotExist:
            raise ValidationError(f"Project with UUID {project_uuid} not found")

    def retrieve(self, request, project_uuid=None, *args, **kwargs):
        """Получение конкретной папки проекта"""
        project = self.get_project_or_404(project_uuid)
        instance = self.get_object()
        
        if instance.project != project:
            raise ValidationError("Folder does not belong to specified project")
            
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        """Получение списка файлов с учетом прав доступа"""
        user = self.request.user
        return File.objects.filter(
            Q(folder__access_rights__user=user) |
            Q(folder__project__members__member__user=user) |  # Проверка через ProjectMember
            Q(folder__project__gip__user=user) |             # Проверка ГИПа
            Q(created_by=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Загрузка нового файла
        """
        try:
            folder_id = kwargs.get('folder_id') or request.data.get('folder')
            if not folder_id:
                raise ValidationError("Folder ID is required")

            folder = get_object_or_404(Folder, id=folder_id)
            
            # Проверка прав доступа
            if not FolderAccess.objects.filter(
                folder=folder,
                user=request.user,
                access_level__in=['WRITE', 'ADMIN']
            ).exists():
                raise PermissionDenied("У вас нет прав на загрузку файлов в эту папку")

            # Проверка файла
            file = request.FILES.get('file')
            if not file:
                raise ValidationError("File is required")

            # Отладочная информация
            print("Received file:", file)
            print("File name:", file.name)
            print("File size:", file.size)
            print("Content type:", file.content_type)

            # Создаем файл
            instance = File.objects.create(
                name=request.data.get('name', file.name),
                folder=folder,
                file=file,
                created_by=request.user,
                size=file.size,
                mime_type=file.content_type
            )

            # Проверяем сохранение
            print("File saved:", instance.file)
            print("File path:", instance.file.path if instance.file else "No path")
            print("File URL:", instance.file.url if instance.file else "No URL")
            print("File exists:", os.path.exists(instance.file.path) if instance.file else False)

            # Проверяем права доступа к папке media
            media_path = settings.MEDIA_ROOT
            print(f"Media path permissions: {oct(os.stat(media_path).st_mode)[-3:]}")
            print(f"Media path owner: {os.stat(media_path).st_uid}")

            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            logger.exception(e)  # Полный стек ошибки
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        """
        Удаление файла
        """
        try:
            instance = self.get_object()
            
            # Проверка прав доступа
            if not FolderAccess.objects.filter(
                folder=instance.folder,
                user=request.user,
                access_level__in=['WRITE', 'ADMIN']
            ).exists():
                raise PermissionDenied("У вас нет прав на удаление этого файла")

            # Удаление физического файла
            if instance.file:
                if os.path.isfile(instance.file.path):
                    os.remove(instance.file.path)

            return super().destroy(request, *args, **kwargs)

        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """
        Перемещение файла в другую папку
        """
        try:
            file = self.get_object()
            new_folder_id = request.data.get('new_folder')
            
            if not new_folder_id:
                raise ValidationError("Необходимо указать новую папку")

            new_folder = get_object_or_404(Folder, id=new_folder_id)
            
            # Проверка прав доступа к текущей и новой папке
            if not (FolderAccess.objects.filter(
                folder=file.folder,
                user=request.user,
                access_level__in=['WRITE', 'ADMIN']
            ).exists() and FolderAccess.objects.filter(
                folder=new_folder,
                user=request.user,
                access_level__in=['WRITE', 'ADMIN']
            ).exists()):
                raise PermissionDenied("У вас нет прав на перемещение файла")

            # Проверка, что папки находятся в одном проекте
            if file.folder.project != new_folder.project:
                raise ValidationError("Нельзя переместить файл в папку другого проекта")

            # Проверка уникальности имени в новой папке
            if File.objects.filter(folder=new_folder, name=file.name).exists():
                raise ValidationError("Файл с таким именем уже существует в целевой папке")

            file.folder = new_folder
            file.save()
            
            return Response(self.get_serializer(file).data)

        except Exception as e:
            logger.error(f"Error moving file: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class FolderAccessViewSet(viewsets.ModelViewSet):
    serializer_class = FolderAccessSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Получение списка прав доступа"""
        user = self.request.user
        return FolderAccess.objects.filter(
            Q(folder__project__members__member__user=user) |  # Проверка через ProjectMember
            Q(folder__project__gip__user=user) |             # Проверка ГИПа
            Q(folder__created_by=user)
        ).distinct()

    def perform_create(self, serializer):
        """Предоставление прав доступа"""
        folder = get_object_or_404(Folder, id=self.request.data.get('folder'))
        
        # Проверяем, что пользователь имеет права администратора
        if not FolderAccess.objects.filter(
            folder=folder,
            user=self.request.user,
            access_level='ADMIN'
        ).exists():
            raise PermissionDenied("You don't have permission to manage access rights")
        
        serializer.save(granted_by=self.request.user)

class FolderActionLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FolderActionLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FolderActionLog.objects.all()
        
        # Фильтрация по проекту
        project_uuid = self.request.query_params.get('project')
        if project_uuid:
            queryset = queryset.filter(project__uuid=project_uuid)
        
        # Фильтрация по типу действия
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        # Фильтрация по дате
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset

# Применяем декораторы после определения всех классов
FolderViewSet.update = log_folder_action('UPDATE')(FolderViewSet.update)
FolderViewSet.destroy = log_folder_action('DELETE')(FolderViewSet.destroy)
FolderViewSet.create_project_folder = log_folder_action('CREATE')(FolderViewSet.create_project_folder)
FolderViewSet.move = log_folder_action('MOVE')(FolderViewSet.move)

FileViewSet.create = log_folder_action('UPLOAD')(FileViewSet.create)
FileViewSet.update = log_folder_action('UPDATE')(FileViewSet.update)
FileViewSet.destroy = log_folder_action('DELETE')(FileViewSet.destroy)
FileViewSet.move = log_folder_action('MOVE')(FileViewSet.move)
