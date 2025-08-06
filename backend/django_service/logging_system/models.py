from django.db import models
from django.utils import timezone


class UnifiedLog(models.Model):
    """统一日志模型"""
    
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'), 
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    log_id = models.CharField(max_length=255, unique=True, help_text="唯一日志ID")
    timestamp = models.DateTimeField(help_text="日志时间戳")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, help_text="日志级别")
    service = models.CharField(max_length=50, help_text="服务名称")
    component = models.CharField(max_length=100, blank=True, null=True, help_text="组件名称")
    module = models.CharField(max_length=100, blank=True, null=True, help_text="模块名称")
    message = models.TextField(help_text="日志消息")
    execution_id = models.IntegerField(blank=True, null=True, help_text="执行ID")
    trace_id = models.CharField(max_length=100, blank=True, null=True, help_text="追踪ID")
    extra_data = models.JSONField(blank=True, null=True, help_text="额外数据")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    
    class Meta:
        db_table = 'unified_logs'
        ordering = ['-timestamp']
        verbose_name = "统一日志"
        verbose_name_plural = "统一日志"
        indexes = [
            models.Index(fields=['timestamp'], name='idx_unified_logs_timestamp'),
            models.Index(fields=['service'], name='idx_unified_logs_service'),
            models.Index(fields=['level'], name='idx_unified_logs_level'),
            models.Index(fields=['execution_id'], name='idx_unified_logs_execution_id'),
            models.Index(fields=['trace_id'], name='idx_unified_logs_trace_id'),
        ]
    
    def __str__(self):
        return f"[{self.level}] {self.service} - {self.message[:50]}..."

    @classmethod
    def create_from_log_entry(cls, log_entry):
        """从LogEntry对象创建数据库记录"""
        return cls.objects.create(
            log_id=log_entry.id,
            timestamp=log_entry.timestamp,
            level=log_entry.level,
            service=log_entry.service,
            component=log_entry.component,
            module=log_entry.module,
            message=log_entry.message,
            execution_id=log_entry.execution_id,
            trace_id=log_entry.trace_id,
            extra_data=log_entry.extra_data
        )


class LogSyncPosition(models.Model):
    """日志同步位置记录"""
    
    service_name = models.CharField(max_length=100, unique=True, help_text="服务名称")
    redis_stream_id = models.CharField(max_length=255, help_text="Redis Stream消息ID")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    class Meta:
        db_table = 'log_sync_position'
        verbose_name = "日志同步位置"
        verbose_name_plural = "日志同步位置"
        
    def __str__(self):
        return f"{self.service_name}: {self.redis_stream_id}"
