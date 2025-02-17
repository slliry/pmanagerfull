from django.db import models
from django.utils import timezone
from accounts.models import User, PhysicalProfile
from projects.models import Project

class Task(models.Model):
    STATUS_CHOICES = [
        ('green', 'Поставленная задача'),
        ('yellow', 'Срок выполнения подгорает'),
        ('red', 'Задача истекла'),
    ]

    title = models.CharField(max_length=255, verbose_name='Название задачи')
    description = models.TextField(verbose_name='Описание задачи', blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks', verbose_name='Исполнитель')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', verbose_name='Проект')
    due_date = models.DateTimeField(verbose_name='Срок выполнения')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='green', verbose_name='Статус задачи')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def save(self, *args, **kwargs):
        # Определяем статус задачи в зависимости от срока выполнения
        if self.due_date < timezone.now():
            self.status = 'red'
        elif self.due_date < timezone.now() + timezone.timedelta(days=1):
            self.status = 'yellow'
        else:
            self.status = 'green'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'

    def __str__(self):
        return self.title 