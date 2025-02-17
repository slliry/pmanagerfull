from django.db.models.signals import post_save
from django.dispatch import receiver
from projects.models import Project
from .models import Folder
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Project)
def create_project_folders(sender, instance, created, **kwargs):
    """
    Создает структуру папок для проекта, когда его статус меняется на 'в работе'
    """
    try:
        logger.info(f"Signal triggered for project {instance.id} with status {instance.status}")
        
        if instance.status == 'in_progress':
            logger.info("Status is in_progress, checking existing folders")
            # Проверяем, есть ли уже созданные корневые папки
            existing_folders = Folder.objects.filter(project=instance, parent=None).exists()
            logger.info(f"Existing folders check: {existing_folders}")
            
            if not existing_folders:
                logger.info("Creating default folder structure")
                Folder.create_default_structure(instance)
                logger.info("Folder structure created successfully")
    except Exception as e:
        logger.error(f"Error creating folder structure: {str(e)}")
        # Возможно, отправить уведомление администратору
