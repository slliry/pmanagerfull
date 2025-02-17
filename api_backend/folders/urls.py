from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FolderViewSet, FileViewSet, FolderAccessViewSet, FolderActionLogViewSet

router = DefaultRouter()
router.register(r'files', FileViewSet, basename='file')
router.register(r'access', FolderAccessViewSet, basename='folder-access')
router.register(r'logs', FolderActionLogViewSet, basename='folder-logs')

urlpatterns = [
    path('', include(router.urls)),
    # Маршруты для работы с папками проекта
    path('projects/<uuid:project_uuid>/folders/', 
         FolderViewSet.as_view({
             'get': 'list_project_folders',
             'post': 'create_project_folder'
         }), 
         name='project-folders'),
         
    path('projects/<uuid:project_uuid>/folders/<int:pk>/', 
         FolderViewSet.as_view({
             'get': 'retrieve',
             'put': 'update',
             'patch': 'partial_update',
             'delete': 'destroy'
         }), 
         name='project-folder-detail'),
         
    # Добавляем маршрут для создания подпапки
    path('projects/<uuid:project_uuid>/folders/<int:pk>/create_subfolder/', 
         FolderViewSet.as_view({'post': 'create_subfolder'}), 
         name='create-subfolder'),
         
    # Маршруты для файлов
    path('projects/<uuid:project_uuid>/folders/<int:folder_id>/files/', 
         FileViewSet.as_view({
             'get': 'list',
             'post': 'create'
         }), 
         name='project-folder-files'),
         
    path('projects/<uuid:project_uuid>/folders/<int:folder_id>/files/<int:pk>/', 
         FileViewSet.as_view({
             'get': 'retrieve',
             'put': 'update',
             'delete': 'destroy'
         }), 
         name='project-folder-file-detail'),
]
