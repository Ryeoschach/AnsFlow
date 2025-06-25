"""
URL configuration for project_management app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, EnvironmentViewSet, ProjectMembershipViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'environments', EnvironmentViewSet, basename='environment')
router.register(r'memberships', ProjectMembershipViewSet, basename='projectmembership')

urlpatterns = [
    path('', include(router.urls)),
]
