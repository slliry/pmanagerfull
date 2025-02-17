from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'assigned_to', 'due_date', 'status')
    search_fields = ('title', 'assigned_to__email')
    list_filter = ('status', 'due_date')