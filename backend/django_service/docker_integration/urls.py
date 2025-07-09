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
    # 系统级别的Docker API
    path('system/info/', views.docker_system_info, name='docker-system-info'),
    path('system/stats/', views.docker_system_stats, name='docker-system-stats'),
    path('system/cleanup/', views.docker_system_cleanup, name='docker-system-cleanup'),
    
    # ViewSet路由
    path('', include(router.urls)),
]
