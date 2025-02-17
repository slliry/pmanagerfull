from rest_framework import serializers
from .models import Task
from projects.models import Project
from datetime import datetime, time
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class TaskSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(
        queryset=Project.objects.all(),
        slug_field='uuid'
    )
    due_date_str = serializers.DateField(write_only=True, required=False)
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True
    )
    assigned_to_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'assigned_to', 'assigned_to_details',
                 'project', 'due_date', 'due_date_str', 'status', 'created_at', 'updated_at']
        read_only_fields = ['status', 'created_at', 'updated_at']
        extra_kwargs = {
            'due_date': {'required': False}
        }

    def get_assigned_to_details(self, obj):
        physical_profile = obj.assigned_to.physical_profile
        return {
            'id': obj.assigned_to.id,
            'first_name': physical_profile.first_name,
            'last_name': physical_profile.last_name,
            'middle_name': physical_profile.middle_name
        }

    def validate(self, data):
        if 'due_date_str' in data:
            date = data.pop('due_date_str')
            naive_datetime = datetime.combine(date, time())
            data['due_date'] = timezone.make_aware(naive_datetime)
        
        if 'due_date' not in data:
            raise serializers.ValidationError("Either due_date or due_date_str must be provided")

        return data