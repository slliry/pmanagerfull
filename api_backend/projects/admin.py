from django.contrib import admin
from .models import ProjectComplexity, Project, ProjectResponse, ProjectMember, ProjectTemplate, ProjectTemplateTask, DefaultProjectTemplateTask, ProjectSpecialtyBudget


@admin.register(ProjectComplexity)
class ProjectComplexityAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'subtitle', 'complexity', 'status', 'gip', 'client', 'project_office')
    list_filter = ('status', 'complexity', 'required_specialties')
    search_fields = ('name', 'subtitle', 'description')
    date_hierarchy = 'created_at'

@admin.register(ProjectResponse)
class ProjectResponseAdmin(admin.ModelAdmin):
    list_display = ('project', 'specialist', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('project__name', 'specialist__user__email')

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('project', 'member', 'role', 'joined_at')
    list_filter = ('role',)
    search_fields = ('project__name', 'member__user__email', 'role')

class ProjectTemplateTaskInline(admin.TabularInline):
    model = ProjectTemplateTask
    extra = 1
    fields = ('order', 'sub_work_name', 'work_name', 'duration', 'start_date', 'notes')

class DefaultProjectTemplateTaskInline(admin.TabularInline):
    model = DefaultProjectTemplateTask
    extra = 1
    fields = ('order', 'sub_work_name', 'work_name')

@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    inlines = [DefaultProjectTemplateTaskInline, ProjectTemplateTaskInline]

@admin.register(ProjectSpecialtyBudget)
class ProjectSpecialtyBudgetAdmin(admin.ModelAdmin):
    list_display = ('project', 'specialty', 'budget')
    list_filter = ('project', 'specialty')
    search_fields = ('project__name', 'specialty__name')