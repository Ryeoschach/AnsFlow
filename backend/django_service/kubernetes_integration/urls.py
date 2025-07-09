"""
Kubernetes 集成 URL 配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()

# 注册视图集
router.register(r'clusters', views.KubernetesClusterViewSet, basename='kubernetes-cluster')
router.register(r'namespaces', views.KubernetesNamespaceViewSet, basename='kubernetes-namespace')
router.register(r'deployments', views.KubernetesDeploymentViewSet, basename='kubernetes-deployment')
router.register(r'services', views.KubernetesServiceViewSet, basename='kubernetes-service')
router.register(r'pods', views.KubernetesPodViewSet, basename='kubernetes-pod')
router.register(r'configmaps', views.KubernetesConfigMapViewSet, basename='kubernetes-configmap')
router.register(r'secrets', views.KubernetesSecretViewSet, basename='kubernetes-secret')

app_name = 'kubernetes_integration'

urlpatterns = [
    path('', include(router.urls)),
]
