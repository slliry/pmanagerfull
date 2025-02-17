from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectComplexityViewSet,
    ProjectViewSet,
    ProjectResponseViewSet,
    ProjectMemberViewSet,
    ProjectTemplateViewSet
)

router = DefaultRouter()
router.register(r'complexities', ProjectComplexityViewSet, basename='projectcomplexity')
router.register(r'responses', ProjectResponseViewSet, basename='projectresponse')
router.register(r'members', ProjectMemberViewSet, basename='projectmember')
router.register(r'templates', ProjectTemplateViewSet, basename='projecttemplate')
router.register(r'', ProjectViewSet, basename='project')

# Эти URL-паттерны будут доступны по:
# /api/projects/responses/{uuid}/accept/
# /api/projects/responses/{uuid}/reject/
# /api/projects/responses/{uuid}/block-chat/

urlpatterns = [
    path('', include(router.urls)),
]