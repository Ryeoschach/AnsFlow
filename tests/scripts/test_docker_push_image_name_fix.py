#!/usr/bin/env python3
"""
测试 Docker 推送镜像名称修复
验证本地镜像 myapp:0722 能够正确推送
"""

import os
import sys
import django

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.services.docker_executor import DockerStepExecutor

class MockStep:
    """模拟原子步骤"""
    def __init__(self, parameters):
        self.parameters = parameters

def test_docker_push_image_name_fix():
    """测试Docker推送镜像名称修复"""
    
    print("=== 测试 Docker 推送镜像名称修复 ===")
    
    # 模拟推送步骤参数
    push_params = {
        'image': 'myapp',      # 镜像名称
        'tag': '0722',         # 标签
        'registry_id': 5       # Harbor 注册表ID
    }
    
    # 创建模拟步骤
    mock_step = MockStep(push_params)
    
    # 创建Docker执行器（禁用真实执行，仅测试逻辑）
    executor = DockerStepExecutor(enable_real_execution=False)
    
    print(f"📋 测试参数:")
    print(f"  镜像名: {push_params['image']}")
    print(f"  标签: {push_params['tag']}")  
    print(f"  注册表ID: {push_params['registry_id']}")
    
    try:
        # 执行推送步骤（模拟模式）
        context = {}
        result = executor._execute_docker_push(mock_step, context)
        
        print(f"\n✅ 推送步骤执行成功")
        print(f"📄 返回信息: {result.get('message', '')}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ 推送步骤失败: {error_msg}")
        
        # 分析错误原因
        if "An image does not exist locally with the tag" in error_msg:
            print(f"\n🔍 镜像查找问题分析:")
            print(f"  ❌ 问题: 系统查找的是错误的镜像名称")
            if "with the tag: myapp" in error_msg:
                print(f"  ❌ 查找的镜像: myapp (缺少标签)")
                print(f"  ✅ 应该查找: myapp:0722 (完整镜像名)")
            
            print(f"\n💡 建议:")
            print(f"  1. 检查镜像名称构建逻辑")
            print(f"  2. 确保包含完整的 image:tag 格式")
            print(f"  3. 验证本地镜像是否真的存在: docker images myapp")
        
        return False

def verify_local_image():
    """验证本地镜像是否存在"""
    import subprocess
    
    print(f"\n=== 验证本地镜像 ===")
    
    try:
        # 检查本地镜像
        result = subprocess.run(['docker', 'images', 'myapp'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Docker 命令执行成功")
            print(f"📋 本地 myapp 镜像:")
            for line in result.stdout.split('\n'):
                if line.strip() and ('REPOSITORY' in line or 'myapp' in line):
                    print(f"  {line}")
            
            # 检查是否包含 0722 标签
            if '0722' in result.stdout:
                print(f"\n✅ 确认存在镜像: myapp:0722")
                return True
            else:
                print(f"\n❌ 未找到标签 0722 的镜像")
                return False
        else:
            print(f"❌ Docker 命令失败: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print(f"❌ Docker 未安装或不在PATH中")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

if __name__ == '__main__':
    print("🐳 Docker 推送镜像名称问题诊断")
    print("="*50)
    
    # 验证本地镜像
    has_local_image = verify_local_image()
    
    # 测试推送逻辑
    push_success = test_docker_push_image_name_fix()
    
    print(f"\n" + "="*50)
    print(f"📊 诊断结果:")
    print(f"  本地镜像存在: {'✅' if has_local_image else '❌'}")
    print(f"  推送逻辑正确: {'✅' if push_success else '❌'}")
    
    if has_local_image and push_success:
        print(f"\n🎉 修复成功！镜像推送应该可以正常工作了")
    elif has_local_image and not push_success:
        print(f"\n⚠️  本地镜像存在，但推送逻辑还有问题，需要进一步调试")
    elif not has_local_image:
        print(f"\n⚠️  请先确保本地存在 myapp:0722 镜像")
        print(f"     可以通过构建步骤重新构建镜像")
    
    print(f"\n💡 下一步:")
    print(f"  1. 重新执行流水线测试")
    print(f"  2. 查看详细的执行日志")
    print(f"  3. 确认推送到Harbor注册表成功")
