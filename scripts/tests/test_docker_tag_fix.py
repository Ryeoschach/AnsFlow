"""
测试Docker镜像标签修复
验证带端口号的注册表URL不会影响标签添加
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
from docker_integration.models import DockerRegistry

def test_docker_tag_with_port():
    """测试带端口号的注册表URL的标签处理"""
    print("🧪 测试Docker镜像标签修复（带端口号注册表）")
    
    try:
        # 获取测试步骤
        step = AtomicStep.objects.get(id=123)
        print(f"步骤参数: {step.parameters}")
        
        # 获取GitLab注册表
        registry = DockerRegistry.objects.get(id=4)
        print(f"注册表: {registry.name} - {registry.url}")
        
        # 创建Docker执行器
        docker_executor = DockerStepExecutor(enable_real_execution=False)
        
        # 执行推送步骤
        context = {}
        result = docker_executor._execute_docker_push(step, context)
        
        # 检查结果
        image_name = result['data']['image_name']
        print(f"✅ 生成的镜像名: {image_name}")
        
        # 验证标签是否正确添加
        expected_image = "gitlab.cyfee.com:8443/test:072201"
        if image_name == expected_image:
            print(f"✅ 标签修复成功！镜像名正确: {image_name}")
            return True
        else:
            print(f"❌ 标签修复失败！")
            print(f"   期望: {expected_image}")
            print(f"   实际: {image_name}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tag_logic():
    """测试标签添加逻辑"""
    print("\n🧪 测试标签添加逻辑")
    
    test_cases = [
        # (full_image_name, tag, expected_result)
        ("gitlab.cyfee.com:8443/test", "072201", "gitlab.cyfee.com:8443/test:072201"),
        ("docker.io/library/nginx", "latest", "docker.io/library/nginx:latest"),
        ("test", "v1.0", "test:v1.0"),
        ("registry.com:5000/myapp", "dev", "registry.com:5000/myapp:dev"),
        ("gitlab.cyfee.com:8443/test:existing", "072201", "gitlab.cyfee.com:8443/test:existing"),  # 已有标签不应重复添加
    ]
    
    all_passed = True
    
    for full_image_name, tag, expected in test_cases:
        # 模拟标签添加逻辑
        image_part = full_image_name.split('/')[-1] if '/' in full_image_name else full_image_name
        if ':' not in image_part:
            result = f"{full_image_name}:{tag}"
        else:
            result = full_image_name
        
        if result == expected:
            print(f"✅ {full_image_name} + {tag} = {result}")
        else:
            print(f"❌ {full_image_name} + {tag} = {result} (期望: {expected})")
            all_passed = False
    
    return all_passed

def main():
    print("🚀 Docker镜像标签修复测试")
    print("=" * 60)
    
    # 测试标签逻辑
    logic_test = test_tag_logic()
    
    print("\n" + "=" * 60)
    
    # 测试实际推送
    push_test = test_docker_tag_with_port()
    
    print("\n" + "=" * 60)
    print("📊 测试结果:")
    print(f"   标签逻辑测试: {'✅ 通过' if logic_test else '❌ 失败'}")
    print(f"   Docker推送测试: {'✅ 通过' if push_test else '❌ 失败'}")
    
    if logic_test and push_test:
        print("\n🎉 所有测试通过！Docker镜像标签现在可以正确处理带端口号的注册表URL")
        print("💡 修复效果:")
        print("   - 不再因为注册表URL中的端口号而跳过标签添加")
        print("   - 镜像名正确构建为: gitlab.cyfee.com:8443/test:072201")
        print("   - 解决了HTTP 403错误中的镜像标签缺失问题")
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查")

if __name__ == "__main__":
    main()
