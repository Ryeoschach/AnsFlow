from django.urls import path, include
from rest_framework.routers import DefaultRouter

# 直接从views.py文件导入，避免循环导入
# 使用相对导入指向父级目录的views.py文件
from ..views import (
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
router.register(r'users', UserViewSet)
router.register(r'audit-logs', AuditLogViewSet)
router.register(r'system-alerts', SystemAlertViewSet)
router.register(r'notification-configs', NotificationConfigViewSet)
router.register(r'global-configs', GlobalConfigViewSet)
router.register(r'backup-records', BackupRecordViewSet)
router.register(r'system-monitoring', SystemMonitoringViewSet, basename='system-monitoring')

# 新增的 API 管理和企业级设置路由
router.register(r'api-keys', APIKeyViewSet)
router.register(r'api-endpoints', APIEndpointViewSet)
router.register(r'system-settings', SystemSettingViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'backup-schedules', BackupScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # 日志管理API
    path('logging/', include('settings_management.logging_urls')),
]
