from django.db import models
from django.contrib.auth import get_user_model
from projects.models import Project

User = get_user_model()

class Folder(models.Model):
    FOLDER_TYPES = [
        ('LIBRARY', 'Library'),
        ('SOURCE', 'Исходные данные'),
        ('PROCESS', 'Процесс работы'),
        ('TASKS', 'Обмен заданиями'),
        ('WORKING', 'Рабочие данные'),
        ('PUBLISHED', 'Опубликованные данные'),
        ('REMARKS', 'Замечания'),
        ('SHORTCUTS', 'Ярлыки'),
    ]

    ACCESS_LEVELS = [
        ('READ', 'Только чтение'),
        ('WRITE', 'Чтение и запись'),
        ('ADMIN', 'Полный доступ'),
    ]

    name = models.CharField(max_length=50)
    folder_type = models.CharField(max_length=20, choices=FOLDER_TYPES, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='folders')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_folders')

    class Meta:
        unique_together = ['project', 'folder_type', 'parent']
        ordering = ['folder_type', 'name']
        indexes = [
            models.Index(fields=['folder_type', 'project']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Папка'
        verbose_name_plural = 'Папки'

    def __str__(self):
        return f"{self.name} - {self.project.name}"

    @classmethod
    def create_default_structure(cls, project):
        """Создает структуру папок по умолчанию для проекта"""
        root_folders = []
        for folder_type, folder_name in cls.FOLDER_TYPES:
            folder = cls.objects.create(
                name=folder_name,
                folder_type=folder_type,
                project=project,
                parent=None
            )
            # Даем полный доступ ГИПу к каждой созданной папке
            if project.gip and project.gip.user:
                FolderAccess.objects.create(
                    folder=folder,
                    user=project.gip.user,
                    access_level='ADMIN',
                    granted_by=project.gip.user  # ГИП м себе дает права
                )
            root_folders.append(folder)
        return root_folders

class File(models.Model):
    name = models.CharField(max_length=255)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='project_files/%Y/%m/%d/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_files')
    size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
            self.mime_type = self.file.content_type if hasattr(self.file, 'content_type') else ''
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Файл'
        verbose_name_plural = 'Файлы'

    def __str__(self):
        return self.name

class FolderAccess(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='access_rights')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_level = models.CharField(max_length=10, choices=Folder.ACCESS_LEVELS)
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_access')

    class Meta:
        unique_together = ['folder', 'user']
        verbose_name = 'Доступ к папке'
        verbose_name_plural = 'Доступы к папкам'

    def __str__(self):
        return f"{self.user.email} - {self.folder.name} ({self.get_access_level_display()})"

class FolderActionLog(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Создание'),
        ('UPDATE', 'Изменение'),
        ('DELETE', 'Удаление'),
        ('MOVE', 'Перемещение'),
        ('UPLOAD', 'Загрузка файла'),
        ('DOWNLOAD', 'Скачивание файла'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    folder = models.ForeignKey(
        Folder, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='action_logs'
    )
    file = models.ForeignKey(
        File, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='action_logs'
    )
    folder_name = models.CharField(max_length=255, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Лог действий с папкой'
        verbose_name_plural = 'Логи действий с папками'

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.user.email} - {self.created_at}"

    def save(self, *args, **kwargs):
        if self.folder and not self.folder_name:
            self.folder_name = self.folder.name
        if self.file and not self.file_name:
            self.file_name = self.file.name
        super().save(*args, **kwargs)
