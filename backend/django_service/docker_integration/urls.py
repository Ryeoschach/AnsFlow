"""
Docker集成URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()
router.register(r'registries', views.DockerRegistryViewSet, basename='docker-registry')
router.register(r'registry-projects', views.DockerRegistryProjectViewSet, basename='docker-registry-project')
router.register(r'images', views.DockerImageViewSet, basename='docker-image')
router.register(r'containers', views.DockerContainerViewSet, basename='docker-container')
router.register(r'compose', views.DockerComposeViewSet, basename='docker-compose')

app_name = 'docker_integration'

urlpatterns = [
    # 系统级别的Docker API
    path('system/info/', views.docker_system_info, name='docker-system-info'),
    path('system/stats/', views.docker_system_stats, name='docker-system-stats'),
    path('system/cleanup/', views.docker_system_cleanup, name='docker-system-cleanup'),
    
    # 注册表项目API
    path('registries/projects/', views.get_all_registry_projects, name='get-all-registry-projects'),
    
    # 本地Docker资源API
    path('local/images/', views.get_local_docker_images, name='get-local-docker-images'),
    path('local/containers/', views.get_local_docker_containers, name='get-local-docker-containers'),
    path('local/import/images/', views.import_local_docker_images, name='import-local-docker-images'),
    path('local/import/containers/', views.import_local_docker_containers, name='import-local-docker-containers'),
    path('local/sync/', views.sync_local_docker_resources, name='sync-local-docker-resources'),
    
    # ViewSet路由
    path('', include(router.urls)),
    
    # 兼容性路由：支持不带尾部斜杠的请求
    path('registries', views.DockerRegistryViewSet.as_view({'get': 'list', 'post': 'create'}), name='registries-compat'),
]
