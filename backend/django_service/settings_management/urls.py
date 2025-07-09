from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'audit-logs', views.AuditLogViewSet)
router.register(r'system-alerts', views.SystemAlertViewSet)
router.register(r'notification-configs', views.NotificationConfigViewSet)
router.register(r'global-configs', views.GlobalConfigViewSet)
router.register(r'backup-records', views.BackupRecordViewSet)
router.register(r'system-monitoring', views.SystemMonitoringViewSet, basename='system-monitoring')

# 新增的 API 管理和企业级设置路由
router.register(r'api-keys', views.APIKeyViewSet)
router.register(r'api-endpoints', views.APIEndpointViewSet)
router.register(r'system-settings', views.SystemSettingViewSet)
router.register(r'teams', views.TeamViewSet)
router.register(r'backup-schedules', views.BackupScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
