from django.test import TestCase
from rest_framework.test import APITestCase
from .models import Folder, File, FolderAccess

class FolderTests(APITestCase):
    def setUp(self):
        # Настройка тестовых данных
        pass

    def test_folder_creation(self):
        # Тест создания папки
        pass

    def test_folder_access(self):
        # Тест прав доступа
        pass
