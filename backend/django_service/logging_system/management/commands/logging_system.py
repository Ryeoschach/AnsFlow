import asyncio
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

from logging_system.models import UnifiedLog, LogSyncPosition


class Command(BaseCommand):
    help = 'AnsFlow统一日志系统管理命令 - 初始化、验证、同步等功能'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['init', 'sync', 'status', 'clean'],
            help='执行的操作: init(初始化), sync(同步), status(状态检查), clean(清理)'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='清理操作保留的天数(默认30天)'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        try:
            if action == 'init':
                self.init_logging_system()
            elif action == 'sync':
                self.run_sync_once()
            elif action == 'status':
                self.show_status()
            elif action == 'clean':
                self.clean_old_logs(options['days'])
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 操作失败: {e}')
            )
            return
            
        self.stdout.write(
            self.style.SUCCESS(f'✅ 操作 {action} 完成')
        )

    def init_logging_system(self):
        """初始化统一日志系统"""
        self.stdout.write("🚀 初始化AnsFlow统一日志系统...")
        
        # 检查数据库表是否存在
        try:
            count = UnifiedLog.objects.count()
            self.stdout.write(f"📊 当前历史日志数量: {count}")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 数据库表检查失败: {e}')
            )
            return
            
        # 检查Redis连接
        try:
            import redis
            from django.conf import settings
            
            # 获取Redis配置
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = getattr(settings, 'REDIS_PORT', 6379)
            redis_db = getattr(settings, 'REDIS_DB', 5)
            
            r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
            r.ping()
            
            # 检查日志流长度
            stream_length = r.xlen('ansflow:logs:stream')
            self.stdout.write(f"📡 Redis Stream中日志数量: {stream_length}")
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Redis连接检查失败: {e}')
            )
            
        self.stdout.write("✅ 统一日志系统初始化检查完成")

    def show_status(self):
        """显示日志系统状态"""
        self.stdout.write("📊 AnsFlow统一日志系统状态报告")
        self.stdout.write("=" * 50)
        
        # 历史日志统计
        try:
            total_logs = UnifiedLog.objects.count()
            services = UnifiedLog.objects.values_list('service', flat=True).distinct()
            
            self.stdout.write(f"💾 历史日志总数: {total_logs}")
            self.stdout.write(f"🔧 服务数量: {len(services)}")
            self.stdout.write(f"📋 服务列表: {', '.join(services)}")
            
            # 按服务统计
            from django.db.models import Count
            service_stats = UnifiedLog.objects.values('service').annotate(
                count=Count('id')
            ).order_by('-count')
            
            self.stdout.write("📈 按服务统计:")
            for stat in service_stats:
                self.stdout.write(f"   {stat['service']}: {stat['count']} 条")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 历史日志统计失败: {e}')
            )
            
        # Redis Stream状态
        try:
            import redis
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = getattr(settings, 'REDIS_PORT', 6379)
            redis_db = getattr(settings, 'REDIS_DB', 5)
            
            r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
            stream_length = r.xlen('ansflow:logs:stream')
            
            self.stdout.write(f"📡 Redis Stream长度: {stream_length}")
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Redis Stream状态获取失败: {e}')
            )
            
        # 同步位置状态
        try:
            sync_positions = LogSyncPosition.objects.all()
            if sync_positions:
                self.stdout.write("🔄 同步位置状态:")
                for pos in sync_positions:
                    self.stdout.write(f"   {pos.service_name}: {pos.redis_stream_id}")
            else:
                self.stdout.write("⚠️  无同步位置记录")
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  同步位置状态获取失败: {e}')
            )

    def run_sync_once(self):
        """执行一次日志同步"""
        self.stdout.write("🔄 开始执行日志同步...")
        
        try:
            # 导入同步模块
            import sys
            from pathlib import Path
            
            # 添加common路径
            common_path = Path(__file__).parent.parent.parent.parent.parent.parent / 'common'
            sys.path.insert(0, str(common_path))
            
            from log_sync_service import LogSyncService
            
            # 运行同步
            async def sync_once():
                service = LogSyncService()
                try:
                    await service.initialize()
                    synced_count = await service.sync_logs_to_mysql()
                    return synced_count
                finally:
                    await service.close()
            
            synced_count = asyncio.run(sync_once())
            self.stdout.write(f"✅ 同步完成，处理了 {synced_count} 条日志")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 同步失败: {e}')
            )

    def clean_old_logs(self, days):
        """清理旧日志"""
        from datetime import timedelta
        from django.utils import timezone
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f"🧹 清理 {days} 天前的日志 (在{cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}之前)")
        
        try:
            deleted_count, _ = UnifiedLog.objects.filter(
                timestamp__lt=cutoff_date
            ).delete()
            
            self.stdout.write(f"✅ 已清理 {deleted_count} 条历史日志")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 清理失败: {e}')
            )
