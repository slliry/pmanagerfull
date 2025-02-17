import os
import subprocess
from celery import shared_task
from datetime import datetime
from django.conf import settings


@shared_task
def persist_cached_messages(chat_id=None):
    """
    Задача для сохранения кешированных сообщений в PostgreSQL.
    
    Args:
        chat_id: ID конкретного чата для сохранения. Если None, сохраняются сообщения всех чатов.
    """
    from chat.cache import MessageCache
    from chat.models import Chat
    import time

    # Добавляем задержку перед сохранением (15 минут)
    time.sleep(900)  # 15 минут = 900 секунд

    if chat_id is not None:
        # Сохраняем сообщения только для конкретного чата
        try:
            persisted_messages = MessageCache.persist_messages(chat_id)
            return f"{len(persisted_messages)} сообщений сохранено в базу данных для чата {chat_id}."
        except Chat.DoesNotExist:
            return f"Чат с ID {chat_id} не найден."

    # Если chat_id не указан, сохраняем сообщения всех чатов
    chats = Chat.objects.all()
    total_messages = 0

    for chat in chats:
        persisted_messages = MessageCache.persist_messages(chat.id)
        total_messages += len(persisted_messages)

    return f"{total_messages} сообщений сохранено в базу данных."


@shared_task
def backup_database():
    """
    Задача для создания резервной копии базы данных.
    """
    # Определяем путь к скрипту
    script_path = os.path.join(settings.BASE_DIR, "scripts", "backup_db.sh")

    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Скрипт для бэкапа базы данных не найден по пути: {script_path}")

    # Проверяем, что скрипт исполняемый
    if not os.access(script_path, os.X_OK):
        raise Exception(f"Скрипт {script_path} не имеет прав на выполнение")

    # Проверка доступности Docker более надежным способом
    try:
        # Проверяем версию Docker для подтверждения работоспособности
        docker_version = subprocess.run(
            ["/usr/bin/docker", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Docker version check: {docker_version.stdout}")
    except subprocess.CalledProcessError as e:
        raise Exception(
            f"Ошибка при проверке версии Docker:\n"
            f"Код возврата: {e.returncode}\n"
            f"STDOUT: {e.stdout}\n"
            f"STDERR: {e.stderr}"
        )
    except FileNotFoundError:
        raise Exception("Docker CLI не найден в системе")

    # Запускаем скрипт с подробным выводом
    try:
        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, 'PATH': f"/usr/bin:{os.environ.get('PATH', '')}"}
        )
        print(f"Backup script output: {result.stdout}")
        return f"Бэкап завершён успешно: {result.stdout}"
    except subprocess.CalledProcessError as e:
        raise Exception(
            f"Ошибка при выполнении бэкапа:\n"
            f"Код возврата: {e.returncode}\n"
            f"STDOUT: {e.stdout}\n"
            f"STDERR: {e.stderr}"
        )
