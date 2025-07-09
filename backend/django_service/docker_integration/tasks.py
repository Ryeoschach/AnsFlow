"""
Docker集成异步任务
"""
import os
import docker
import subprocess
import json
import yaml
import logging
from datetime import datetime
from celery import shared_task
from django.utils import timezone
from django.conf import settings

from .models import (
    DockerRegistry, DockerImage, DockerImageVersion,
    DockerContainer, DockerContainerStats, DockerCompose
)

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def build_docker_image_task(self, image_id):
    """异步构建Docker镜像"""
    try:
        image = DockerImage.objects.get(id=image_id)
        logger.info(f"开始构建镜像: {image.name}:{image.tag}")
        
        # 更新构建状态
        image.build_status = 'building'
        image.build_started_at = timezone.now()
        image.save()
        
        # 创建临时构建目录
        build_dir = f"/tmp/docker_build_{image_id}"
        os.makedirs(build_dir, exist_ok=True)
        
        # 写入Dockerfile
        dockerfile_path = os.path.join(build_dir, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write(image.dockerfile_content)
        
        # 初始化Docker客户端
        client = docker.from_env()
        
        # 构建镜像
        try:
            # 构建参数
            build_args = image.build_args or {}
            tag = f"{image.name}:{image.tag}"
            
            # 执行构建
            build_result = client.images.build(
                path=build_dir,
                tag=tag,
                dockerfile='Dockerfile',
                buildargs=build_args,
                rm=True,
                forcerm=True
            )
            
            built_image = build_result[0]
            
            # 更新镜像信息
            image.image_id = built_image.id
            image.image_size = built_image.attrs.get('Size', 0)
            image.build_status = 'success'
            image.build_completed_at = timezone.now()
            
            # 计算构建耗时
            if image.build_started_at:
                duration = (image.build_completed_at - image.build_started_at).total_seconds()
                image.build_duration = int(duration)
            
            image.build_logs = f"镜像构建成功: {built_image.id[:12]}"
            image.save()
            
            logger.info(f"镜像构建成功: {image.name}:{image.tag}")
            
            # 创建版本记录
            DockerImageVersion.objects.create(
                image=image,
                version=image.tag,
                dockerfile_content=image.dockerfile_content,
                build_context=image.build_context,
                build_args=image.build_args,
                docker_image_id=image.image_id,
                image_size=image.image_size,
                created_by=image.created_by
            )
            
            return {
                'status': 'success',
                'image_id': image.image_id,
                'image_size': image.image_size
            }
            
        except docker.errors.BuildError as e:
            error_msg = str(e)
            image.build_status = 'failed'
            image.build_completed_at = timezone.now()
            image.build_logs = f"构建失败: {error_msg}"
            image.save()
            
            logger.error(f"镜像构建失败: {error_msg}")
            return {
                'status': 'failed',
                'error': error_msg
            }
        
        finally:
            # 清理临时目录
            try:
                import shutil
                shutil.rmtree(build_dir)
            except Exception as e:
                logger.warning(f"清理构建目录失败: {e}")
                
    except DockerImage.DoesNotExist:
        logger.error(f"镜像不存在: {image_id}")
        return {'status': 'error', 'message': '镜像不存在'}
    except Exception as e:
        logger.error(f"构建镜像时发生错误: {e}")
        
        # 更新失败状态
        try:
            image = DockerImage.objects.get(id=image_id)
            image.build_status = 'failed'
            image.build_completed_at = timezone.now()
            image.build_logs = f"构建异常: {str(e)}"
            image.save()
        except:
            pass
            
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True)
def push_docker_image_task(self, image_id):
    """异步推送Docker镜像"""
    try:
        image = DockerImage.objects.get(id=image_id)
        logger.info(f"开始推送镜像: {image.name}:{image.tag}")
        
        if not image.image_id:
            return {'status': 'error', 'message': '镜像未构建'}
        
        client = docker.from_env()
        
        # 获取镜像
        docker_image = client.images.get(image.image_id)
        
        # 构造推送标签
        registry = image.registry
        if registry.registry_type == 'dockerhub':
            push_tag = f"{image.name}:{image.tag}"
        else:
            registry_url = registry.url.replace('https://', '').replace('http://', '')
            push_tag = f"{registry_url}/{image.name}:{image.tag}"
        
        # 为镜像打标签
        docker_image.tag(push_tag)
        
        # 推送镜像
        push_result = client.images.push(
            push_tag,
            auth_config=registry.auth_config if registry.auth_config else None
        )
        
        # 更新推送状态
        image.is_pushed = True
        image.pushed_at = timezone.now()
        image.save()
        
        logger.info(f"镜像推送成功: {push_tag}")
        return {
            'status': 'success',
            'push_tag': push_tag
        }
        
    except DockerImage.DoesNotExist:
        logger.error(f"镜像不存在: {image_id}")
        return {'status': 'error', 'message': '镜像不存在'}
    except Exception as e:
        logger.error(f"推送镜像时发生错误: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True)
def deploy_docker_container_task(self, container_id, action):
    """异步部署Docker容器"""
    try:
        container = DockerContainer.objects.get(id=container_id)
        logger.info(f"容器操作: {action} - {container.name}")
        
        client = docker.from_env()
        
        if action == 'start':
            # 启动容器
            if container.container_id:
                # 容器已存在，直接启动
                docker_container = client.containers.get(container.container_id)
                docker_container.start()
            else:
                # 创建并启动新容器
                
                # 构建镜像名称
                image_name = container.image.full_name
                
                # 端口映射
                ports = {}
                for mapping in container.port_mappings:
                    if isinstance(mapping, dict) and 'host' in mapping and 'container' in mapping:
                        ports[f"{mapping['container']}/tcp"] = mapping['host']
                
                # 数据卷
                volumes = {}
                for volume in container.volumes:
                    if isinstance(volume, dict) and 'host' in volume and 'container' in volume:
                        volumes[volume['host']] = {'bind': volume['container'], 'mode': 'rw'}
                
                # 创建容器
                docker_container = client.containers.create(
                    image=image_name,
                    name=container.name,
                    command=container.command if container.command else None,
                    environment=container.environment_vars,
                    ports=ports,
                    volumes=volumes,
                    working_dir=container.working_dir if container.working_dir else None,
                    network_mode=container.network_mode,
                    restart_policy={'Name': container.restart_policy},
                    remove=container.auto_remove,
                    mem_limit=container.memory_limit if container.memory_limit else None,
                    cpu_period=100000,  # 默认CPU周期
                    cpu_quota=int(float(container.cpu_limit) * 100000) if container.cpu_limit else None
                )
                
                # 更新容器ID
                container.container_id = docker_container.id
                
                # 启动容器
                docker_container.start()
            
            # 更新状态
            container.status = 'running'
            container.started_at = timezone.now()
            
        elif action == 'stop':
            if container.container_id:
                docker_container = client.containers.get(container.container_id)
                docker_container.stop()
                
                container.status = 'stopped'
                container.finished_at = timezone.now()
        
        elif action == 'restart':
            if container.container_id:
                docker_container = client.containers.get(container.container_id)
                docker_container.restart()
                
                container.status = 'running'
                container.started_at = timezone.now()
        
        container.save()
        
        logger.info(f"容器操作成功: {action} - {container.name}")
        return {
            'status': 'success',
            'action': action,
            'container_status': container.status
        }
        
    except DockerContainer.DoesNotExist:
        logger.error(f"容器不存在: {container_id}")
        return {'status': 'error', 'message': '容器不存在'}
    except Exception as e:
        logger.error(f"容器操作时发生错误: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True)
def collect_container_stats_task(self, container_id):
    """收集容器统计信息"""
    try:
        container = DockerContainer.objects.get(id=container_id)
        
        if not container.container_id:
            return {'status': 'error', 'message': '容器未创建'}
        
        client = docker.from_env()
        docker_container = client.containers.get(container.container_id)
        
        # 获取统计信息
        stats = docker_container.stats(stream=False)
        
        # 解析统计数据
        cpu_stats = stats.get('cpu_stats', {})
        memory_stats = stats.get('memory_stats', {})
        networks = stats.get('networks', {})
        blkio_stats = stats.get('blkio_stats', {})
        
        # 计算CPU使用率
        cpu_delta = cpu_stats.get('cpu_usage', {}).get('total_usage', 0) - \
                   cpu_stats.get('precpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0)
        system_delta = cpu_stats.get('system_cpu_usage', 0) - \
                      cpu_stats.get('precpu_stats', {}).get('system_cpu_usage', 0)
        
        cpu_usage_percent = 0
        if system_delta > 0 and cpu_delta > 0:
            cpu_count = len(cpu_stats.get('cpu_usage', {}).get('percpu_usage', []))
            cpu_usage_percent = (cpu_delta / system_delta) * cpu_count * 100
        
        # 计算内存使用率
        memory_usage = memory_stats.get('usage', 0)
        memory_limit = memory_stats.get('limit', 0)
        memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
        
        # 网络统计
        network_rx_bytes = sum(net.get('rx_bytes', 0) for net in networks.values())
        network_tx_bytes = sum(net.get('tx_bytes', 0) for net in networks.values())
        
        # 磁盘统计
        block_read_bytes = 0
        block_write_bytes = 0
        for io_stat in blkio_stats.get('io_service_bytes_recursive', []):
            if io_stat.get('op') == 'Read':
                block_read_bytes += io_stat.get('value', 0)
            elif io_stat.get('op') == 'Write':
                block_write_bytes += io_stat.get('value', 0)
        
        # 进程数
        pids = stats.get('pids_stats', {}).get('current', 0)
        
        # 保存统计数据
        DockerContainerStats.objects.create(
            container=container,
            cpu_usage_percent=round(cpu_usage_percent, 2),
            cpu_system_usage=cpu_stats.get('system_cpu_usage', 0),
            cpu_total_usage=cpu_stats.get('cpu_usage', {}).get('total_usage', 0),
            memory_usage=memory_usage,
            memory_limit=memory_limit,
            memory_percent=round(memory_percent, 2),
            network_rx_bytes=network_rx_bytes,
            network_tx_bytes=network_tx_bytes,
            block_read_bytes=block_read_bytes,
            block_write_bytes=block_write_bytes,
            pids=pids
        )
        
        logger.info(f"收集容器统计信息成功: {container.name}")
        return {
            'status': 'success',
            'stats': {
                'cpu_usage_percent': cpu_usage_percent,
                'memory_percent': memory_percent,
                'memory_usage': memory_usage,
                'memory_limit': memory_limit
            }
        }
        
    except DockerContainer.DoesNotExist:
        logger.error(f"容器不存在: {container_id}")
        return {'status': 'error', 'message': '容器不存在'}
    except Exception as e:
        logger.error(f"收集容器统计信息时发生错误: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True)
def deploy_docker_compose_task(self, compose_id, action):
    """部署Docker Compose项目"""
    try:
        compose = DockerCompose.objects.get(id=compose_id)
        logger.info(f"Compose操作: {action} - {compose.name}")
        
        # 创建工作目录
        work_dir = f"/tmp/compose_{compose_id}"
        os.makedirs(work_dir, exist_ok=True)
        
        # 写入docker-compose.yml
        compose_file = os.path.join(work_dir, 'docker-compose.yml')
        with open(compose_file, 'w') as f:
            f.write(compose.compose_content)
        
        # 写入.env文件
        if compose.environment_file:
            env_file = os.path.join(work_dir, '.env')
            with open(env_file, 'w') as f:
                f.write(compose.environment_file)
        
        # 执行docker-compose命令
        cmd = ['docker-compose', '-f', compose_file, '-p', compose.name]
        
        if action == 'up':
            cmd.extend(['up', '-d'])
            new_status = 'running'
        elif action == 'down':
            cmd.extend(['down'])
            new_status = 'stopped'
        else:
            return {'status': 'error', 'message': f'不支持的操作: {action}'}
        
        # 执行命令
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            # 更新状态
            compose.status = new_status
            compose.save()
            
            # 解析服务信息
            if action == 'up':
                try:
                    # 获取服务列表
                    ps_cmd = ['docker-compose', '-f', compose_file, '-p', compose.name, 'ps', '--format', 'json']
                    ps_result = subprocess.run(ps_cmd, cwd=work_dir, capture_output=True, text=True)
                    
                    if ps_result.returncode == 0:
                        services = []
                        for line in ps_result.stdout.strip().split('\n'):
                            if line:
                                try:
                                    service_info = json.loads(line)
                                    services.append(service_info.get('Service', ''))
                                except json.JSONDecodeError:
                                    pass
                        
                        compose.services = list(set(services))
                        compose.save()
                except Exception as e:
                    logger.warning(f"获取服务列表失败: {e}")
            
            logger.info(f"Compose操作成功: {action} - {compose.name}")
            return {
                'status': 'success',
                'action': action,
                'output': result.stdout
            }
        else:
            logger.error(f"Compose操作失败: {result.stderr}")
            compose.status = 'error'
            compose.save()
            
            return {
                'status': 'error',
                'message': result.stderr,
                'output': result.stdout
            }
        
    except DockerCompose.DoesNotExist:
        logger.error(f"Compose项目不存在: {compose_id}")
        return {'status': 'error', 'message': 'Compose项目不存在'}
    except subprocess.TimeoutExpired:
        logger.error(f"Compose操作超时: {compose_id}")
        return {'status': 'error', 'message': '操作超时'}
    except Exception as e:
        logger.error(f"Compose操作时发生错误: {e}")
        return {'status': 'error', 'message': str(e)}
    finally:
        # 清理工作目录
        try:
            import shutil
            shutil.rmtree(work_dir)
        except Exception as e:
            logger.warning(f"清理工作目录失败: {e}")


@shared_task
def cleanup_old_container_stats():
    """清理旧的容器统计数据"""
    try:
        # 保留最近7天的数据
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=7)
        
        deleted_count = DockerContainerStats.objects.filter(
            recorded_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"清理了 {deleted_count} 条旧的容器统计数据")
        return {'status': 'success', 'deleted_count': deleted_count}
        
    except Exception as e:
        logger.error(f"清理统计数据时发生错误: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def monitor_all_containers():
    """监控所有运行中的容器"""
    try:
        running_containers = DockerContainer.objects.filter(status='running')
        
        for container in running_containers:
            # 异步收集每个容器的统计信息
            collect_container_stats_task.delay(container.id)
        
        logger.info(f"启动了 {len(running_containers)} 个容器的监控任务")
        return {
            'status': 'success',
            'container_count': len(running_containers)
        }
        
    except Exception as e:
        logger.error(f"监控容器时发生错误: {e}")
        return {'status': 'error', 'message': str(e)}
