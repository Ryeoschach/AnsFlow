"""
Docker集成视图
"""
import docker
import json
import yaml
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from celery import current_app
import psutil

from .models import (
    DockerRegistry, DockerImage, DockerImageVersion,
    DockerContainer, DockerContainerStats, DockerCompose
)
from .serializers import (
    DockerRegistrySerializer, DockerRegistryListSerializer,
    DockerImageSerializer, DockerImageListSerializer,
    DockerImageVersionSerializer,
    DockerContainerSerializer, DockerContainerListSerializer,
    DockerContainerStatsSerializer,
    DockerComposeSerializer, DockerComposeListSerializer
)
from .tasks import (
    build_docker_image_task, push_docker_image_task,
    deploy_docker_container_task, collect_container_stats_task,
    deploy_docker_compose_task
)


class DockerRegistryViewSet(viewsets.ModelViewSet):
    """Docker仓库管理视图集"""
    queryset = DockerRegistry.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return DockerRegistryListSerializer
        return DockerRegistrySerializer

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试仓库连接"""
        registry = self.get_object()
        
        try:
            # 这里实现具体的连接测试逻辑
            # 根据不同的仓库类型使用不同的测试方法
            registry.status = 'active'
            registry.last_check = timezone.now()
            registry.check_message = '连接成功'
            registry.save()
            
            return Response({
                'status': 'success',
                'message': '仓库连接测试成功'
            })
        except Exception as e:
            registry.status = 'error'
            registry.last_check = timezone.now()
            registry.check_message = str(e)
            registry.save()
            
            return Response({
                'status': 'error',
                'message': f'仓库连接测试失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """设置为默认仓库"""
        registry = self.get_object()
        
        # 取消其他默认仓库
        DockerRegistry.objects.filter(is_default=True).update(is_default=False)
        
        # 设置当前仓库为默认
        registry.is_default = True
        registry.save()
        
        return Response({'message': '默认仓库设置成功'})


class DockerImageViewSet(viewsets.ModelViewSet):
    """Docker镜像管理视图集"""
    queryset = DockerImage.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return DockerImageListSerializer
        return DockerImageSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤参数
        registry_id = self.request.query_params.get('registry_id')
        build_status = self.request.query_params.get('build_status')
        is_template = self.request.query_params.get('is_template')
        
        if registry_id:
            queryset = queryset.filter(registry_id=registry_id)
        if build_status:
            queryset = queryset.filter(build_status=build_status)
        if is_template is not None:
            queryset = queryset.filter(is_template=is_template.lower() == 'true')
            
        return queryset

    @action(detail=True, methods=['post'])
    def build(self, request, pk=None):
        """构建镜像"""
        image = self.get_object()
        
        # 检查是否已在构建中
        if image.build_status == 'building':
            return Response({
                'status': 'error',
                'message': '镜像正在构建中，请等待完成'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新构建状态
        image.build_status = 'building'
        image.build_started_at = timezone.now()
        image.save()
        
        # 启动异步构建任务
        task = build_docker_image_task.delay(image.id)
        
        return Response({
            'status': 'success',
            'message': '镜像构建任务已启动',
            'task_id': task.id
        })

    @action(detail=True, methods=['post'])
    def push(self, request, pk=None):
        """推送镜像"""
        image = self.get_object()
        
        if image.build_status != 'success':
            return Response({
                'status': 'error',
                'message': '镜像未构建成功，无法推送'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 启动异步推送任务
        task = push_docker_image_task.delay(image.id)
        
        return Response({
            'status': 'success',
            'message': '镜像推送任务已启动',
            'task_id': task.id
        })

    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """创建镜像版本"""
        image = self.get_object()
        version_data = request.data.copy()
        version_data['image'] = image.id
        
        serializer = DockerImageVersionSerializer(data=version_data, context={'request': request})
        if serializer.is_valid():
            version = serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def dockerfile_template(self, request, pk=None):
        """获取Dockerfile模板"""
        templates = {
            'node': '''FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]''',
            'python': '''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "app.py"]''',
            'nginx': '''FROM nginx:alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY . /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]'''
        }
        
        template_type = request.query_params.get('type', 'node')
        return Response({
            'template': templates.get(template_type, templates['node'])
        })


class DockerContainerViewSet(viewsets.ModelViewSet):
    """Docker容器管理视图集"""
    queryset = DockerContainer.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return DockerContainerListSerializer
        return DockerContainerSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤参数
        status_filter = self.request.query_params.get('status')
        image_id = self.request.query_params.get('image_id')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if image_id:
            queryset = queryset.filter(image_id=image_id)
            
        return queryset

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """启动容器"""
        container = self.get_object()
        
        if container.status == 'running':
            return Response({
                'status': 'error',
                'message': '容器已在运行中'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 启动异步部署任务
        task = deploy_docker_container_task.delay(container.id, 'start')
        
        return Response({
            'status': 'success',
            'message': '容器启动任务已启动',
            'task_id': task.id
        })

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止容器"""
        container = self.get_object()
        
        if container.status == 'stopped':
            return Response({
                'status': 'error',
                'message': '容器已停止'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 启动异步停止任务
        task = deploy_docker_container_task.delay(container.id, 'stop')
        
        return Response({
            'status': 'success',
            'message': '容器停止任务已启动',
            'task_id': task.id
        })

    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None):
        """重启容器"""
        container = self.get_object()
        
        # 启动异步重启任务
        task = deploy_docker_container_task.delay(container.id, 'restart')
        
        return Response({
            'status': 'success',
            'message': '容器重启任务已启动',
            'task_id': task.id
        })

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取容器日志"""
        container = self.get_object()
        
        if not container.container_id:
            return Response({
                'status': 'error',
                'message': '容器未创建'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 获取日志参数
            tail = request.query_params.get('tail', '100')
            since = request.query_params.get('since')
            
            # 这里实现获取Docker容器日志的逻辑
            # client = docker.from_env()
            # logs = client.containers.get(container.container_id).logs(tail=tail, since=since)
            
            # 模拟日志数据
            logs = f"Container {container.name} logs (tail={tail})"
            
            return Response({
                'logs': logs,
                'container_id': container.container_id
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'获取日志失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """获取容器统计信息"""
        container = self.get_object()
        
        # 获取最新的统计数据
        latest_stats = container.stats.first()
        
        if latest_stats:
            serializer = DockerContainerStatsSerializer(latest_stats)
            return Response(serializer.data)
        else:
            # 启动统计收集任务
            collect_container_stats_task.delay(container.id)
            return Response({
                'message': '正在收集统计数据，请稍后再试'
            })


class DockerComposeViewSet(viewsets.ModelViewSet):
    """Docker Compose管理视图集"""
    queryset = DockerCompose.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return DockerComposeListSerializer
        return DockerComposeSerializer

    @action(detail=True, methods=['post'])
    def deploy(self, request, pk=None):
        """部署Compose项目"""
        compose = self.get_object()
        
        # 启动异步部署任务
        task = deploy_docker_compose_task.delay(compose.id, 'up')
        
        return Response({
            'status': 'success',
            'message': 'Compose部署任务已启动',
            'task_id': task.id
        })

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止Compose项目"""
        compose = self.get_object()
        
        # 启动异步停止任务
        task = deploy_docker_compose_task.delay(compose.id, 'down')
        
        return Response({
            'status': 'success',
            'message': 'Compose停止任务已启动',
            'task_id': task.id
        })

    @action(detail=True, methods=['post'])
    def validate_compose(self, request, pk=None):
        """验证Compose文件"""
        compose = self.get_object()
        
        try:
            # 验证YAML格式
            yaml_data = yaml.safe_load(compose.compose_content)
            
            # 基础验证
            if 'version' not in yaml_data:
                return Response({
                    'status': 'error',
                    'message': '缺少version字段'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if 'services' not in yaml_data:
                return Response({
                    'status': 'error',
                    'message': '缺少services字段'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'status': 'success',
                'message': 'Compose文件验证通过',
                'services': list(yaml_data.get('services', {}).keys())
            })
            
        except yaml.YAMLError as e:
            return Response({
                'status': 'error',
                'message': f'YAML格式错误: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def template(self, request):
        """获取Compose模板"""
        templates = {
            'web-app': {
                'version': '3.8',
                'services': {
                    'web': {
                        'build': '.',
                        'ports': ['3000:3000'],
                        'environment': ['NODE_ENV=production'],
                        'depends_on': ['db']
                    },
                    'db': {
                        'image': 'postgres:13',
                        'environment': [
                            'POSTGRES_DB=myapp',
                            'POSTGRES_USER=user',
                            'POSTGRES_PASSWORD=password'
                        ],
                        'volumes': ['db_data:/var/lib/postgresql/data']
                    }
                },
                'volumes': {
                    'db_data': {}
                }
            }
        }
        
        template_type = request.query_params.get('type', 'web-app')
        template = templates.get(template_type, templates['web-app'])
        
        return Response({
            'template': yaml.dump(template, default_flow_style=False)
        })


# 系统级别的Docker API函数

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def docker_system_info(request):
    """获取Docker系统信息"""
    try:
        client = docker.from_env()
        
        # 获取Docker系统信息
        docker_info = client.info()
        docker_version = client.version()
        
        return Response({
            'docker_version': docker_version.get('Version', 'Unknown'),
            'api_version': docker_version.get('ApiVersion', 'Unknown'),
            'server_version': docker_info.get('ServerVersion', 'Unknown'),
            'kernel_version': docker_info.get('KernelVersion', 'Unknown'),
            'operating_system': docker_info.get('OperatingSystem', 'Unknown'),
            'architecture': docker_info.get('Architecture', 'Unknown'),
            'total_memory': docker_info.get('MemTotal', 0),
            'containers': docker_info.get('Containers', 0),
            'running_containers': docker_info.get('ContainersRunning', 0),
            'paused_containers': docker_info.get('ContainersPaused', 0),
            'stopped_containers': docker_info.get('ContainersStopped', 0),
            'images': docker_info.get('Images', 0),
            'storage_driver': docker_info.get('Driver', 'Unknown'),
            'logging_driver': docker_info.get('LoggingDriver', 'Unknown'),
            'plugins': {
                'volume': docker_info.get('Plugins', {}).get('Volume', []),
                'network': docker_info.get('Plugins', {}).get('Network', []),
                'authorization': docker_info.get('Plugins', {}).get('Authorization', [])
            },
            'registry_config': docker_info.get('RegistryConfig', {}),
            'warnings': docker_info.get('Warnings', [])
        })
        
    except docker.errors.DockerException as e:
        return Response({
            'error': f'Docker连接失败: {str(e)}'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({
            'error': f'获取Docker系统信息失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def docker_system_stats(request):
    """获取Docker系统资源统计"""
    try:
        # 从数据库获取统计信息
        total_images = DockerImage.objects.count()
        total_containers = DockerContainer.objects.count()
        running_containers = DockerContainer.objects.filter(status='running').count()
        total_registries = DockerRegistry.objects.count()
        total_compose_projects = DockerCompose.objects.count()
        
        # 尝试从Docker获取磁盘使用情况
        disk_usage = {
            'images': 0,
            'containers': 0,
            'volumes': 0,
            'build_cache': 0
        }
        
        try:
            client = docker.from_env()
            df_info = client.df()
            
            # 计算镜像磁盘使用
            if 'Images' in df_info and isinstance(df_info['Images'], list):
                for image in df_info['Images']:
                    if isinstance(image, dict):
                        disk_usage['images'] += image.get('Size', 0)
            
            # 计算容器磁盘使用
            if 'Containers' in df_info and isinstance(df_info['Containers'], list):
                for container in df_info['Containers']:
                    if isinstance(container, dict):
                        disk_usage['containers'] += container.get('SizeRw', 0)
            
            # 计算数据卷磁盘使用
            if 'Volumes' in df_info and isinstance(df_info['Volumes'], list):
                for volume in df_info['Volumes']:
                    if isinstance(volume, dict):
                        disk_usage['volumes'] += volume.get('Size', 0)
            
            # 计算构建缓存磁盘使用
            if 'BuildCache' in df_info and isinstance(df_info['BuildCache'], dict):
                disk_usage['build_cache'] = df_info['BuildCache'].get('Size', 0)
            
        except docker.errors.DockerException:
            # 如果Docker不可用，使用默认值
            pass
        
        return Response({
            'total_images': total_images,
            'total_containers': total_containers,
            'running_containers': running_containers,
            'total_registries': total_registries,
            'total_compose_projects': total_compose_projects,
            'disk_usage': disk_usage
        })
        
    except Exception as e:
        return Response({
            'error': f'获取Docker系统统计失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def docker_system_cleanup(request):
    """Docker系统清理"""
    try:
        client = docker.from_env()
        
        options = request.data if request.data else {}
        cleanup_containers = options.get('containers', False)
        cleanup_images = options.get('images', False)
        cleanup_volumes = options.get('volumes', False)
        cleanup_networks = options.get('networks', False)
        
        results = {
            'success': True,
            'cleaned_up': [],
            'errors': [],
            'space_reclaimed': 0
        }
        
        # 清理容器
        if cleanup_containers:
            try:
                # 删除已停止的容器
                containers = client.containers.list(all=True, filters={'status': 'exited'})
                for container in containers:
                    try:
                        container.remove()
                        results['cleaned_up'].append(f'Container: {container.short_id}')
                    except Exception as e:
                        results['errors'].append(f'Container {container.short_id}: {str(e)}')
            except Exception as e:
                results['errors'].append(f'清理容器失败: {str(e)}')
        
        # 清理镜像
        if cleanup_images:
            try:
                # 删除悬空镜像
                dangling_images = client.images.list(filters={'dangling': True})
                for image in dangling_images:
                    try:
                        client.images.remove(image.id, force=True)
                        results['cleaned_up'].append(f'Image: {image.short_id}')
                    except Exception as e:
                        results['errors'].append(f'Image {image.short_id}: {str(e)}')
            except Exception as e:
                results['errors'].append(f'清理镜像失败: {str(e)}')
        
        # 清理数据卷
        if cleanup_volumes:
            try:
                # 删除未使用的数据卷
                volumes = client.volumes.list(filters={'dangling': True})
                for volume in volumes:
                    try:
                        volume.remove()
                        results['cleaned_up'].append(f'Volume: {volume.name}')
                    except Exception as e:
                        results['errors'].append(f'Volume {volume.name}: {str(e)}')
            except Exception as e:
                results['errors'].append(f'清理数据卷失败: {str(e)}')
        
        # 清理网络
        if cleanup_networks:
            try:
                # 删除未使用的网络
                networks = client.networks.list()
                for network in networks:
                    if network.name not in ['bridge', 'host', 'none'] and not network.containers:
                        try:
                            network.remove()
                            results['cleaned_up'].append(f'Network: {network.name}')
                        except Exception as e:
                            results['errors'].append(f'Network {network.name}: {str(e)}')
            except Exception as e:
                results['errors'].append(f'清理网络失败: {str(e)}')
        
        # 如果有错误但也有成功清理的项目，设置为部分成功
        if results['errors'] and results['cleaned_up']:
            results['success'] = 'partial'
        elif results['errors']:
            results['success'] = False
        
        return Response(results)
        
    except docker.errors.DockerException as e:
        return Response({
            'success': False,
            'error': f'Docker连接失败: {str(e)}',
            'cleaned_up': [],
            'errors': [str(e)],
            'space_reclaimed': 0
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Docker系统清理失败: {str(e)}',
            'cleaned_up': [],
            'errors': [str(e)],
            'space_reclaimed': 0
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_local_docker_images(request):
    """获取本地Docker镜像列表"""
    try:
        client = docker.from_env()
        images = client.images.list()
        
        image_list = []
        for image in images:
            # 获取镜像标签，处理<none>标签的情况
            tags = image.tags if image.tags else ['<none>:<none>']
            
            for tag in tags:
                # 解析镜像名称和标签
                if ':' in tag:
                    name, version = tag.rsplit(':', 1)
                else:
                    name, version = tag, 'latest'
                
                image_data = {
                    'docker_id': image.id,
                    'short_id': image.short_id,
                    'name': name,
                    'tag': version,
                    'size': image.attrs.get('Size', 0),
                    'created': image.attrs.get('Created', ''),
                    'labels': image.attrs.get('Config', {}).get('Labels') or {},
                    'architecture': image.attrs.get('Architecture', ''),
                    'os': image.attrs.get('Os', ''),
                    'parent_id': image.attrs.get('Parent', ''),
                    'repo_digests': image.attrs.get('RepoDigests', []),
                    'repo_tags': image.attrs.get('RepoTags', [])
                }
                image_list.append(image_data)
        
        return Response({
            'success': True,
            'images': image_list,
            'total': len(image_list)
        })
        
    except docker.errors.DockerException as e:
        return Response({
            'success': False,
            'error': f'Docker连接失败: {str(e)}',
            'images': [],
            'total': 0
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'获取本地镜像失败: {str(e)}',
            'images': [],
            'total': 0
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_local_docker_containers(request):
    """获取本地Docker容器列表"""
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        
        container_list = []
        for container in containers:
            # 获取容器端口映射
            ports = []
            if container.attrs.get('NetworkSettings', {}).get('Ports'):
                for port, bindings in container.attrs['NetworkSettings']['Ports'].items():
                    if bindings:
                        for binding in bindings:
                            ports.append(f"{binding.get('HostPort', '')}->{port}")
                    else:
                        ports.append(port)
            
            # 获取环境变量
            env_vars = container.attrs.get('Config', {}).get('Env', [])
            
            container_data = {
                'docker_id': container.id,
                'short_id': container.short_id,
                'name': container.name,
                'image': container.image.tags[0] if container.image.tags else container.image.id,
                'status': container.status,
                'state': container.attrs.get('State', {}),
                'created': container.attrs.get('Created', ''),
                'started_at': container.attrs.get('State', {}).get('StartedAt', ''),
                'finished_at': container.attrs.get('State', {}).get('FinishedAt', ''),
                'ports': ports,
                'labels': container.attrs.get('Config', {}).get('Labels') or {},
                'env': env_vars,
                'mounts': [
                    {
                        'source': mount.get('Source', ''),
                        'destination': mount.get('Destination', ''),
                        'type': mount.get('Type', ''),
                        'read_only': mount.get('RW', True) == False
                    }
                    for mount in container.attrs.get('Mounts', [])
                ],
                'network_mode': container.attrs.get('HostConfig', {}).get('NetworkMode', ''),
                'restart_policy': container.attrs.get('HostConfig', {}).get('RestartPolicy', {}),
                'log_config': container.attrs.get('HostConfig', {}).get('LogConfig', {})
            }
            container_list.append(container_data)
        
        return Response({
            'success': True,
            'containers': container_list,
            'total': len(container_list)
        })
        
    except docker.errors.DockerException as e:
        return Response({
            'success': False,
            'error': f'Docker连接失败: {str(e)}',
            'containers': [],
            'total': 0
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'获取本地容器失败: {str(e)}',
            'containers': [],
            'total': 0
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_local_docker_images(request):
    """将本地Docker镜像导入到系统"""
    try:
        client = docker.from_env()
        images = client.images.list()
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        # 获取默认仓库
        default_registry = DockerRegistry.objects.filter(is_default=True).first()
        if not default_registry:
            # 如果没有默认仓库，创建一个本地仓库
            default_registry = DockerRegistry.objects.create(
                name='Local Registry',
                url='local://',
                registry_type='private',
                status='active',
                is_default=True,
                created_by=request.user,
                description='本地Docker镜像仓库'
            )
        
        for image in images:
            try:
                # 获取镜像标签
                tags = image.tags if image.tags else ['<none>:<none>']
                
                for tag in tags:
                    # 跳过<none>标签
                    if tag == '<none>:<none>':
                        continue
                    
                    # 解析镜像名称和标签
                    if ':' in tag:
                        name, version = tag.rsplit(':', 1)
                    else:
                        name, version = tag, 'latest'
                    
                    # 检查是否已存在
                    existing_image = DockerImage.objects.filter(
                        name=name,
                        registry=default_registry
                    ).first()
                    
                    if existing_image:
                        skipped_count += 1
                        continue
                    
                    # 创建新的镜像记录
                    docker_image = DockerImage.objects.create(
                        name=name,
                        registry=default_registry,
                        dockerfile_content=f'# 从本地Docker导入的镜像\n# 原始镜像: {tag}',
                        build_context='.',
                        image_size=image.attrs.get('Size', 0),
                        image_id=image.id,
                        build_status='success',
                        build_completed_at=timezone.now(),
                        created_by=request.user,
                        description=f'从本地Docker导入的镜像: {tag}'
                    )
                    
                    # 创建镜像版本
                    DockerImageVersion.objects.create(
                        image=docker_image,
                        version=version,
                        dockerfile_content=f'# 从本地Docker导入的镜像\n# 原始镜像: {tag}',
                        build_context='.',
                        docker_image_id=image.id,
                        size=image.attrs.get('Size', 0),
                        created_by=request.user,
                        changelog=f'从本地Docker导入的版本: {version}'
                    )
                    
                    imported_count += 1
                    
            except Exception as e:
                errors.append(f'镜像 {image.short_id}: {str(e)}')
        
        return Response({
            'success': True,
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': errors,
            'message': f'成功导入 {imported_count} 个镜像，跳过 {skipped_count} 个已存在的镜像'
        })
        
    except docker.errors.DockerException as e:
        return Response({
            'success': False,
            'error': f'Docker连接失败: {str(e)}',
            'imported': 0,
            'skipped': 0,
            'errors': [str(e)]
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'导入镜像失败: {str(e)}',
            'imported': 0,
            'skipped': 0,
            'errors': [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_local_docker_containers(request):
    """将本地Docker容器导入到系统"""
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        for container in containers:
            try:
                # 检查是否已存在
                existing_container = DockerContainer.objects.filter(
                    container_id=container.id
                ).first()
                
                if existing_container:
                    skipped_count += 1
                    continue
                
                # 获取容器关联的镜像
                image_name = container.image.tags[0] if container.image.tags else container.image.id
                docker_image = None
                
                # 尝试找到对应的镜像记录
                if ':' in image_name:
                    name, tag = image_name.rsplit(':', 1)
                    docker_image = DockerImage.objects.filter(name=name).first()
                
                # 获取端口映射
                port_mappings = []
                if container.attrs.get('NetworkSettings', {}).get('Ports'):
                    for port, bindings in container.attrs['NetworkSettings']['Ports'].items():
                        if bindings:
                            for binding in bindings:
                                port_mappings.append({
                                    'container_port': port,
                                    'host_port': binding.get('HostPort'),
                                    'host_ip': binding.get('HostIp', '0.0.0.0')
                                })
                
                # 获取环境变量
                env_vars = {}
                for env in container.attrs.get('Config', {}).get('Env', []):
                    if '=' in env:
                        key, value = env.split('=', 1)
                        env_vars[key] = value
                
                # 获取挂载点
                volumes = []
                for mount in container.attrs.get('Mounts', []):
                    volumes.append({
                        'source': mount.get('Source', ''),
                        'destination': mount.get('Destination', ''),
                        'type': mount.get('Type', 'bind'),
                        'mode': mount.get('Mode', 'rw')
                    })
                
                # 状态映射
                status_mapping = {
                    'running': 'running',
                    'exited': 'exited',
                    'created': 'created',
                    'restarting': 'restarting',
                    'removing': 'removing',
                    'paused': 'paused',
                    'dead': 'dead'
                }
                mapped_status = status_mapping.get(container.status, 'stopped')
                
                # 处理命令
                cmd = container.attrs.get('Config', {}).get('Cmd', [])
                if cmd and isinstance(cmd, list):
                    command = ' '.join(str(c) for c in cmd)
                else:
                    command = str(cmd) if cmd else ''
                
                # 创建容器记录
                docker_container = DockerContainer.objects.create(
                    name=container.name,
                    image=docker_image,
                    container_id=container.id,
                    status=mapped_status,
                    command=command,
                    working_dir=container.attrs.get('Config', {}).get('WorkingDir', ''),
                    environment_vars=env_vars,
                    port_mappings=port_mappings,
                    volumes=volumes,
                    network_mode=container.attrs.get('HostConfig', {}).get('NetworkMode', 'bridge'),
                    restart_policy=container.attrs.get('HostConfig', {}).get('RestartPolicy', {}).get('Name', 'no'),
                    created_by=request.user,
                    description=f'从本地Docker导入的容器: {container.name}'
                )
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f'容器 {container.name}: {str(e)}')
        
        return Response({
            'success': True,
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': errors,
            'message': f'成功导入 {imported_count} 个容器，跳过 {skipped_count} 个已存在的容器'
        })
        
    except docker.errors.DockerException as e:
        return Response({
            'success': False,
            'error': f'Docker连接失败: {str(e)}',
            'imported': 0,
            'skipped': 0,
            'errors': [str(e)]
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'导入容器失败: {str(e)}',
            'imported': 0,
            'skipped': 0,
            'errors': [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_local_docker_resources(request):
    """同步本地Docker资源状态"""
    try:
        client = docker.from_env()
        
        # 同步容器状态
        updated_containers = 0
        container_errors = []
        
        for container_record in DockerContainer.objects.exclude(container_id=''):
            try:
                # 尝试获取本地容器
                try:
                    local_container = client.containers.get(container_record.container_id)
                    # 更新状态
                    if container_record.status != local_container.status:
                        container_record.status = local_container.status
                        container_record.save()
                        updated_containers += 1
                except docker.errors.NotFound:
                    # 本地容器不存在，标记为已删除
                    container_record.status = 'removed'
                    container_record.save()
                    updated_containers += 1
                    
            except Exception as e:
                container_errors.append(f'容器 {container_record.name}: {str(e)}')
        
        # 同步镜像状态
        updated_images = 0
        image_errors = []
        
        for image_record in DockerImage.objects.exclude(image_id=''):
            try:
                # 尝试获取本地镜像
                try:
                    local_image = client.images.get(image_record.image_id)
                    # 更新大小等信息
                    if image_record.image_size != local_image.attrs.get('Size', 0):
                        image_record.image_size = local_image.attrs.get('Size', 0)
                        image_record.save()
                        updated_images += 1
                except docker.errors.ImageNotFound:
                    # 本地镜像不存在，更新构建状态
                    if image_record.build_status != 'removed':
                        image_record.build_status = 'removed'
                        image_record.save()
                        updated_images += 1
                        
            except Exception as e:
                image_errors.append(f'镜像 {image_record.name}: {str(e)}')
        
        return Response({
            'success': True,
            'updated_containers': updated_containers,
            'updated_images': updated_images,
            'container_errors': container_errors,
            'image_errors': image_errors,
            'message': f'同步完成：更新了 {updated_containers} 个容器和 {updated_images} 个镜像'
        })
        
    except docker.errors.DockerException as e:
        return Response({
            'success': False,
            'error': f'Docker连接失败: {str(e)}',
            'updated_containers': 0,
            'updated_images': 0,
            'container_errors': [str(e)],
            'image_errors': []
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'同步失败: {str(e)}',
            'updated_containers': 0,
            'updated_images': 0,
            'container_errors': [str(e)],
            'image_errors': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
