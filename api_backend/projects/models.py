from django.db import models
from accounts.models import Specialty
from django.core.validators import MinValueValidator
import uuid

class ProjectComplexity(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название категории сложности')
    description = models.TextField(verbose_name='Описание категории', blank=True)

    class Meta:
        verbose_name = 'Категория сложности проекта'
        verbose_name_plural = 'Категории сложности проектов'

    def __str__(self):
        return self.name
    
class ProjectTemplate(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название шаблона')
    description = models.TextField(verbose_name='Описание шаблона', blank=True)
    
    class Meta:
        verbose_name = 'Шаблон проекта'
        verbose_name_plural = 'Шаблоны проектов'

    def __str__(self):
        return self.name

class DefaultProjectTemplateTask(models.Model):
    template = models.ForeignKey(
        'ProjectTemplate',
        on_delete=models.CASCADE,
        related_name='default_tasks',
        verbose_name='Шаблон',
    )
    order = models.CharField(max_length=10, verbose_name='Порядковый номер')
    work_name = models.CharField(max_length=200, verbose_name='Наименование работ')
    sub_work_name = models.CharField(max_length=200, verbose_name='Подописание работ')

    class Meta:
        verbose_name = 'Предустановленная задача шаблона'
        verbose_name_plural = 'Предустановленные задачи шаблона'
        ordering = ['order']

    def __str__(self):
        return f'{self.order}. {self.work_name} - {self.sub_work_name} в шаблоне {self.template.name}'

class ProjectTemplateTask(models.Model):
    template = models.ForeignKey(
        ProjectTemplate,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Шаблон'
        )
    order = models.CharField(max_length=10, verbose_name='Порядковый номер', blank=True, null=True)
    work_name = models.CharField(max_length=200, verbose_name='Наименование работ')
    sub_work_name = models.CharField(max_length=200, verbose_name='Подописание работ')
    duration = models.CharField(max_length=20, verbose_name='Длительность в днях')
    start_date = models.DateField(verbose_name='Дата начала', blank=True, null=True)
    notes = models.TextField(verbose_name='Примечания', blank=True)
    
    class Meta:
        verbose_name = 'Задача шаблона'
        verbose_name_plural = 'Задачи шаблона'

    def __str__(self):
        return f'{self.order}. {self.work_name} - {self.sub_work_name} в шаблоне {self.template.name}'

class Project(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('auction', 'На аукционе'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200, verbose_name='Название проекта')
    subtitle = models.CharField(max_length=500, verbose_name='Краткое описание')
    complexity = models.ForeignKey(
        ProjectComplexity,
        on_delete=models.PROTECT,
        verbose_name='Категория сложности'
    )
    estimated_duration = models.PositiveIntegerField(
        verbose_name='Предполагаемый срок выполнения (месяцев)',
        validators=[MinValueValidator(1)]
    )
    client = models.ForeignKey(
        'accounts.LegalProfile',
        on_delete=models.PROTECT,
        related_name='client_projects',
        verbose_name='Заказчик'
    )
    project_office = models.ForeignKey(
        'accounts.LegalProfile',
        on_delete=models.PROTECT,
        related_name='office_projects',
        verbose_name='Проектная организация'
    )
    gip = models.ForeignKey(
        'accounts.PhysicalProfile',
        on_delete=models.PROTECT,
        related_name='gip_projects',
        verbose_name='ГИП'
    )
    description = models.TextField(verbose_name='Описание проекта')
    required_specialties = models.ManyToManyField(
        Specialty,
        verbose_name='Требуемые специальности'
    )
    template = models.ForeignKey(
        ProjectTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Шаблон проекта'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Статус проекта'
    )
    chat = models.OneToOneField(
        'chat.Chat',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project',
        verbose_name='Чат проекта'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class ProjectSpecialtyBudget(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='specialty_budgets')
    specialty = models.ForeignKey(Specialty, on_delete=models.PROTECT)
    budget = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Бюджет')

    class Meta:
        verbose_name = 'Бюджет специальности проекта'
        verbose_name_plural = 'Бюджеты специальностей проекта'

    def __str__(self):
        return f'Бюджет для {self.specialty.name} в проекте {self.project.name}'


class ProjectResponse(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name='Проект'
    )
    specialist = models.ForeignKey(
        'accounts.PhysicalProfile',
        on_delete=models.CASCADE,
        related_name='project_responses',
        verbose_name='Специалист'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    message = models.TextField(verbose_name='Сообщение')
    chat = models.OneToOneField(
        'chat.Chat',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_response',
        verbose_name='Личный чат с ГИПом'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отклик на проект'
        verbose_name_plural = 'Отклики на проекты'
        indexes = [
            models.Index(fields=['project', 'specialist']),
        ]
        unique_together = ['project', 'specialist']

    def __str__(self):
        return f'Отклик на проект {self.project.name} от {self.specialist.user.email}'

class ProjectMember(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name='Проект'
    )
    member = models.ForeignKey(
        'accounts.PhysicalProfile',
        on_delete=models.CASCADE,
        related_name='project_memberships',
        verbose_name='Участник'
    )
    role = models.CharField(max_length=100, verbose_name='Роль в проекте')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Участник проекта'
        verbose_name_plural = 'Участники проекта'
        unique_together = ['project', 'member']

    def __str__(self):
        return f'{self.member.user.email} - {self.role} в проекте {self.project.name}'