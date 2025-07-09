#!/usr/bin/env python3
"""
Django                 AuditLog.objects.create(
                    user=test_user,
                    action='TEST',
                    resource_type='test_resource',
                    resource_id='test_001',
                    details={'test': 'data'},
                    ip_address='127.0.0.1',
                    user_agent='test-agent',
                    result='success'
                )本
检查审计日志模型和数据
"""

import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from settings_management.models import AuditLog, SystemAlert, NotificationConfig
from django.contrib.auth.models import User

def test_models():
    """测试模型"""
    print("=" * 50)
    print("测试 Django 模型")
    print("=" * 50)
    
    # 测试审计日志模型
    try:
        audit_count = AuditLog.objects.count()
        print(f"审计日志记录数: {audit_count}")
        
        if audit_count > 0:
            latest_log = AuditLog.objects.latest('timestamp')
            print(f"最新审计日志: {latest_log.user} - {latest_log.action}")
        else:
            print("没有审计日志记录，创建一个测试记录...")
            test_user = User.objects.first()
            if test_user:
                AuditLog.objects.create(
                    user=test_user.username,
                    action='TEST',
                    resource='test_resource',
                    resource_id='test_001',
                    details={'test': 'data'},
                    ip_address='127.0.0.1',
                    user_agent='test-agent',
                    result='success'
                )
                print("测试审计日志记录已创建")
            
    except Exception as e:
        print(f"审计日志模型错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试系统告警模型
    try:
        alert_count = SystemAlert.objects.count()
        print(f"系统告警记录数: {alert_count}")
    except Exception as e:
        print(f"系统告警模型错误: {e}")
    
    # 测试通知配置模型
    try:
        config_count = NotificationConfig.objects.count()
        print(f"通知配置记录数: {config_count}")
    except Exception as e:
        print(f"通知配置模型错误: {e}")

def test_serializers():
    """测试序列化器"""
    print("\n" + "=" * 50)
    print("测试序列化器")
    print("=" * 50)
    
    try:
        from settings_management.serializers import AuditLogSerializer
        from settings_management.models import AuditLog
        
        logs = AuditLog.objects.all()[:1]
        if logs:
            log = logs[0]
            serializer = AuditLogSerializer(log)
            print(f"序列化器工作正常: {list(serializer.data.keys())}")
        else:
            print("没有审计日志数据进行序列化测试")
            
    except Exception as e:
        print(f"序列化器错误: {e}")
        import traceback
        traceback.print_exc()

def test_viewset():
    """测试视图集"""
    print("\n" + "=" * 50)
    print("测试视图集")
    print("=" * 50)
    
    try:
        from settings_management.views import AuditLogViewSet
        from django.test import RequestFactory
        from django.contrib.auth.models import User
        
        # 创建测试请求
        factory = RequestFactory()
        request = factory.get('/api/v1/settings/audit-logs/')
        
        # 添加用户到请求（模拟认证）
        user = User.objects.first()
        if user:
            request.user = user
            
            # 创建视图集实例
            viewset = AuditLogViewSet()
            viewset.request = request
            
            # 测试获取 queryset
            queryset = viewset.get_queryset()
            print(f"ViewSet queryset 计数: {queryset.count()}")
            
        else:
            print("没有用户进行视图集测试")
            
    except Exception as e:
        print(f"视图集错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"开始 Django 模型测试")
    
    test_models()
    test_serializers()
    test_viewset()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
