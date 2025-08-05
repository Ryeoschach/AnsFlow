#!/usr/bin/env python
"""
Docker容器导入功能测试
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

import docker
from django.contrib.auth.models import User
from docker_integration.models import DockerRegistry, DockerImage, DockerContainer

def test_docker_connection():
    """测试Docker连接"""
    print("🔍 测试Docker连接...")
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        print(f"✅ Docker连接成功，找到 {len(containers)} 个容器")
        
        # 显示前5个容器
        for i, container in enumerate(containers[:5]):
            status = container.status
            name = container.name
            image = container.image.tags[0] if container.image.tags else container.image.id[:12]
            print(f"  📦 {i+1}: {name} ({image}) - {status}")
        
        return client, containers
    except Exception as e:
        print(f"❌ Docker连接失败: {e}")
        return None, []

def test_container_import():
    """测试容器导入逻辑"""
    print("\n🔄 测试容器导入逻辑...")
    
    client, containers = test_docker_connection()
    if not client:
        return
    
    # 获取或创建用户
    user = User.objects.first()
    if not user:
        user = User.objects.create_user('test', 'test@example.com', 'password')
        print("📝 创建测试用户")
    
    imported_count = 0
    skipped_count = 0
    errors = []
    
    print(f"\n🚀 开始导入 {len(containers)} 个容器...")
    
    for i, container in enumerate(containers):
        try:
            print(f"\n📦 处理容器 {i+1}/{len(containers)}: {container.name}")
            
            # 获取容器信息
            container_id = container.id
            name = container.name
            image_name = container.image.tags[0] if container.image.tags else container.image.id[:12]
            status = container.status
            
            print(f"  🏷️ 名称: {name}")
            print(f"  🖼️ 镜像: {image_name}")
            print(f"  📊 状态: {status}")
            print(f"  🆔 ID: {container_id[:12]}...")
            
            # 检查是否已存在
            existing_container = DockerContainer.objects.filter(
                name=name
            ).first()
            
            if existing_container:
                print(f"  ⏭️ 容器已存在，跳过")
                skipped_count += 1
                continue
            
            # 找到对应的镜像记录
            docker_image = None
            if ':' in image_name:
                img_name, img_tag = image_name.rsplit(':', 1)
            else:
                img_name, img_tag = image_name, 'latest'
            
            # 查找数据库中的镜像记录
            docker_image = DockerImage.objects.filter(name=img_name).first()
            
            if not docker_image:
                print(f"  ⚠️ 未找到对应的镜像记录: {img_name}")
                # 我们可以跳过这个容器或者创建一个临时镜像记录
                errors.append(f'容器 {name}: 未找到对应的镜像记录 {img_name}')
                continue
            
            print(f"  ✅ 找到对应镜像: {docker_image.name}")
            
            # 获取容器详细信息
            container_info = container.attrs
            
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
            
            mapped_status = status_mapping.get(status, 'stopped')
            
            # 获取端口映射
            port_mappings = []
            if container_info.get('NetworkSettings', {}).get('Ports'):
                ports = container_info['NetworkSettings']['Ports']
                for container_port, host_bindings in ports.items():
                    if host_bindings:
                        for binding in host_bindings:
                            port_mappings.append({
                                'container_port': container_port,
                                'host_port': binding.get('HostPort'),
                                'host_ip': binding.get('HostIp', '0.0.0.0')
                            })
            
            # 获取环境变量
            env_vars = {}
            if container_info.get('Config', {}).get('Env'):
                for env in container_info['Config']['Env']:
                    if '=' in env:
                        key, value = env.split('=', 1)
                        env_vars[key] = value
            
            # 获取数据卷
            volumes = []
            if container_info.get('Mounts'):
                for mount in container_info['Mounts']:
                    volumes.append({
                        'source': mount.get('Source'),
                        'destination': mount.get('Destination'),
                        'type': mount.get('Type'),
                        'mode': mount.get('Mode', 'rw')
                    })
            
            print(f"  ➕ 创建容器记录")
            
            # 创建容器记录
            cmd = container_info.get('Config', {}).get('Cmd', [])
            if cmd and isinstance(cmd, list):
                command = ' '.join(str(c) for c in cmd)
            else:
                command = str(cmd) if cmd else ''
            
            docker_container = DockerContainer.objects.create(
                name=name,
                image=docker_image,
                container_id=container_id,
                command=command,
                working_dir=container_info.get('Config', {}).get('WorkingDir', ''),
                environment_vars=env_vars,
                port_mappings=port_mappings,
                volumes=volumes,
                network_mode=container_info.get('HostConfig', {}).get('NetworkMode', 'bridge'),
                status=mapped_status,
                created_by=user,
                description=f'从本地Docker导入的容器: {name}'
            )
            
            print(f"  ✅ 导入成功: {name}")
            imported_count += 1
            
        except Exception as e:
            error_msg = f'容器 {container.name}: {str(e)}'
            errors.append(error_msg)
            print(f"  ❌ 错误: {error_msg}")
    
    print(f"\n📊 导入结果:")
    print(f"  ✅ 导入成功: {imported_count} 个")
    print(f"  ⏭️ 已存在跳过: {skipped_count} 个")
    print(f"  ❌ 错误: {len(errors)} 个")
    
    if errors:
        print("  错误详情:")
        for error in errors:
            print(f"    - {error}")
    
    return imported_count, skipped_count, errors

def check_imported_containers():
    """检查导入的容器"""
    print("\n📋 检查导入的容器...")
    
    containers = DockerContainer.objects.all()
    print(f"数据库中共有 {containers.count()} 个容器")
    
    for container in containers[:10]:  # 显示前10个
        print(f"  📦 {container.name} ({container.status}) - 镜像: {container.image.name}")

if __name__ == "__main__":
    print("🚀 Docker容器导入功能测试")
    print("=" * 50)
    
    try:
        imported, skipped, errors = test_container_import()
        check_imported_containers()
        
        print(f"\n🎉 测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
