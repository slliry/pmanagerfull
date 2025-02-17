from rest_framework import serializers
from .models import Folder, File, FolderAccess, FolderActionLog
from projects.models import Project
from django.conf import settings

class FileSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ['id', 'name', 'folder', 'file', 'created_at', 'updated_at', 'created_by', 'size', 'mime_type']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'size', 'mime_type']

    def get_file(self, obj):
        if obj.file:
            try:
                return f"{settings.MEDIA_HOST}{obj.file.url}"
            except Exception as e:
                print(f"Error getting file URL: {e}")
                return None
        return None

    def create(self, validated_data):
        file = validated_data.get('file')
        if file:
            # Убедимся, что файл сохраняется
            instance = super().create(validated_data)
            instance.save()  # Это вызовет метод save модели и обновит size и mime_type
            return instance
        return super().create(validated_data)

    def to_representation(self, instance):
        # Добавляем отладочную информацию
        print(f"File instance: {instance}")
        print(f"File URL: {instance.file.url if instance.file else 'No file'}")
        
        ret = super().to_representation(instance)
        print(f"Serialized data: {ret}")
        return ret

class FolderSerializer(serializers.ModelSerializer):
    files = FileSerializer(many=True, read_only=True)
    children = serializers.SerializerMethodField()
    project_uuid = serializers.UUIDField(source='project.uuid', read_only=True)
    project = serializers.UUIDField(format='hex_verbose', required=False)

    class Meta:
        model = Folder
        fields = ['id', 'name', 'folder_type', 'project', 'project_uuid', 'parent', 'created_at', 
                 'updated_at', 'created_by', 'files', 'children']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'project_uuid']

    def get_children(self, obj):
        children = Folder.objects.filter(parent=obj)
        return FolderSerializer(children, many=True).data

    def validate_project(self, value):
        if value:
            try:
                return Project.objects.get(uuid=value)
            except Project.DoesNotExist:
                raise serializers.ValidationError(f"Project with UUID {value} not found")
        return value

    def create(self, validated_data):
        project_uuid = validated_data.get('project')
        if isinstance(project_uuid, str):
            try:
                validated_data['project'] = Project.objects.get(uuid=project_uuid)
            except Project.DoesNotExist:
                raise serializers.ValidationError(f"Project with UUID {project_uuid} not found")
        return super().create(validated_data)

class FolderAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = FolderAccess
        fields = ['id', 'folder', 'user', 'access_level', 'granted_at', 'granted_by']
        read_only_fields = ['granted_at', 'granted_by']

class FolderActionLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    project_name = serializers.CharField(source='project.name', read_only=True)
    folder_name = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)

    class Meta:
        model = FolderActionLog
        fields = ['id', 'user_email', 'user_name', 'project_name', 'folder_name', 'file_name', 
                 'action_type', 'action_type_display', 'description', 'created_at']

    def get_user_name(self, obj):
        if not obj.user:
            return "Система"
            
        if obj.user.profile_type == 'physical':
            try:
                profile = obj.user.physical_profile
                full_name = f"{profile.last_name} {profile.first_name}"
                if profile.middle_name:
                    full_name += f" {profile.middle_name}"
                return full_name.strip()
            except:
                pass
        elif obj.user.profile_type == 'legal':
            try:
                return obj.user.legal_profile.company_name
            except:
                pass
                
        return obj.user.email

    def get_folder_name(self, obj):
        return obj.folder.name if obj.folder else obj.folder_name

    def get_file_name(self, obj):
        return obj.file.name if obj.file else obj.file_name
