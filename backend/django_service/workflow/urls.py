"""
URL configuration for workflow app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'', views.WorkflowViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
