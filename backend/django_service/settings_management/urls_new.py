"""
AnsFlow设置管理URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# 使用绝对导入路径避免循环导入
from settings_management.views import (
    UserViewSet,
    AuditLogViewSet,
    SystemAlertViewSet,
    NotificationConfigViewSet,
    GlobalConfigViewSet,
    BackupRecordViewSet,
    SystemMonitoringViewSet,
    APIKeyViewSet,
    APIEndpointViewSet,
    SystemSettingViewSet,
    TeamViewSet,
    BackupScheduleViewSet,
)

router = DefaultRouter()

# 注册所有ViewSet
router.register(r'users', UserViewSet)
router.register(r'audit-logs', AuditLogViewSet)
router.register(r'system-alerts', SystemAlertViewSet)
router.register(r'notification-configs', NotificationConfigViewSet)
router.register(r'global-configs', GlobalConfigViewSet)
router.register(r'backup-records', BackupRecordViewSet)
router.register(r'system-monitoring', SystemMonitoringViewSet, basename='system-monitoring')
router.register(r'api-keys', APIKeyViewSet)
router.register(r'api-endpoints', APIEndpointViewSet)
router.register(r'system-settings', SystemSettingViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'backup-schedules', BackupScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Phase 3: 日志管理API
    path('logging/', include('settings_management.logging_urls')),
]
