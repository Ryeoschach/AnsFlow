#!/usr/bin/env python3
"""
修复Docker Push步骤注册表选择问题
问题：Docker push步骤没有使用用户选择的注册表，而是使用了默认的Docker Hub
"""

import sys
import os

# 设置Django环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from docker_integration.models import DockerRegistry
from cicd_integrations.models import AtomicStep

def analyze_docker_push_issue():
    """分析Docker Push问题"""
    print("🔍 分析Docker Push注册表选择问题...")
    print("=" * 60)
    
    # 1. 检查Docker Push步骤
    docker_push_steps = AtomicStep.objects.filter(step_type='docker_push')
    print(f"\n📦 发现 {docker_push_steps.count()} 个Docker Push步骤:")
    
    for step in docker_push_steps:
        print(f"\n步骤ID: {step.id}")
        print(f"名称: {step.name}")
        print(f"参数: {step.parameters}")
        
        # 获取指定的注册表ID
        registry_id = step.parameters.get('registry_id')
        if registry_id:
            try:
                registry = DockerRegistry.objects.get(id=registry_id)
                print(f"✅ 指定注册表: {registry.name} ({registry.url})")
            except DockerRegistry.DoesNotExist:
                print(f"❌ 注册表ID {registry_id} 不存在")
        else:
            print("⚠️  未指定注册表ID")
    
    # 2. 检查所有注册表
    print(f"\n🏪 所有可用的Docker注册表:")
    registries = DockerRegistry.objects.all()
    for registry in registries:
        default_mark = " (默认)" if registry.is_default else ""
        print(f"ID: {registry.id} | {registry.name} | {registry.url}{default_mark}")
    
    return docker_push_steps

def create_docker_executor_fix():
    """创建Docker执行器修复代码"""
    print("\n🛠️  创建Docker执行器修复...")
    
    fix_code = '''
# 在 pipelines/services/docker_executor.py 的 _execute_docker_push 方法中修复

def _execute_docker_push(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
    """执行 Docker 推送步骤"""
    # 从 ansible_parameters 中获取参数
    params = step.ansible_parameters or {}
    docker_config = params.get('docker_config', {})
    
    # **FIX: 处理 AtomicStep 模型的 parameters 字段**
    if hasattr(step, 'parameters') and step.parameters:
        # AtomicStep 模型使用 parameters 字段
        step_params = step.parameters
        image_name = step_params.get('image') or step_params.get('image_name')
        registry_id = step_params.get('registry_id')
        
        # 如果指定了 registry_id，获取注册表信息
        registry = None
        if registry_id:
            from docker_integration.models import DockerRegistry
            try:
                registry = DockerRegistry.objects.get(id=registry_id)
                print(f"[DEBUG] 使用指定的注册表: {registry.name} ({registry.url})")
            except DockerRegistry.DoesNotExist:
                print(f"[WARNING] 注册表ID {registry_id} 不存在，使用默认设置")
                registry = None
    else:
        # PipelineStep 模型的处理方式（原有逻辑）
        image_name = (
            params.get('image') or 
            params.get('image_name') or 
            params.get('docker_image') or
            getattr(step, 'docker_image', None) or 
            context.get('docker_image')
        )
        registry = getattr(step, 'docker_registry', None)
    
    if not image_name:
        raise ValueError("No Docker image specified for push step")
    
    # 获取仓库信息
    if registry:
        # 使用配置的仓库
        registry_url = registry.url
        username = registry.username
        password = registry.get_decrypted_password()
    else:
        # 使用步骤配置中的仓库信息或默认设置
        registry_url = docker_config.get('registry_url')
        username = docker_config.get('username')
        password = docker_config.get('password')
    
    # 构建完整的镜像名称
    if registry and registry.registry_type != 'dockerhub':
        # 私有注册表需要添加前缀
        registry_host = registry.url.replace('https://', '').replace('http://', '')
        if not image_name.startswith(registry_host):
            full_image_name = f"{registry_host}/{image_name}"
        else:
            full_image_name = image_name
    else:
        full_image_name = image_name
    
    # 添加标签
    tag = step_params.get('tag', 'latest') if hasattr(step, 'parameters') else getattr(step, 'docker_tag', 'latest')
    if ':' not in full_image_name:
        full_image_name = f"{full_image_name}:{tag}"
    
    print(f"[DEBUG] 最终推送镜像名: {full_image_name}")
    print(f"[DEBUG] 使用注册表: {registry.url if registry else '默认'}")
    
    try:
        # 创建 Docker 管理器 - 支持真实执行
        docker_manager = DockerManager(enable_real_execution=self.enable_real_execution)
        
        # 登录仓库（如果需要）
        if username and password and registry_url:
            login_success = docker_manager.login_registry(registry_url, username, password)
            if not login_success:
                raise Exception(f"Docker仓库登录失败: {registry_url}")
        
        # 推送镜像
        result = docker_manager.push_image(full_image_name)
        
        return {
            'message': f'Image {full_image_name} pushed successfully',
            'output': result.get('push_log', ''),
            'data': {
                'image_name': full_image_name,
                'registry_url': registry_url,
                'digest': result.get('digest'),
                'size': result.get('size')
            }
        }
        
    except Exception as e:
        raise Exception(f"Docker push failed: {str(e)}")
'''
    
    with open('/Users/creed/Workspace/OpenSource/ansflow/docker_executor_fix.py', 'w') as f:
        f.write(fix_code)
    
    print("✅ 修复代码已生成到 docker_executor_fix.py")

def main():
    """主函数"""
    print("🐳 Docker Push 注册表选择问题修复工具")
    print("=" * 60)
    
    # 分析问题
    docker_push_steps = analyze_docker_push_issue()
    
    if not docker_push_steps:
        print("❌ 没有找到Docker Push步骤")
        return
    
    # 创建修复代码
    create_docker_executor_fix()
    
    print("\n📋 问题总结:")
    print("1. ❌ DockerStepExecutor 期望 PipelineStep 模型的 docker_registry 字段")
    print("2. ❌ 但实际传入的是 AtomicStep 模型的 parameters 字段")
    print("3. ❌ 导致注册表信息丢失，默认使用 Docker Hub")
    print("4. ✅ 修复: 在 DockerStepExecutor 中添加对 AtomicStep.parameters 的支持")
    
    print("\n🔧 下一步操作:")
    print("1. 修改 pipelines/services/docker_executor.py 中的 _execute_docker_push 方法")
    print("2. 添加对 AtomicStep.parameters.registry_id 的处理")
    print("3. 确保使用正确的注册表进行推送")

if __name__ == '__main__':
    main()
