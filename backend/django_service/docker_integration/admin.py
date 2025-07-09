"""
Docker集成管理后台注册
"""
from django.contrib import admin
from .models import (
    DockerRegistry, DockerImage, DockerImageVersion,
    DockerContainer, DockerContainerStats, DockerCompose
)


@admin.register(DockerRegistry)
class DockerRegistryAdmin(admin.ModelAdmin):
    """Docker仓库管理后台"""
    list_display = ['name', 'registry_type', 'url', 'status', 'is_default', 'created_at']
    list_filter = ['registry_type', 'status', 'is_default']
    search_fields = ['name', 'url', 'username']
    readonly_fields = ['created_at', 'updated_at', 'last_check']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'url', 'registry_type', 'username', 'description', 'is_default')
        }),
        ('认证配置', {
            'fields': ('auth_config',),
            'classes': ('collapse',)
        }),
        ('状态信息', {
            'fields': ('status', 'last_check', 'check_message'),
            'classes': ('collapse',)
        }),
        ('元数据', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(DockerImage)
class DockerImageAdmin(admin.ModelAdmin):
    """Docker镜像管理后台"""
    list_display = ['name', 'tag', 'registry', 'build_status', 'image_size_mb', 'is_template', 'created_at']
    list_filter = ['build_status', 'is_template', 'registry', 'created_at']
    search_fields = ['name', 'tag', 'description']
    readonly_fields = ['image_id', 'image_digest', 'build_logs', 'build_started_at', 
                      'build_completed_at', 'build_duration', 'is_pushed', 'pushed_at',
                      'created_at', 'updated_at', 'full_name']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'tag', 'registry', 'description', 'is_template')
        }),
        ('构建配置', {
            'fields': ('dockerfile_content', 'build_context', 'build_args'),
        }),
        ('构建状态', {
            'fields': ('build_status', 'build_logs', 'build_started_at', 
                      'build_completed_at', 'build_duration'),
            'classes': ('collapse',)
        }),
        ('镜像信息', {
            'fields': ('image_id', 'image_digest', 'image_size', 'full_name'),
            'classes': ('collapse',)
        }),
        ('推送状态', {
            'fields': ('is_pushed', 'pushed_at'),
            'classes': ('collapse',)
        }),
        ('元数据', {
            'fields': ('labels', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def image_size_mb(self, obj):
        """显示镜像大小（MB）"""
        if obj.image_size:
            return f"{obj.image_size / (1024 * 1024):.1f} MB"
        return "-"
    image_size_mb.short_description = "镜像大小"


@admin.register(DockerImageVersion)
class DockerImageVersionAdmin(admin.ModelAdmin):
    """Docker镜像版本管理后台"""
    list_display = ['image', 'version', 'docker_image_id_short', 'image_size_mb', 'is_release', 'created_at']
    list_filter = ['is_release', 'created_at']
    search_fields = ['image__name', 'version', 'changelog']
    readonly_fields = ['checksum', 'created_at']
    
    def docker_image_id_short(self, obj):
        """显示短镜像ID"""
        if obj.docker_image_id:
            return obj.docker_image_id[:12]
        return "-"
    docker_image_id_short.short_description = "镜像ID"
    
    def image_size_mb(self, obj):
        """显示镜像大小（MB）"""
        if obj.image_size:
            return f"{obj.image_size / (1024 * 1024):.1f} MB"
        return "-"
    image_size_mb.short_description = "镜像大小"


@admin.register(DockerContainer)
class DockerContainerAdmin(admin.ModelAdmin):
    """Docker容器管理后台"""
    list_display = ['name', 'image', 'status', 'container_id_short', 'started_at', 'created_at']
    list_filter = ['status', 'restart_policy', 'auto_remove', 'created_at']
    search_fields = ['name', 'image__name', 'description']
    readonly_fields = ['container_id', 'exit_code', 'started_at', 'finished_at', 
                      'created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'image', 'description')
        }),
        ('运行配置', {
            'fields': ('command', 'working_dir', 'environment_vars', 
                      'port_mappings', 'volumes', 'network_mode'),
        }),
        ('资源限制', {
            'fields': ('memory_limit', 'cpu_limit'),
            'classes': ('collapse',)
        }),
        ('运行状态', {
            'fields': ('status', 'container_id', 'exit_code', 'started_at', 'finished_at'),
            'classes': ('collapse',)
        }),
        ('运行策略', {
            'fields': ('restart_policy', 'auto_remove'),
            'classes': ('collapse',)
        }),
        ('元数据', {
            'fields': ('labels', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def container_id_short(self, obj):
        """显示短容器ID"""
        if obj.container_id:
            return obj.container_id[:12]
        return "-"
    container_id_short.short_description = "容器ID"


@admin.register(DockerContainerStats)
class DockerContainerStatsAdmin(admin.ModelAdmin):
    """Docker容器统计管理后台"""
    list_display = ['container', 'cpu_usage_percent', 'memory_percent', 
                   'network_io_mb', 'block_io_mb', 'pids', 'recorded_at']
    list_filter = ['recorded_at']
    search_fields = ['container__name']
    readonly_fields = ['recorded_at']
    
    def network_io_mb(self, obj):
        """显示网络IO（MB）"""
        total = obj.network_rx_bytes + obj.network_tx_bytes
        return f"{total / (1024 * 1024):.1f} MB"
    network_io_mb.short_description = "网络IO"
    
    def block_io_mb(self, obj):
        """显示磁盘IO（MB）"""
        total = obj.block_read_bytes + obj.block_write_bytes
        return f"{total / (1024 * 1024):.1f} MB"
    block_io_mb.short_description = "磁盘IO"


@admin.register(DockerCompose)
class DockerComposeAdmin(admin.ModelAdmin):
    """Docker Compose管理后台"""
    list_display = ['name', 'status', 'services_count', 'networks_count', 'volumes_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'description', 'status')
        }),
        ('配置文件', {
            'fields': ('compose_content', 'environment_file', 'working_directory'),
        }),
        ('项目信息', {
            'fields': ('services', 'networks', 'volumes'),
            'classes': ('collapse',)
        }),
        ('元数据', {
            'fields': ('labels', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def services_count(self, obj):
        """显示服务数量"""
        return len(obj.services) if obj.services else 0
    services_count.short_description = "服务数"
    
    def networks_count(self, obj):
        """显示网络数量"""
        return len(obj.networks) if obj.networks else 0
    networks_count.short_description = "网络数"
    
    def volumes_count(self, obj):
        """显示数据卷数量"""
        return len(obj.volumes) if obj.volumes else 0
    volumes_count.short_description = "数据卷数"
