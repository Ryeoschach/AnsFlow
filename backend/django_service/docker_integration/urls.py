"""
Docker集成URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()
router.register(r'registries', views.DockerRegistryViewSet, basename='docker-registry')
router.register(r'images', views.DockerImageViewSet, basename='docker-image')
router.register(r'containers', views.DockerContainerViewSet, basename='docker-container')
router.register(r'compose', views.DockerComposeViewSet, basename='docker-compose')

app_name = 'docker_integration'

urlpatterns = [
    path('', include(router.urls)),
]
