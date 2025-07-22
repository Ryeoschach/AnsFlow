#!/usr/bin/env python
"""
直接测试Docker导入功能
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
from docker_integration.models import DockerRegistry, DockerImage, DockerImageVersion

def test_docker_connection():
    """测试Docker连接"""
    print("🔍 测试Docker连接...")
    try:
        client = docker.from_env()
        images = client.images.list()
        print(f"✅ Docker连接成功，找到 {len(images)} 个镜像")
        
        # 显示前5个镜像
        for i, image in enumerate(images[:5]):
            tags = image.tags if image.tags else ['<none>:<none>']
            print(f"  📦 {i+1}: {tags[0]} ({image.short_id})")
        
        return client, images
    except Exception as e:
        print(f"❌ Docker连接失败: {e}")
        return None, []

def test_import_logic():
    """测试导入逻辑"""
    print("\n🔄 测试导入逻辑...")
    
    client, images = test_docker_connection()
    if not client:
        return
    
    # 获取或创建用户
    user = User.objects.first()
    if not user:
        user = User.objects.create_user('test', 'test@example.com', 'password')
        print("📝 创建测试用户")
    
    # 获取或创建默认仓库
    default_registry = DockerRegistry.objects.filter(is_default=True).first()
    if not default_registry:
        default_registry = DockerRegistry.objects.create(
            name='Local Registry',
            url='local://',
            registry_type='private',
            status='active',
            is_default=True,
            created_by=user,
            description='本地Docker镜像仓库'
        )
        print("📝 创建默认仓库")
    else:
        print(f"✅ 使用现有默认仓库: {default_registry.name}")
    
    imported_count = 0
    skipped_count = 0
    errors = []
    
    print(f"\n🚀 开始导入 {len(images)} 个镜像...")
    
    for i, image in enumerate(images):
        try:
            print(f"\n📦 处理镜像 {i+1}/{len(images)}: {image.short_id}")
            
            # 获取镜像标签
            tags = image.tags if image.tags else ['<none>:<none>']
            print(f"  🏷️ 标签: {tags}")
            
            for tag in tags:
                # 跳过<none>标签
                if tag == '<none>:<none>':
                    print(f"  ⏭️ 跳过无标签镜像")
                    continue
                
                # 解析镜像名称和标签
                if ':' in tag:
                    name, version = tag.rsplit(':', 1)
                else:
                    name, version = tag, 'latest'
                
                print(f"  🔍 检查镜像: {name}:{version}")
                
                # 检查是否已存在
                existing_image = DockerImage.objects.filter(
                    name=name,
                    registry=default_registry
                ).first()
                
                if existing_image:
                    print(f"  ⏭️ 已存在，跳过")
                    skipped_count += 1
                    continue
                
                print(f"  ➕ 创建新镜像记录")
                
                # 创建新的镜像记录
                docker_image = DockerImage.objects.create(
                    name=name,
                    registry=default_registry,
                    dockerfile_content=f'# 从本地Docker导入的镜像\n# 原始镜像: {tag}',
                    build_context='.',
                    image_size=image.attrs.get('Size', 0),
                    image_id=image.id,
                    build_status='success',
                    created_by=user,
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
                    created_by=user,
                    changelog=f'从本地Docker导入的版本: {version}'
                )
                
                print(f"  ✅ 导入成功: {name}:{version}")
                imported_count += 1
                
        except Exception as e:
            error_msg = f'镜像 {image.short_id}: {str(e)}'
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

def check_imported_images():
    """检查导入的镜像"""
    print("\n📋 检查导入的镜像...")
    
    images = DockerImage.objects.all()
    print(f"数据库中共有 {images.count()} 个镜像")
    
    for image in images[:10]:  # 显示前10个
        print(f"  📦 {image.name} (状态: {image.build_status}, 大小: {image.image_size} bytes)")

if __name__ == "__main__":
    print("🚀 Docker导入功能直接测试")
    print("=" * 50)
    
    try:
        imported, skipped, errors = test_import_logic()
        check_imported_images()
        
        print(f"\n🎉 测试完成!")
        print(f"如果导入数量为0，可能是因为：")
        print(f"1. 所有镜像都已经存在")
        print(f"2. 所有镜像都没有标签（<none>标签）")
        print(f"3. 权限或其他错误")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
