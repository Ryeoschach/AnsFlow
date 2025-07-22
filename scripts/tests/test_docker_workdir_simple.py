#!/usr/bin/env python3
"""
简化的Docker工作目录测试
直接测试Docker执行器是否能正确使用传递的工作目录
"""

import os
import sys
import tempfile

# 添加后端路径
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
import django
django.setup()

from pipelines.services.docker_executor import DockerStepExecutor
from unittest.mock import MagicMock

def test_docker_workdir_simple():
    """简化的Docker工作目录测试"""
    
    # 1. 创建测试目录结构
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"创建临时目录: {temp_dir}")
        
        # 创建子目录模拟git clone后的结构
        git_clone_dir = os.path.join(temp_dir, 'test')
        os.makedirs(git_clone_dir)
        
        # 在子目录中创建Dockerfile
        dockerfile_content = """FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
        dockerfile_path = os.path.join(git_clone_dir, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        print(f"创建Git clone目录: {git_clone_dir}")
        print(f"创建Dockerfile: {dockerfile_path}")
        
        # 2. 创建Docker执行器
        executor = DockerStepExecutor()
        
        # 3. 创建模拟步骤
        step = MagicMock()
        step.step_type = 'docker_build'
        step.name = 'Test Docker Build'
        step.id = 999
        step.ansible_parameters = {
            'dockerfile': 'Dockerfile',
            'context': '.',
            'docker_image': 'test-workdir',
            'docker_tag': 'simple'
        }
        
        # 4. 准备上下文，包含Git clone后的工作目录
        context = {
            'working_directory': git_clone_dir,  # 这是关键：指定Docker执行器应该使用的目录
            'workspace_path': temp_dir,
            'execution_env': os.environ.copy()
        }
        
        print(f"原始工作目录: {os.getcwd()}")
        print(f"传递给Docker执行器的工作目录: {context['working_directory']}")
        
        try:
            # 5. 执行Docker build
            print("\n=== 执行Docker build测试 ===")
            result = executor.execute_step(step, context)
            
            print(f"执行结果: {result}")
            print(f"成功: {result.get('success', False)}")
            
            if result.get('output'):
                print(f"输出: {result['output']}")
            
            if not result.get('success') and result.get('error'):
                print(f"错误: {result['error']}")
            
            # 6. 验证结果
            success = result.get('success', False)
            if success:
                print("✅ Docker工作目录测试成功!")
                print("✅ Docker执行器正确使用了传递的工作目录")
            else:
                print("❌ Docker工作目录测试失败")
                if 'no such file or directory' in str(result.get('error', '')).lower():
                    print("❌ 可能仍然存在工作目录问题")
            
            return success
            
        except Exception as e:
            print(f"执行失败: {e}")
            return False
        finally:
            print(f"测试完成后工作目录: {os.getcwd()}")

if __name__ == '__main__':
    print("🧪 开始简化的Docker工作目录测试")
    print("=" * 50)
    
    try:
        success = test_docker_workdir_simple()
        exit_code = 0 if success else 1
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 Docker工作目录测试通过!")
        else:
            print("💥 Docker工作目录测试失败!")
        
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
