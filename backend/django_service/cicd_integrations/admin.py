"""
CI/CD 集成管理界面
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import CICDTool, AtomicStep, PipelineExecution, StepExecution


@admin.register(CICDTool)
class CICDToolAdmin(admin.ModelAdmin):
    """CI/CD 工具管理"""
    
    list_display = [
        'name', 'tool_type', 'project', 'status_badge', 
        'last_health_check', 'created_by', 'created_at'
    ]
    list_filter = ['tool_type', 'status', 'created_at']
    search_fields = ['name', 'base_url', 'project__name']
    readonly_fields = ['created_at', 'updated_at', 'last_health_check']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'tool_type', 'base_url', 'project')
        }),
        ('认证配置', {
            'fields': ('username', 'token'),
            'classes': ('collapse',)
        }),
        ('高级配置', {
            'fields': ('config', 'metadata', 'status'),
            'classes': ('collapse',)
        }),
        ('元数据', {
            'fields': ('created_by', 'created_at', 'updated_at', 'last_health_check'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """状态徽章"""
        colors = {
            'active': 'green',
            'inactive': 'orange',
            'error': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(AtomicStep)
class AtomicStepAdmin(admin.ModelAdmin):
    """原子步骤管理"""
    
    list_display = [
        'name', 'step_type', 'pipeline', 'order', 'is_public', 
        'created_by', 'created_at'
    ]
    list_filter = ['step_type', 'pipeline', 'is_public', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'step_type', 'description', 'pipeline', 'order', 'is_public')
        }),
        ('配置', {
            'fields': ('parameters', 'config', 'conditions', 'timeout', 'retry_count'),
            'classes': ('collapse',)
        }),
        ('依赖关系', {
            'fields': ('dependencies',),
            'description': '依赖的步骤名称列表（JSON格式）'
        }),
        ('元数据', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related('pipeline', 'created_by')


@admin.register(PipelineExecution)
class PipelineExecutionAdmin(admin.ModelAdmin):
    """流水线执行管理"""
    
    list_display = [
        'id', 'pipeline', 'cicd_tool', 'status_badge', 'trigger_type',
        'triggered_by', 'duration_display', 'created_at'
    ]
    list_filter = ['status', 'trigger_type', 'cicd_tool__tool_type', 'created_at']
    search_fields = ['pipeline__name', 'external_id', 'triggered_by__username']
    readonly_fields = [
        'created_at', 'updated_at', 'started_at', 'completed_at',
        'external_id', 'external_url', 'logs'
    ]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('pipeline', 'cicd_tool', 'status', 'trigger_type')
        }),
        ('外部工具信息', {
            'fields': ('external_id', 'external_url'),
            'classes': ('collapse',)
        }),
        ('执行配置', {
            'fields': ('definition', 'parameters'),
            'classes': ('collapse',)
        }),
        ('执行结果', {
            'fields': ('logs', 'artifacts', 'test_results'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('触发信息', {
            'fields': ('triggered_by', 'trigger_data'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """状态徽章"""
        colors = {
            'pending': 'orange',
            'running': 'blue',
            'success': 'green',
            'failed': 'red',
            'cancelled': 'gray',
            'timeout': 'purple'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def duration_display(self, obj):
        """执行时长显示"""
        duration = obj.duration
        if duration:
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "-"
    duration_display.short_description = 'Duration'


@admin.register(StepExecution)
class StepExecutionAdmin(admin.ModelAdmin):
    """步骤执行管理"""
    
    list_display = [
        'id', 'pipeline_execution', 'atomic_step', 'order',
        'status_badge', 'duration_display', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['atomic_step__name', 'pipeline_execution__pipeline__name']
    readonly_fields = [
        'created_at', 'updated_at', 'started_at', 'completed_at',
        'external_id'
    ]
    
    def status_badge(self, obj):
        """状态徽章"""
        colors = {
            'pending': 'orange',
            'running': 'blue',
            'success': 'green',
            'failed': 'red',
            'skipped': 'gray',
            'cancelled': 'purple'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def duration_display(self, obj):
        """执行时长显示"""
        duration = obj.duration
        if duration:
            total_seconds = int(duration.total_seconds())
            if total_seconds >= 60:
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                return f"{minutes}m {seconds}s"
            else:
                return f"{total_seconds}s"
        return "-"
    duration_display.short_description = 'Duration'
