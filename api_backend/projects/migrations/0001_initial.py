# Generated by Django 5.1.2 on 2025-01-07 09:11

import django.core.validators
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectComplexity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название категории сложности')),
                ('description', models.TextField(blank=True, verbose_name='Описание категории')),
            ],
            options={
                'verbose_name': 'Категория сложности проекта',
                'verbose_name_plural': 'Категории сложности проектов',
            },
        ),
        migrations.CreateModel(
            name='ProjectTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название шаблона')),
                ('description', models.TextField(blank=True, verbose_name='Описание шаблона')),
            ],
            options={
                'verbose_name': 'Шаблон проекта',
                'verbose_name_plural': 'Шаблоны проектов',
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(max_length=200, verbose_name='Название проекта')),
                ('subtitle', models.CharField(max_length=500, verbose_name='Краткое описание')),
                ('estimated_duration', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Предполагаемый срок выполнения (месяцев)')),
                ('description', models.TextField(verbose_name='Описание проекта')),
                ('status', models.CharField(choices=[('draft', 'Черновик'), ('auction', 'На аукционе'), ('in_progress', 'В работе'), ('completed', 'Завершен'), ('cancelled', 'Отменен')], default='draft', max_length=20, verbose_name='Статус проекта')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('chat', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project', to='chat.chat', verbose_name='Чат проекта')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='client_projects', to='accounts.legalprofile', verbose_name='Заказчик')),
                ('gip', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='gip_projects', to='accounts.physicalprofile', verbose_name='ГИП')),
                ('project_office', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='office_projects', to='accounts.legalprofile', verbose_name='Проектная организация')),
                ('required_specialties', models.ManyToManyField(to='accounts.specialty', verbose_name='Требуемые специальности')),
                ('complexity', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='projects.projectcomplexity', verbose_name='Категория сложности')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='projects.projecttemplate', verbose_name='Шаблон проекта')),
            ],
            options={
                'verbose_name': 'Проект',
                'verbose_name_plural': 'Проекты',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProjectSpecialtyBudget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('budget', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Бюджет')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='specialty_budgets', to='projects.project')),
                ('specialty', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounts.specialty')),
            ],
            options={
                'verbose_name': 'Бюджет специальности проекта',
                'verbose_name_plural': 'Бюджеты специальностей проекта',
            },
        ),
        migrations.CreateModel(
            name='DefaultProjectTemplateTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.CharField(max_length=10, verbose_name='Порядковый номер')),
                ('work_name', models.CharField(max_length=200, verbose_name='Наименование работ')),
                ('sub_work_name', models.CharField(max_length=200, verbose_name='Подописание работ')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='default_tasks', to='projects.projecttemplate', verbose_name='Шаблон')),
            ],
            options={
                'verbose_name': 'Предустановленная задача шаблона',
                'verbose_name_plural': 'Предустановленные задачи шаблона',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='ProjectTemplateTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.CharField(blank=True, max_length=10, null=True, verbose_name='Порядковый номер')),
                ('work_name', models.CharField(max_length=200, verbose_name='Наименование работ')),
                ('sub_work_name', models.CharField(max_length=200, verbose_name='Подописание работ')),
                ('duration', models.CharField(max_length=20, verbose_name='Длительность в днях')),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='Дата начала')),
                ('notes', models.TextField(blank=True, verbose_name='Примечания')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='projects.projecttemplate', verbose_name='Шаблон')),
            ],
            options={
                'verbose_name': 'Задача шаблона',
                'verbose_name_plural': 'Задачи шаблона',
            },
        ),
        migrations.CreateModel(
            name='ProjectMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=100, verbose_name='Роль в проекте')),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_memberships', to='accounts.physicalprofile', verbose_name='Участник')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='projects.project', verbose_name='Проект')),
            ],
            options={
                'verbose_name': 'Участник проекта',
                'verbose_name_plural': 'Участники проекта',
                'unique_together': {('project', 'member')},
            },
        ),
        migrations.CreateModel(
            name='ProjectResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('status', models.CharField(choices=[('pending', 'На рассмотрении'), ('accepted', 'Принято'), ('rejected', 'Отклонено')], default='pending', max_length=20, verbose_name='Статус')),
                ('message', models.TextField(verbose_name='Сообщение')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chat', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project_response', to='chat.chat', verbose_name='Личный чат с ГИПом')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='projects.project', verbose_name='Проект')),
                ('specialist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_responses', to='accounts.physicalprofile', verbose_name='Специалист')),
            ],
            options={
                'verbose_name': 'Отклик на проект',
                'verbose_name_plural': 'Отклики на проекты',
                'indexes': [models.Index(fields=['project', 'specialist'], name='projects_pr_project_4d041a_idx')],
                'unique_together': {('project', 'specialist')},
            },
        ),
    ]
