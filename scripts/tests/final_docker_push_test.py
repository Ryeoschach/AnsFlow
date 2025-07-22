"""
最终验证：Docker推送注册表选择修复测试
"""

import os
import sys
import django

# 设置Django环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from pipelines.services.docker_executor import DockerStepExecutor
from cicd_integrations.models import AtomicStep
from pipelines.models import PipelineStep
from docker_integration.models import DockerRegistry

def test_atomic_step_docker_push():
    """测试AtomicStep的Docker推送步骤"""
    print("🧪 测试 AtomicStep Docker推送（registry_id=4）")
    
    try:
        step = AtomicStep.objects.get(id=123)
        docker_executor = DockerStepExecutor(enable_real_execution=False)
        
        context = {}
        result = docker_executor._execute_docker_push(step, context)
        
        print(f"✅ AtomicStep 测试成功")
        print(f"   镜像名称: {result['data']['image_name']}")
        print(f"   注册表URL: {result['data']['registry_url']}")
        print(f"   注册表名称: {result['data']['registry_name']}")
        
        # 验证结果
        assert "gitlab.cyfee.com:8443" in result['data']['image_name'], "镜像名称应包含GitLab注册表地址"
        assert result['data']['registry_name'] == "gitlab", "注册表名称应为gitlab"
        
        return True
        
    except Exception as e:
        print(f"❌ AtomicStep 测试失败: {e}")
        return False

def test_pipeline_step_docker_push():
    """测试PipelineStep的Docker推送步骤"""
    print("\n🧪 测试 PipelineStep Docker推送（docker_registry=gitlab）")
    
    try:
        step = PipelineStep.objects.get(id=120)
        docker_executor = DockerStepExecutor(enable_real_execution=False)
        
        context = {}
        result = docker_executor._execute_docker_push(step, context)
        
        print(f"✅ PipelineStep 测试成功")
        print(f"   镜像名称: {result['data']['image_name']}")
        print(f"   注册表URL: {result['data']['registry_url']}")
        print(f"   注册表名称: {result['data']['registry_name']}")
        
        # 验证结果
        assert "gitlab.cyfee.com:8443" in result['data']['image_name'], "镜像名称应包含GitLab注册表地址"
        assert result['data']['registry_name'] == "gitlab", "注册表名称应为gitlab"
        
        return True
        
    except Exception as e:
        print(f"❌ PipelineStep 测试失败: {e}")
        return False

def main():
    print("🚀 Docker推送注册表选择修复 - 最终验证测试")
    print("=" * 60)
    
    # 显示注册表配置
    print("📋 当前注册表配置:")
    gitlab_registry = DockerRegistry.objects.get(id=4)
    print(f"   ID: {gitlab_registry.id}")
    print(f"   名称: {gitlab_registry.name}")
    print(f"   URL: {gitlab_registry.url}")
    print(f"   类型: {gitlab_registry.registry_type}")
    
    print("\n" + "=" * 60)
    
    # 运行测试
    atomic_success = test_atomic_step_docker_push()
    pipeline_success = test_pipeline_step_docker_push()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"   AtomicStep 测试: {'✅ 通过' if atomic_success else '❌ 失败'}")
    print(f"   PipelineStep 测试: {'✅ 通过' if pipeline_success else '❌ 失败'}")
    
    if atomic_success and pipeline_success:
        print("\n🎉 所有测试通过！Docker推送现在将使用用户选择的GitLab注册表而不是Docker Hub")
        print("💡 修复效果:")
        print("   - AtomicStep通过parameters.registry_id正确选择注册表")
        print("   - PipelineStep通过docker_registry字段正确选择注册表")
        print("   - 镜像名称正确构建为: gitlab.cyfee.com:8443/test:072201")
        print("   - 不再推送到registry-1.docker.io")
    else:
        print("\n⚠️ 部分测试失败，请检查配置")

if __name__ == "__main__":
    main()
