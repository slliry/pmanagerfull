from django.urls import path
from .views import TaskViewSet
from rest_framework import routers

# Используем SimpleRouter вместо DefaultRouter
router = routers.SimpleRouter()
router.register('', TaskViewSet, basename='task')

urlpatterns = router.urls