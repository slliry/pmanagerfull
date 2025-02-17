from django.contrib import admin
from .models import Folder, File, FolderAccess, FolderActionLog

# Register your models here.

@admin.register(FolderActionLog)
class FolderActionLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action_type', 'description')
    list_filter = ('action_type', 'created_at', 'project')
    search_fields = ('description', 'user__email')
    date_hierarchy = 'created_at'
    actions = ['delete_selected']  # Добавляем возможность массового удаления

    def has_add_permission(self, request):
        return False  # Запрещаем создание логов через админку

    def has_change_permission(self, request, obj=None):
        return False  # Запрещаем изменение логов

    def has_delete_permission(self, request, obj=None):
        return True  # Разрешаем удаление логов

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'folder_type', 'parent', 'created_by', 'created_at')
    list_filter = ('folder_type', 'project', 'created_at')
    search_fields = ('name', 'project__name')

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('name', 'folder', 'created_by', 'created_at', 'size')
    list_filter = ('created_at', 'folder__project')
    search_fields = ('name', 'folder__name')

@admin.register(FolderAccess)
class FolderAccessAdmin(admin.ModelAdmin):
    list_display = ('folder', 'user', 'access_level', 'granted_by', 'granted_at')
    list_filter = ('access_level', 'granted_at')
    search_fields = ('folder__name', 'user__email')
