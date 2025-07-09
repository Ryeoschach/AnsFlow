import psutil
import platform
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    AuditLog, SystemAlert, NotificationConfig, 
    GlobalConfig, UserProfile, BackupRecord,
    APIKey, APIEndpoint, SystemSetting, Team, 
    TeamMembership, BackupSchedule
)
from .serializers import (
    UserSerializer, UserCreateSerializer, UserProfileSerializer,
    AuditLogSerializer, SystemAlertSerializer, NotificationConfigSerializer,
    GlobalConfigSerializer, BackupRecordSerializer, SystemStatusSerializer,
    SystemMetricsSerializer, APIKeySerializer, APIEndpointSerializer,
    SystemSettingSerializer, TeamSerializer, TeamMembershipSerializer,
    BackupScheduleSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """用户管理ViewSet"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['id', 'username', 'email', 'date_joined', 'last_login']
    ordering = ['-date_joined']
    filterset_fields = ['is_active', 'is_staff']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=True, methods=['post'])
    def set_password(self, request, pk=None):
        """设置用户密码"""
        user = self.get_object()
        password = request.data.get('password')
        
        if not password or len(password) < 8:
            return Response(
                {'error': '密码长度不能少于8位'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(password)
        user.save()
        
        # 记录审计日志
        AuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            resource_type='user_password',
            resource_id=str(user.id),
            details={'target_user': user.username},
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            result='success'
        )
        
        return Response({'message': '密码设置成功'})

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """切换用户激活状态"""
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        
        # 记录审计日志
        AuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            resource_type='user_status',
            resource_id=str(user.id),
            details={
                'target_user': user.username,
                'new_status': 'active' if user.is_active else 'inactive'
            },
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            result='success'
        )
        
        return Response({
            'message': f'用户已{"激活" if user.is_active else "停用"}',
            'is_active': user.is_active
        })

    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """审计日志ViewSet（只读）"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['user__username', 'action', 'resource_type', 'resource_id']
    ordering_fields = ['timestamp', 'user', 'action', 'result']
    ordering = ['-timestamp']
    filterset_fields = ['action', 'result', 'resource_type']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 按时间范围过滤
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取审计日志统计信息"""
        # 最近7天的统计
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        stats = {
            'total_count': self.get_queryset().count(),
            'recent_count': self.get_queryset().filter(timestamp__gte=seven_days_ago).count(),
            'action_distribution': list(
                self.get_queryset()
                .filter(timestamp__gte=seven_days_ago)
                .values('action')
                .annotate(count=Count('action'))
                .order_by('-count')
            ),
            'result_distribution': list(
                self.get_queryset()
                .filter(timestamp__gte=seven_days_ago)
                .values('result')
                .annotate(count=Count('result'))
            )
        }
        
        return Response(stats)


class SystemAlertViewSet(viewsets.ModelViewSet):
    """系统告警ViewSet"""
    queryset = SystemAlert.objects.all()
    serializer_class = SystemAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['message', 'component']
    ordering_fields = ['created_at', 'severity', 'type']
    ordering = ['-created_at']
    filterset_fields = ['type', 'severity', 'resolved', 'component']

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """解决告警"""
        alert = self.get_object()
        alert.resolve(resolved_by=request.user.username)
        
        # 记录审计日志
        AuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            resource_type='system_alert',
            resource_id=str(alert.id),
            details={'action': 'resolve', 'message': alert.message[:100]},
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            result='success'
        )
        
        return Response({'message': '告警已解决'})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取告警统计信息"""
        stats = {
            'total_count': self.get_queryset().count(),
            'unresolved_count': self.get_queryset().filter(resolved=False).count(),
            'severity_distribution': list(
                self.get_queryset()
                .filter(resolved=False)
                .values('severity')
                .annotate(count=Count('severity'))
            ),
            'type_distribution': list(
                self.get_queryset()
                .filter(resolved=False)
                .values('type')
                .annotate(count=Count('type'))
            )
        }
        
        return Response(stats)

    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class NotificationConfigViewSet(viewsets.ModelViewSet):
    """通知配置ViewSet"""
    queryset = NotificationConfig.objects.all()
    serializer_class = NotificationConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'type']
    ordering_fields = ['created_at', 'name', 'type']
    ordering = ['-created_at']
    filterset_fields = ['type', 'enabled']

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """测试通知配置"""
        config = self.get_object()
        
        # 这里可以实现实际的通知测试逻辑
        # 目前返回模拟结果
        test_result = {
            'success': True,
            'message': f'测试通知已发送到 {config.name}',
            'timestamp': timezone.now()
        }
        
        # 记录审计日志
        AuditLog.objects.create(
            user=request.user.username,
            action='EXECUTE',
            resource='notification_test',
            resource_id=str(config.id),
            details={'config_name': config.name, 'config_type': config.type},
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            result='success' if test_result['success'] else 'failure'
        )
        
        return Response(test_result)

    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class GlobalConfigViewSet(viewsets.ModelViewSet):
    """全局配置ViewSet"""
    queryset = GlobalConfig.objects.all()
    serializer_class = GlobalConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['key', 'description']
    ordering_fields = ['key', 'type', 'created_at']
    ordering = ['key']
    filterset_fields = ['type', 'is_sensitive']

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """按类型获取配置"""
        config_type = request.query_params.get('type')
        if not config_type:
            return Response(
                {'error': '请指定配置类型'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        configs = self.get_queryset().filter(type=config_type)
        serializer = self.get_serializer(configs, many=True)
        return Response(serializer.data)


class BackupRecordViewSet(viewsets.ModelViewSet):
    """备份记录ViewSet"""
    queryset = BackupRecord.objects.all()
    serializer_class = BackupRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'backup_type']
    ordering_fields = ['created_at', 'name', 'file_size', 'status']
    ordering = ['-created_at']
    filterset_fields = ['status', 'backup_type']

    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """下载备份文件"""
        backup = self.get_object()
        
        if backup.status != 'completed':
            return Response(
                {'error': '备份文件未完成，无法下载'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 这里应该实现实际的文件下载逻辑
        # 目前返回下载链接
        download_url = f"/api/backups/{backup.id}/file/"
        
        # 记录审计日志
        AuditLog.objects.create(
            user=request.user.username,
            action='VIEW',
            resource='backup_download',
            resource_id=str(backup.id),
            details={'backup_name': backup.name, 'file_path': backup.file_path},
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            result='success'
        )
        
        return Response({
            'download_url': download_url,
            'file_name': backup.name,
            'file_size': backup.file_size
        })

    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SystemMonitoringViewSet(viewsets.ViewSet):
    """系统监控ViewSet"""
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """获取系统监控概览数据"""
        try:
            # 获取系统资源使用情况
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 简化的概览数据
            overview_data = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'system_health': 'healthy' if cpu_usage < 70 and memory.percent < 70 else 'warning',
                'last_updated': timezone.now()
            }
            
            return Response(overview_data)
            
        except Exception as e:
            return Response(
                {'error': f'获取系统监控数据失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def health(self, request):
        """获取系统健康状态"""
        try:
            # 获取系统资源使用情况
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 判断各组件健康状态
            cpu_status = 'healthy' if cpu_usage < 70 else ('warning' if cpu_usage < 90 else 'critical')
            memory_status = 'healthy' if memory.percent < 70 else ('warning' if memory.percent < 90 else 'critical')
            disk_status = 'healthy' if disk.percent < 80 else ('warning' if disk.percent < 95 else 'critical')
            
            # 整体健康状态
            if cpu_status == 'critical' or memory_status == 'critical' or disk_status == 'critical':
                overall_status = 'critical'
            elif cpu_status == 'warning' or memory_status == 'warning' or disk_status == 'warning':
                overall_status = 'warning'
            else:
                overall_status = 'healthy'
            
            health_data = {
                'overall_status': overall_status,
                'components': {
                    'cpu': {
                        'status': cpu_status,
                        'usage': cpu_usage,
                        'threshold': {'warning': 70, 'critical': 90}
                    },
                    'memory': {
                        'status': memory_status,
                        'usage': memory.percent,
                        'threshold': {'warning': 70, 'critical': 90}
                    },
                    'disk': {
                        'status': disk_status,
                        'usage': disk.percent,
                        'threshold': {'warning': 80, 'critical': 95}
                    }
                },
                'checked_at': timezone.now()
            }
            
            return Response(health_data)
            
        except Exception as e:
            return Response(
                {'error': f'获取系统健康状态失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def status(self, request):
        """获取系统状态"""
        try:
            # 获取系统资源使用情况
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # 获取系统信息
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            # 模拟活跃用户和运行任务数
            active_users = User.objects.filter(last_login__gte=timezone.now() - timedelta(hours=24)).count()
            running_jobs = 5  # 这里应该从实际的任务系统获取
            
            # 判断系统健康状态
            if cpu_usage > 90 or memory.percent > 90 or disk.percent > 90:
                system_health = 'critical'
            elif cpu_usage > 70 or memory.percent > 70 or disk.percent > 70:
                system_health = 'warning'
            else:
                system_health = 'healthy'
            
            status_data = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'network_io': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv,
                },
                'active_users': active_users,
                'running_jobs': running_jobs,
                'system_health': system_health,
                'uptime': str(uptime),
                'last_updated': timezone.now()
            }
            
            serializer = SystemStatusSerializer(status_data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'获取系统状态失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """获取系统指标历史数据"""
        # 这里应该从监控数据库或时序数据库获取历史数据
        # 目前返回模拟数据
        
        hours = int(request.query_params.get('hours', 24))
        now = timezone.now()
        
        metrics = []
        for i in range(hours):
            timestamp = now - timedelta(hours=hours-i)
            metrics.append({
                'timestamp': timestamp,
                'cpu_usage': 20 + (i % 30),  # 模拟数据
                'memory_usage': 30 + (i % 25),
                'disk_usage': 45 + (i % 10),
                'network_in': 1000 + (i * 100),
                'network_out': 800 + (i * 80),
            })
        
        serializer = SystemMetricsSerializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def info(self, request):
        """获取系统信息"""
        try:
            system_info = {
                'platform': platform.platform(),
                'processor': platform.processor(),
                'architecture': platform.architecture(),
                'python_version': platform.python_version(),
                'hostname': platform.node(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'disk_total': psutil.disk_usage('/').total,
                'boot_time': datetime.fromtimestamp(psutil.boot_time()),
            }
            
            return Response(system_info)
            
        except Exception as e:
            return Response(
                {'error': f'获取系统信息失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class APIKeyViewSet(viewsets.ModelViewSet):
    """API密钥管理ViewSet"""
    queryset = APIKey.objects.all()
    serializer_class = APIKeySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'key']
    ordering_fields = ['id', 'name', 'created_at', 'last_used_at']
    ordering = ['-created_at']
    filterset_fields = ['status', 'created_by']

    def perform_create(self, serializer):
        import secrets
        import hashlib
        
        # 生成API密钥和秘钥
        api_key = secrets.token_hex(32)
        api_secret = hashlib.sha256(secrets.token_bytes(64)).hexdigest()
        
        serializer.save(
            created_by=self.request.user,
            key=api_key,
            secret=api_secret
        )

    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """重新生成API密钥"""
        api_key = self.get_object()
        
        import secrets
        import hashlib
        
        api_key.key = secrets.token_hex(32)
        api_key.secret = hashlib.sha256(secrets.token_bytes(64)).hexdigest()
        api_key.usage_count = 0
        api_key.last_used_at = None
        api_key.save()
        
        return Response({
            'message': 'API密钥已重新生成',
            'key': api_key.key
        })

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """撤销API密钥"""
        api_key = self.get_object()
        api_key.status = 'inactive'
        api_key.save()
        
        return Response({'message': 'API密钥已撤销'})


class APIEndpointViewSet(viewsets.ModelViewSet):
    """API端点管理ViewSet"""
    queryset = APIEndpoint.objects.all()
    serializer_class = APIEndpointSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'path', 'description']
    ordering_fields = ['id', 'name', 'path', 'created_at']
    ordering = ['path']
    filterset_fields = ['method', 'is_enabled', 'auth_required']

    @action(detail=False, methods=['post'])
    def sync_endpoints(self, request):
        """同步系统API端点"""
        # 这里可以实现自动扫描和同步系统API端点的逻辑
        return Response({'message': 'API端点同步完成'})


class SystemSettingViewSet(viewsets.ModelViewSet):
    """系统设置管理ViewSet"""
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['key', 'description']
    ordering_fields = ['id', 'category', 'key', 'updated_at']
    ordering = ['category', 'key']
    filterset_fields = ['category', 'data_type', 'is_public']

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """按分类获取设置"""
        category = request.query_params.get('category')
        if not category:
            return Response(
                {'error': '请指定分类'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        settings = self.queryset.filter(category=category)
        if not request.user.is_staff:
            settings = settings.filter(is_public=True)
        
        serializer = self.get_serializer(settings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """批量更新设置"""
        updates = request.data.get('updates', [])
        updated_count = 0
        
        for update in updates:
            try:
                setting = SystemSetting.objects.get(key=update['key'])
                setting.value = update['value']
                setting.updated_by = request.user
                setting.save()
                updated_count += 1
            except SystemSetting.DoesNotExist:
                continue
        
        return Response({
            'message': f'成功更新 {updated_count} 项设置',
            'updated_count': updated_count
        })


class TeamViewSet(viewsets.ModelViewSet):
    """团队管理ViewSet"""
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name', 'created_at']
    ordering = ['name']
    filterset_fields = ['is_active', 'created_by']

    def perform_create(self, serializer):
        team = serializer.save(created_by=self.request.user)
        # 创建团队时，创建者自动成为 owner
        TeamMembership.objects.create(
            team=team,
            user=self.request.user,
            role='owner'
        )

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """添加团队成员"""
        team = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'member')
        
        try:
            user = User.objects.get(id=user_id)
            membership, created = TeamMembership.objects.get_or_create(
                team=team,
                user=user,
                defaults={
                    'role': role,
                    'invited_by': request.user
                }
            )
            
            if not created:
                return Response(
                    {'error': '用户已经是团队成员'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'message': '成员添加成功',
                'membership': TeamMembershipSerializer(membership).data
            })
        except User.DoesNotExist:
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """移除团队成员"""
        team = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            membership = TeamMembership.objects.get(team=team, user_id=user_id)
            membership.delete()
            return Response({'message': '成员移除成功'})
        except TeamMembership.DoesNotExist:
            return Response(
                {'error': '成员不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def update_member_role(self, request, pk=None):
        """更新成员角色"""
        team = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role')
        
        try:
            membership = TeamMembership.objects.get(team=team, user_id=user_id)
            membership.role = role
            membership.save()
            return Response({
                'message': '角色更新成功',
                'membership': TeamMembershipSerializer(membership).data
            })
        except TeamMembership.DoesNotExist:
            return Response(
                {'error': '成员不存在'},
                status=status.HTTP_404_NOT_FOUND
            )


class BackupScheduleViewSet(viewsets.ModelViewSet):
    """备份计划管理ViewSet"""
    queryset = BackupSchedule.objects.all()
    serializer_class = BackupScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name', 'created_at', 'next_run_at']
    ordering = ['-created_at']
    filterset_fields = ['frequency', 'status', 'backup_type']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """立即执行备份"""
        schedule = self.get_object()
        
        # 创建备份记录
        backup_record = BackupRecord.objects.create(
            name=f"{schedule.name}-manual-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            backup_type=schedule.backup_type,
            status='pending',
            created_by=request.user,
            file_path=f"/backups/{schedule.backup_type}/manual/",
        )
        
        # 这里可以触发实际的备份任务
        # backup_task.delay(backup_record.id)
        
        return Response({
            'message': '备份任务已启动',
            'backup_record_id': backup_record.id
        })

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """暂停备份计划"""
        schedule = self.get_object()
        schedule.status = 'paused'
        schedule.save()
        return Response({'message': '备份计划已暂停'})

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """恢复备份计划"""
        schedule = self.get_object()
        schedule.status = 'active'
        schedule.save()
        return Response({'message': '备份计划已恢复'})
