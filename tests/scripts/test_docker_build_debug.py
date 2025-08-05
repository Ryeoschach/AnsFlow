#!/usr/bin/env python3
"""
测试Docker构建路径调试信息
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

def test_docker_build_debug():
    """测试Docker构建的路径调试信息"""
    
    # 创建临时目录和Dockerfile
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"创建测试目录: {temp_dir}")
        
        # 创建子目录模拟git clone结果
        test_repo_dir = os.path.join(temp_dir, 'test')
        os.makedirs(test_repo_dir)
        
        # 创建Dockerfile
        dockerfile_content = """FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
        dockerfile_path = os.path.join(test_repo_dir, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        print(f"创建Dockerfile: {dockerfile_path}")
        
        # 切换到test子目录（模拟git clone后的目录切换）
        os.chdir(test_repo_dir)
        print(f"切换到目录: {os.getcwd()}")
        
        # 创建Docker执行器
        executor = DockerStepExecutor()
        
        # 创建模拟步骤
        step = MagicMock()
        step.ansible_parameters = {
            'dockerfile': 'test/Dockerfile',  # 使用相对路径（这是可能的问题）
            'context': '.',
            'docker_image': 'test-app',
            'docker_tag': 'debug'
        }
        step.docker_image = 'test-app'
        step.docker_tag = 'debug'
        
        # 创建上下文
        context = {}
        
        try:
            print("\n=== 执行Docker构建测试 ===")
            result = executor._execute_docker_build(step, context)
            print(f"构建结果: {result}")
        except Exception as e:
            print(f"构建失败（预期的）: {e}")
            print("这个失败是预期的，主要是为了查看调试日志")

if __name__ == '__main__':
    print("🧪 开始Docker构建路径调试测试")
    print("=" * 50)
    
    try:
        test_docker_build_debug()
        print("\n" + "=" * 50)
        print("🎉 调试测试完成！")
        
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
