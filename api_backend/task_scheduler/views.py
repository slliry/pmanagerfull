from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Task
from .serializers import TaskSerializer
from projects.models import ProjectMember

class IsGIPOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(request.user, 'physical_profile') and request.user.physical_profile.is_gip

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsGIPOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'physical_profile'):
            return Task.objects.none()

        if user.physical_profile.is_gip:
            # ГИП видит задачи своих проектов
            return Task.objects.filter(project__gip=user.physical_profile)
        else:
            # Обычный пользователь видит задачи проектов, в которых участвует
            user_projects = ProjectMember.objects.filter(
                member=user.physical_profile
            ).values_list('project', flat=True)
            return Task.objects.filter(project__in=user_projects)

    def perform_create(self, serializer):
        # Проверяем, что пользователь является ГИПом проекта
        project = serializer.validated_data['project']
        if project.gip.user != self.request.user:
            raise PermissionDenied("Только ГИП может создавать задачи для этого проекта.")
        serializer.save()

    def get_permissions(self):
        print("="*50)
        print("Debugging permissions:")
        print(f"Method: {self.request.method}")
        print(f"Path: {self.request.path}")
        print(f"Headers: {dict(self.request.headers)}")
        print(f"User: {self.request.user}")
        print(f"Is authenticated: {self.request.user.is_authenticated}")
        if hasattr(self.request.user, 'physical_profile'):
            print(f"Has physical profile: True")
            print(f"Is GIP: {self.request.user.physical_profile.is_gip}")
        else:
            print("Has physical profile: False")
        print("="*50)
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        print("="*50)
        print("Create method called")
        print(f"Request data: {request.data}")
        print("="*50)
        return super().create(request, *args, **kwargs)