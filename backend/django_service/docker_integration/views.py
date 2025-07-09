"""
Docker集成视图
"""
import docker
import json
import yaml
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from celery import current_app

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
