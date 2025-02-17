from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (
    ProjectComplexity, Project, ProjectResponse,
    ProjectMember, ProjectSpecialtyBudget,
    ProjectTemplate, ProjectTemplateTask, DefaultProjectTemplateTask
)
from accounts.serializers import PhysicalProfileSerializer, LegalProfileSerializer, SpecialtySerializer
from accounts.models import Specialty, LegalProfile
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class ProjectComplexitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectComplexity
        fields = ['id', 'name', 'description']

class DefaultProjectTemplateTaskSerializer(serializers.ModelSerializer):
   class Meta:
    model = DefaultProjectTemplateTask
    fields = ['id', 'order', 'work_name', 'sub_work_name']

class ProjectTemplateTaskSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(required=False, allow_null=True)
    
    class Meta:
        model = ProjectTemplateTask
        fields = ['id', 'order', 'work_name', 'sub_work_name', 'duration', 'start_date', 'notes']

class ProjectTemplateSerializer(serializers.ModelSerializer):
    tasks = ProjectTemplateTaskSerializer(many=True)
    default_tasks = DefaultProjectTemplateTaskSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProjectTemplate
        fields = ['id', 'name', 'description', 'tasks', 'default_tasks']

    def create(self, validated_data):
        tasks_data = validated_data.pop('tasks', [])
        template = ProjectTemplate.objects.create(**validated_data)
        
        for task_data in tasks_data:
            ProjectTemplateTask.objects.create(template=template, **task_data)
        
        return template

    def update(self, instance, validated_data):
        tasks_data = validated_data.pop('tasks', [])
        instance = super().update(instance, validated_data)
        
        # Обновляем задачи
        if tasks_data:
            instance.tasks.all().delete()
            for task_data in tasks_data:
                ProjectTemplateTask.objects.create(template=instance, **task_data)
            
        return instance

class ProjectSpecialtyBudgetSerializer(serializers.ModelSerializer):
    specialty = serializers.PrimaryKeyRelatedField(queryset=Specialty.objects.all())

    class Meta:
        model = ProjectSpecialtyBudget
        fields = ['specialty', 'budget']

class ProjectResponseSerializer(serializers.ModelSerializer):
    specialist = PhysicalProfileSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_uuid = serializers.UUIDField(source='project.uuid', read_only=True)
    message = serializers.CharField(required=True)
    uuid = serializers.UUIDField(read_only=True)
    specialist_full_name = serializers.SerializerMethodField()
    specialty_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectResponse
        fields = [
            'id', 'uuid',
            'project_name', 'project_uuid',
            'specialist', 'specialist_full_name',
            'specialty_name', 'status', 'message',
            'created_at'
        ]
        read_only_fields = ['status', 'specialist', 'uuid', 'project_name', 'project_uuid']

    def get_specialist_full_name(self, obj):
        return f"{obj.specialist.last_name} {obj.specialist.first_name} {obj.specialist.middle_name or ''}".strip()

    def get_specialty_name(self, obj):
        return obj.specialist.specialty.name if obj.specialist.specialty else None

    def create(self, validated_data):
        # При создании отклика нам нужен project, поэтому добавляем его из context
        project_uuid = self.context.get('project_uuid')
        if not project_uuid:
            raise serializers.ValidationError("project_uuid is required")
        
        try:
            project = Project.objects.get(uuid=project_uuid)
        except Project.DoesNotExist:
            raise serializers.ValidationError("Project not found")
            
        validated_data['project'] = project
        return super().create(validated_data)

class ProjectMemberSerializer(serializers.ModelSerializer):
    member = PhysicalProfileSerializer(read_only=True)
    project_uuid = serializers.UUIDField(source='project.uuid', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    user_id = serializers.IntegerField(source='member.user.id', read_only=True)

    class Meta:
        model = ProjectMember
        fields = [
            'id', 'project_uuid', 'project_name',
            'user_id', 'member', 'role', 'joined_at'
        ]

class ProjectSerializer(serializers.ModelSerializer):
    complexity = ProjectComplexitySerializer(read_only=True)
    complexity_id = serializers.PrimaryKeyRelatedField(
        queryset=ProjectComplexity.objects.all(),
        source='complexity',
        write_only=True
    )
    client = serializers.PrimaryKeyRelatedField(
        queryset=LegalProfile.objects.all(),
        write_only=True
    )
    specialty_budgets = ProjectSpecialtyBudgetSerializer(many=True)
    template = ProjectTemplateSerializer(read_only=True)
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=ProjectTemplate.objects.all(),
        source='template',
        write_only=True,
        required=False,
        allow_null=True
    )
    required_specialties = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Specialty.objects.all()),
        write_only=True
    )
    
    class Meta:
        model = Project
        fields = [
            'id', 'uuid', 'name', 'subtitle', 'complexity', 'complexity_id',
            'estimated_duration', 'client',
            'description', 'required_specialties', 'template', 'template_id', 'specialty_budgets',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'created_at', 'updated_at']

    def create(self, validated_data):
        specialty_budgets_data = validated_data.pop('specialty_budgets', [])
        required_specialties = validated_data.pop('required_specialties', [])
        
        # Проверяем наличие профиля у пользователя
        user = self.context['request'].user
        if hasattr(user, 'physical_profile') and user.physical_profile.project_office:
            project_office = user.physical_profile.project_office
        else:
            raise serializers.ValidationError("У пользователя нет связанного Project Office.")

        # Удаляем project_office из validated_data, если он там есть
        validated_data.pop('project_office', None)

        project = Project.objects.create(project_office=project_office, **validated_data)
        
        # Устанавливаем требуемые специальности
        project.required_specialties.set(required_specialties)

        # Создаем бюджеты для каждой специальности
        for budget_data in specialty_budgets_data:
            ProjectSpecialtyBudget.objects.create(project=project, **budget_data)
        return project

    def update(self, instance, validated_data):
        specialty_budgets_data = validated_data.pop('specialty_budgets', [])
        required_specialties = validated_data.pop('required_specialties', [])
        
        # Проверяем наличие профиля у пользователя
        user = self.context['request'].user
        if hasattr(user, 'physical_profile') and user.physical_profile.project_office:
            project_office = user.physical_profile.project_office
        else:
            raise serializers.ValidationError("У пользователя нет связанного Project Office.")

        # Удаляем project_office из validated_data, если он там есть
        validated_data.pop('project_office', None)

        instance = super().update(instance, validated_data)
        instance.project_office = project_office
        instance.required_specialties.set(required_specialties)

        # Удаляем старые бюджеты и создаем новые
        instance.specialty_budgets.all().delete()
        for budget_data in specialty_budgets_data:
            ProjectSpecialtyBudget.objects.create(project=instance, **budget_data)

        return instance